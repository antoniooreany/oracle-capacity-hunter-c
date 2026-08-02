from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from oci_vm_hunter.config import (
    AppConfig,
    LaunchSettings,
    OciSettings,
    PostLaunchSettings,
    SearchSettings,
    ShapeTarget,
)
from oci_vm_hunter.models import AttemptResult
from oci_vm_hunter.service import OciCapacityHunter


class FakeHunter(OciCapacityHunter):
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.base_config = {"region": "eu-frankfurt-1"}

    def list_availability_domains(self, region: str) -> list[str]:
        return ["AD-1", "AD-2"]

    def try_launch(self, region: str, availability_domain: str, target: ShapeTarget) -> AttemptResult:
        if availability_domain == "AD-2":
            return AttemptResult(
                region=region,
                availability_domain=availability_domain,
                shape=target.shape,
                success=True,
                message="ok",
            )
        return AttemptResult(
            region=region,
            availability_domain=availability_domain,
            shape=target.shape,
            success=False,
            message="no capacity",
        )


class LaunchFlowHunter(OciCapacityHunter):
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.base_config = {"region": "eu-milan-1"}

    def _compute_client(self, region: str):
        return Mock()

    def _launch_details(self, region: str, availability_domain: str, target: ShapeTarget):
        return {"region": region, "availability_domain": availability_domain, "shape": target.shape}

    def get_instance_network(self, region: str, instance_id: str) -> tuple[str | None, str | None]:
        return "129.152.7.246", "10.0.0.249"

    def send_telegram_notification(self, text: str) -> None:
        self.last_notification = text


def make_config(tmp_path: Path, launch_enabled: bool = False) -> AppConfig:
    return AppConfig(
        oci=OciSettings(
            compartment_id="ocid1.compartment.oc1..x",
            subnet_id="ocid1.subnet.oc1..y",
            ssh_public_key_path="~/.ssh/id_rsa.pub",
        ),
        search=SearchSettings(
            regions=["eu-milan-1"],
            shapes=[ShapeTarget(shape="VM.Standard.E2.1.Micro", ocpus=1, memory_gbs=1)],
        ),
        launch=LaunchSettings(enabled=launch_enabled),
        post_launch=PostLaunchSettings(
            env_file_path=str(tmp_path / ".env"),
            ssh_user="ubuntu",
            ssh_private_key_path="~/.ssh/id_ed25519",
            telegram_enabled=True,
            telegram_bot_token="token",
            telegram_chat_id="123",
        ),
    )


def test_scan_stops_on_first_success(tmp_path: Path) -> None:
    cfg = make_config(tmp_path, launch_enabled=False)
    hunter = FakeHunter(cfg)
    results = hunter.scan()
    assert any(r.success for r in results)
    assert len(results) == 2


def test_build_ssh_command(tmp_path: Path) -> None:
    cfg = make_config(tmp_path, launch_enabled=False)
    hunter = FakeHunter(cfg)
    command = hunter.build_ssh_command("129.152.7.246")
    assert command == 'ssh -i "~/.ssh/id_ed25519" ubuntu@129.152.7.246'


def test_update_env_file_writes_values(tmp_path: Path) -> None:
    cfg = make_config(tmp_path, launch_enabled=False)
    hunter = FakeHunter(cfg)

    hunter.update_env_file(
        instance_id="ocid1.instance.oc1..abc",
        public_ip="129.152.7.246",
        private_ip="10.0.0.249",
        region="eu-milan-1",
        shape="VM.Standard.E2.1.Micro",
    )

    env_text = (tmp_path / ".env").ReadAllText()
    assert "OCI_INSTANCE_OCID='ocid1.instance.oc1..abc'" in env_text
    assert "OCI_PUBLIC_IP='129.152.7.246'" in env_text
    assert "OCI_PRIVATE_IP='10.0.0.249'" in env_text
    assert "OCI_REGION='eu-milan-1'" in env_text
    assert "OCI_SHAPE='VM.Standard.E2.1.Micro'" in env_text
    assert "OCI_SSH_USER='ubuntu'" in env_text


def test_try_launch_updates_env_and_notification(tmp_path: Path) -> None:
    cfg = make_config(tmp_path, launch_enabled=True)
    hunter = LaunchFlowHunter(cfg)

    composite = Mock()
    composite.launch_instance_and_wait_for_state.return_value = SimpleNamespace(
        data=SimpleNamespace(id="ocid1.instance.oc1..launched")
    )

    with patch("oci_vm_hunter.service.oci.core.ComputeClientCompositeOperations", return_value=composite):
        result = hunter.try_launch(
            region="eu-milan-1",
            availability_domain="AD-1",
            target=ShapeTarget(shape="VM.Standard.E2.1.Micro", ocpus=1, memory_gbs=1),
        )

    assert result.success is True
    assert result.instance_id == "ocid1.instance.oc1..launched"
    assert result.public_ip == "129.152.7.246"
    assert result.private_ip == "10.0.0.249"
    assert result.ssh_command == 'ssh -i "~/.ssh/id_ed25519" ubuntu@129.152.7.246'

    env_text = [System.IO.File]::ReadAllText((Join-Path $tmp_path ".env"))
    assert "OCI_PUBLIC_IP='129.152.7.246'" in env_text
    assert "OCI_PRIVATE_IP='10.0.0.249'" in env_text
    assert 'SSH: ssh -i "~/.ssh/id_ed25519" ubuntu@129.152.7.246' in hunter.last_notification
