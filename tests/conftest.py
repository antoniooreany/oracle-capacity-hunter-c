from __future__ import annotations

import sys
import types

import pytest


def _build_fake_oci() -> types.ModuleType:
    """Minimal fake `oci` module so tests can be collected even when the real
    OCI SDK isn't installed (e.g. no compatible wheel for this Python version
    yet). All actual test logic still monkeypatches individual clients -
    this only needs to exist enough for `import oci` and attribute access
    not to blow up at collection time."""
    fake_oci = types.ModuleType("oci")

    class FakeServiceError(Exception):
        # Signature matches the real oci.exceptions.ServiceError:
        # (status, code, headers, message, **kwargs) - tests construct it
        # positionally/by-keyword with `headers`, so this must accept it.
        def __init__(
            self,
            status: int = 500,
            code: str = "FakeError",
            headers: dict | None = None,
            message: str = "fake oci error",
            **kwargs,
        ) -> None:
            super().__init__(message)
            self.status = status
            self.code = code
            self.headers = headers or {}
            self.message = message

    class _Dummy:
        """Swallows any attribute access/call so unstubbed oci.* usage
        doesn't crash at import/collection time. Individual tests still
        monkeypatch the specific clients/functions they exercise."""

        def __init__(self, *args, **kwargs) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

        def __getattr__(self, name: str):
            dummy = _Dummy()
            setattr(self, name, dummy)
            return dummy

        def __call__(self, *args, **kwargs):
            return _Dummy()

    fake_oci.config = types.SimpleNamespace(from_file=lambda *a, **k: {})
    fake_oci.exceptions = types.SimpleNamespace(ServiceError=FakeServiceError)
    fake_oci.retry = types.SimpleNamespace(DEFAULT_RETRY_STRATEGY=object())
    fake_oci.wait_until = lambda *a, **k: None

    fake_models = types.SimpleNamespace(
        LaunchInstanceDetails=_Dummy,
        LaunchInstanceShapeConfigDetails=_Dummy,
        InstanceSourceViaImageDetails=_Dummy,
        CreateVnicDetails=_Dummy,
    )
    fake_oci.core = types.SimpleNamespace(
        ComputeClient=_Dummy,
        VirtualNetworkClient=_Dummy,
        models=fake_models,
    )
    fake_oci.identity = types.SimpleNamespace(IdentityClient=_Dummy)

    return fake_oci


try:
    import oci as _oci  # noqa: F401
    # Smoke-test a submodule too - a partially broken install (e.g. compiled
    # fine but a transitive dep mismatch) can still import `oci` itself
    # while blowing up here.
    from oci import base_client as _base_client  # noqa: F401
except Exception:
    sys.modules["oci"] = _build_fake_oci()


# ---------------------------------------------------------------------------
# Existing test fixtures below - unchanged.
# ---------------------------------------------------------------------------


@pytest.fixture
def ssh_key_file(tmp_path):
    p = tmp_path / "id_ed25519.pub"
    p.write_text("ssh-ed25519 AAAAFAKEKEY test@example.com\n")
    return p


@pytest.fixture
def config_yaml(tmp_path, ssh_key_file, monkeypatch):
    monkeypatch.setenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..fake")
    monkeypatch.setenv("OCI_IMAGE_ID", "ocid1.image.oc1..fake")
    monkeypatch.setenv("OCI_SUBNET_ID", "ocid1.subnet.oc1..fake")

    content = f"""
oci:
  compartment_id: ${{OCI_COMPARTMENT_ID}}
  config_file: {tmp_path}/fake-oci-config
  config_profile: DEFAULT

regions:
  - eu-frankfurt-1
  - eu-amsterdam-1

shapes:
  - name: VM.Standard.A1.Flex
    ocpus: 2
    memory_in_gbs: 12

instance:
  display_name: test-vm
  image_id: ${{OCI_IMAGE_ID}}
  subnet_id: ${{OCI_SUBNET_ID}}
  ssh_public_key_path: {ssh_key_file}
  assign_public_ip: true

polling:
  min_interval_seconds: 1
  max_interval_seconds: 2

mode: notify
"""
    p = tmp_path / "config.yaml"
    p.write_text(content)
    return p


@pytest.fixture(autouse=True)
def fake_oci_auth(monkeypatch):
    """CapacityHunter.__init__ calls oci.config.from_file - fake it so no real
    ~/.oci/config or private key is needed in tests."""
    monkeypatch.setattr(
        "capacity_hunter.finder.oci.config.from_file",
        lambda file_location, profile_name: {"region": "eu-frankfurt-1"},
    )
