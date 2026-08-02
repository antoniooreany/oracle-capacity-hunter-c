from __future__ import annotations

import pytest


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
