from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import oci  # TODO: not resolved
import pytest

from capacity_hunter.config import load_config
from capacity_hunter.finder import CapacityHunter
from capacity_hunter.notifier import TelegramNotifier


def _ad(name):
    return SimpleNamespace(name=name)


def _make_compute_client(monkeypatch, *, existing_instance=None, launch_side_effect=None):
    """Patch capacity_hunter.finder.oci.core.ComputeClient to return one shared mock,
    regardless of how many times/regions it's instantiated for."""
    client = MagicMock()
    client.list_instances.return_value = SimpleNamespace(
        data=[SimpleNamespace(id=existing_instance)] if existing_instance else []
    )
    if launch_side_effect is not None:
        client.launch_instance.side_effect = launch_side_effect
    else:
        client.launch_instance.return_value = SimpleNamespace(
            data=SimpleNamespace(id="ocid1.instance.oc1..new")
        )
    client.get_instance.return_value = SimpleNamespace(data=SimpleNamespace(id="ocid1.instance.oc1..new"))
    client.list_vnic_attachments.return_value = SimpleNamespace(
        data=[SimpleNamespace(vnic_id="ocid1.vnic.oc1..fake")]
    )
    monkeypatch.setattr("capacity_hunter.finder.oci.core.ComputeClient", lambda cfg: client)
    monkeypatch.setattr("capacity_hunter.finder.oci.wait_until", lambda *a, **k: None)
    return client


def _make_identity_client(monkeypatch, ad_names):
    client = MagicMock()
    client.list_availability_domains.return_value = SimpleNamespace(
        data=[_ad(n) for n in ad_names]
    )
    monkeypatch.setattr("capacity_hunter.finder.oci.identity.IdentityClient", lambda cfg: client)
    return client


def _make_vnic_client(monkeypatch, public_ip="1.2.3.4"):
    client = MagicMock()
    client.get_vnic.return_value = SimpleNamespace(data=SimpleNamespace(public_ip=public_ip))
    monkeypatch.setattr("capacity_hunter.finder.oci.core.VirtualNetworkClient", lambda cfg: client)
    return client


def test_run_once_finds_capacity_on_first_try(config_yaml, monkeypatch):
    _make_identity_client(monkeypatch, ["AD-1"])
    _make_compute_client(monkeypatch)
    _make_vnic_client(monkeypatch)

    config = load_config(config_yaml)
    config.mode = "create"  # this test asserts on the launched-and-kept path
    hunter = CapacityHunter(config, notifier=MagicMock(spec=TelegramNotifier))

    result = hunter.run_once()

    assert result.found is True
    assert result.region == "eu-frankfurt-1"
    assert result.availability_domain == "AD-1"
    assert result.public_ip == "1.2.3.4"


def test_run_once_skips_ad_on_out_of_capacity(config_yaml, monkeypatch):
    _make_identity_client(monkeypatch, ["AD-1", "AD-2"])
    out_of_capacity = oci.exceptions.ServiceError(
        status=500, code="OutOfCapacity", headers={}, message="no room"
    )
    success = SimpleNamespace(data=SimpleNamespace(id="ocid1.instance.oc1..new"))
    _make_compute_client(monkeypatch, launch_side_effect=[out_of_capacity, success])
    _make_vnic_client(monkeypatch)

    config = load_config(config_yaml)
    config.mode = "create"
    hunter = CapacityHunter(config, notifier=MagicMock(spec=TelegramNotifier))

    result = hunter.run_once()

    assert result.found is True
    assert result.availability_domain == "AD-2"


def test_run_once_returns_not_found_when_all_ads_exhausted(config_yaml, monkeypatch):
    _make_identity_client(monkeypatch, ["AD-1"])
    out_of_capacity = oci.exceptions.ServiceError(
        status=500, code="OutOfCapacity", headers={}, message="no room"
    )
    # both regions x 1 AD x 1 shape = 2 attempts total
    _make_compute_client(monkeypatch, launch_side_effect=[out_of_capacity, out_of_capacity])

    config = load_config(config_yaml)
    hunter = CapacityHunter(config, notifier=MagicMock(spec=TelegramNotifier))

    result = hunter.run_once()

    assert result.found is False


def test_run_once_skips_search_if_instance_already_running(config_yaml, monkeypatch):
    identity_client = _make_identity_client(monkeypatch, ["AD-1"])
    compute_client = _make_compute_client(monkeypatch, existing_instance="ocid1.instance.oc1..already")

    config = load_config(config_yaml)
    hunter = CapacityHunter(config, notifier=MagicMock(spec=TelegramNotifier))

    result = hunter.run_once()

    assert result.found is True
    assert result.instance_id == "ocid1.instance.oc1..already"
    # Should never even look up availability domains, since it bailed early
    identity_client.list_availability_domains.assert_not_called()
    compute_client.launch_instance.assert_not_called()


def test_notify_mode_terminates_probe_instance(config_yaml, monkeypatch):
    _make_identity_client(monkeypatch, ["AD-1"])
    compute_client = _make_compute_client(monkeypatch)
    # config_yaml fixture sets mode: notify by default

    config = load_config(config_yaml)
    assert config.mode == "notify"
    hunter = CapacityHunter(config, notifier=MagicMock(spec=TelegramNotifier))

    result = hunter.run_once()

    assert result.found is True
    assert result.instance_id is None  # terminated, nothing to connect to
    compute_client.terminate_instance.assert_called_once_with("ocid1.instance.oc1..new")


def test_unexpected_service_error_propagates(config_yaml, monkeypatch):
    _make_identity_client(monkeypatch, ["AD-1"])
    auth_error = oci.exceptions.ServiceError(
        status=401, code="NotAuthenticated", headers={}, message="bad key"
    )
    _make_compute_client(monkeypatch, launch_side_effect=auth_error)

    config = load_config(config_yaml)
    hunter = CapacityHunter(config, notifier=MagicMock(spec=TelegramNotifier))

    with pytest.raises(oci.exceptions.ServiceError):
        hunter.run_once()
