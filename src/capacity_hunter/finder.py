"""Capacity-hunting logic: iterate regions/ADs/shapes, launch on success."""
from __future__ import annotations

import base64
import logging
import random
import time
from dataclasses import dataclass

import oci # TODO: not resolved

from capacity_hunter.config import HunterConfig, ShapeConfig
from capacity_hunter.notifier import TelegramNotifier

logger = logging.getLogger(__name__)

# OCI reports capacity exhaustion via a 500 ServiceError with this code.
OUT_OF_CAPACITY_CODES = {"OutOfCapacity", "LimitExceeded", "InternalError"}


@dataclass
class LaunchResult:
    found: bool
    region: str | None = None
    availability_domain: str | None = None
    shape: ShapeConfig | None = None
    public_ip: str | None = None
    instance_id: str | None = None


class CapacityHunter:
    """Iterates (region, AD, shape) combinations looking for free capacity."""

    def __init__(self, config: HunterConfig, notifier: TelegramNotifier | None = None) -> None:
        self._config = config
        self._notifier = notifier or TelegramNotifier(config.telegram)
        self._base_oci_config = oci.config.from_file(
            file_location=config.oci_config_file,
            profile_name=config.oci_config_profile,
        )

    def _clients_for_region(self, region: str) -> tuple[oci.core.ComputeClient, oci.identity.IdentityClient]:
        cfg = dict(self._base_oci_config)
        cfg["region"] = region
        return oci.core.ComputeClient(cfg), oci.identity.IdentityClient(cfg)

    def _availability_domains(self, identity_client: oci.identity.IdentityClient) -> list[str]:
        response = identity_client.list_availability_domains(self._config.compartment_id)
        return [ad.name for ad in response.data]

    def _already_running(self, compute_client: oci.core.ComputeClient) -> str | None:
        response = compute_client.list_instances(
            compartment_id=self._config.compartment_id,
            display_name=self._config.instance.display_name,
            lifecycle_state="RUNNING",
        )
        if response.data:
            return response.data[0].id
        return None

    def _metadata(self) -> dict:
        with open(self._config.instance.ssh_public_key_path, encoding="utf-8") as fh:
            ssh_key = fh.read().strip()
        meta = {"ssh_authorized_keys": ssh_key}
        if self._config.instance.user_data_path:
            with open(self._config.instance.user_data_path, "rb") as fh:
                meta["user_data"] = base64.b64encode(fh.read()).decode("ascii")
        return meta

    def _try_launch(
        self,
        compute_client: oci.core.ComputeClient,
        region: str,
        ad: str,
        shape: ShapeConfig,
    ) -> LaunchResult:
        details = oci.core.models.LaunchInstanceDetails(
            compartment_id=self._config.compartment_id,
            availability_domain=ad,
            display_name=self._config.instance.display_name,
            shape=shape.name,
            shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
                ocpus=shape.ocpus,
                memory_in_gbs=shape.memory_in_gbs,
            ),
            source_details=oci.core.models.InstanceSourceViaImageDetails(
                image_id=self._config.instance.image_id,
            ),
            create_vnic_details=oci.core.models.CreateVnicDetails(
                subnet_id=self._config.instance.subnet_id,
                assign_public_ip=self._config.instance.assign_public_ip,
            ),
            metadata=self._metadata(),
        )
        try:
            launch_response = compute_client.launch_instance(details)
        except oci.exceptions.ServiceError as exc:
            if exc.code in OUT_OF_CAPACITY_CODES or exc.status == 500:
                logger.info("No capacity in %s / %s: %s", region, ad, exc.code)
                return LaunchResult(found=False)
            raise  # unexpected error - surface it

        instance = launch_response.data

        if self._config.mode == "notify":
            # We only wanted to detect capacity, not keep the instance.
            # Terminate immediately so we don't consume the free-tier slot.
            compute_client.terminate_instance(instance.id)
            return LaunchResult(
                found=True,
                region=region,
                availability_domain=ad,
                shape=shape,
                instance_id=None,  # terminated - nothing to connect to
            )

        oci.wait_until(
            compute_client,
            compute_client.get_instance(instance.id),
            "lifecycle_state",
            "RUNNING",
            max_wait_seconds=180,
        )
        vnic_attachments = compute_client.list_vnic_attachments(
            compartment_id=self._config.compartment_id, instance_id=instance.id
        ).data
        public_ip = None
        if vnic_attachments:
            vnic_client = oci.core.VirtualNetworkClient(dict(self._base_oci_config, region=region))
            vnic = vnic_client.get_vnic(vnic_attachments[0].vnic_id).data
            public_ip = vnic.public_ip

        return LaunchResult(
            found=True,
            region=region,
            availability_domain=ad,
            shape=shape,
            public_ip=public_ip,
            instance_id=instance.id,
        )

    def run_once(self) -> LaunchResult:
        """Single pass across all configured regions/ADs/shapes. No looping/sleeping."""
        for region in self._config.regions:
            compute_client, identity_client = self._clients_for_region(region)

            existing = self._already_running(compute_client)
            if existing:
                logger.info("Instance already RUNNING in %s (%s), stopping search.", region, existing)
                return LaunchResult(found=True, region=region, instance_id=existing)

            for ad in self._availability_domains(identity_client):
                for shape in self._config.shapes:
                    logger.info("Trying region=%s ad=%s shape=%s", region, ad, shape.name)
                    result = self._try_launch(compute_client, region, ad, shape)
                    if result.found:
                        return result
        return LaunchResult(found=False)

    def run_forever(self) -> LaunchResult:
        """Loop with exponential backoff until capacity is found."""
        sleep_time = self._config.min_interval_seconds
        while True:
            result = self.run_once()
            if result.found:
                self._announce(result)
                return result

            logger.info("No capacity anywhere this round. Sleeping %ss", sleep_time)
            time.sleep(sleep_time)
            sleep_time = min(sleep_time * 2, self._config.max_interval_seconds)
            sleep_time += random.randint(0, 10)

    def _announce(self, result: LaunchResult) -> None:
        if result.instance_id and not result.public_ip and not result.availability_domain:
            msg = f"ℹ️ Instance already running in {result.region} ({result.instance_id})"
        elif result.public_ip is None and result.instance_id is None:
            msg = (
                f"🔔 Capacity is available (mode=notify, probe instance terminated)!\n"
                f"Region: {result.region}\n"
                f"AD: {result.availability_domain}\n"
                f"Shape: {result.shape.name if result.shape else '?'}\n"
                f"Switch mode to 'create' or launch manually now."
            )
        else:
            msg = (
                f"✅ Oracle A1 capacity found and VM launched!\n"
                f"Region: {result.region}\n"
                f"AD: {result.availability_domain}\n"
                f"Shape: {result.shape.name if result.shape else '?'}\n"
                f"Public IP: {result.public_ip or 'pending'}"
            )
        logger.info(msg)
        self._notifier.send(msg)
