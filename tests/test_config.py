from __future__ import annotations

import pytest

from capacity_hunter.config import ConfigError, load_config


def test_load_config_expands_env_vars(config_yaml):
    config = load_config(config_yaml)
    assert config.compartment_id == "ocid1.compartment.oc1..fake"
    assert config.instance.image_id == "ocid1.image.oc1..fake"
    assert config.instance.subnet_id == "ocid1.subnet.oc1..fake"


def test_load_config_parses_regions_and_shapes(config_yaml):
    config = load_config(config_yaml)
    assert config.regions == ["eu-frankfurt-1", "eu-amsterdam-1"]
    assert len(config.shapes) == 1
    assert config.shapes[0].name == "VM.Standard.A1.Flex"
    assert config.shapes[0].ocpus == 2


def test_load_config_missing_env_var_raises(config_yaml, monkeypatch):
    monkeypatch.delenv("OCI_COMPARTMENT_ID", raising=False)
    with pytest.raises(ConfigError, match="OCI_COMPARTMENT_ID"):
        load_config(config_yaml)


def test_load_config_invalid_mode_raises(tmp_path, ssh_key_file, monkeypatch):
    monkeypatch.setenv("OCI_COMPARTMENT_ID", "x")
    monkeypatch.setenv("OCI_IMAGE_ID", "x")
    monkeypatch.setenv("OCI_SUBNET_ID", "x")
    bad = tmp_path / "bad.yaml"
    bad.write_text(f"""
oci:
  compartment_id: ${{OCI_COMPARTMENT_ID}}
regions: [eu-frankfurt-1]
shapes:
  - name: VM.Standard.A1.Flex
    ocpus: 1
    memory_in_gbs: 6
instance:
  display_name: test
  image_id: ${{OCI_IMAGE_ID}}
  subnet_id: ${{OCI_SUBNET_ID}}
  ssh_public_key_path: {ssh_key_file}
mode: not-a-real-mode
""")
    with pytest.raises(ConfigError, match="mode must be"):
        load_config(bad)
