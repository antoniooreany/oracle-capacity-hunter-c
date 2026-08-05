[project]
name = "oci-vm-capacity-hunter"
version = "0.1.0"
description = "CLI and UI for hunting OCI A1/Flex VM capacity"
requires-python = ">=3.11"
# и остальные поля [project] здесь без изменений

[project.scripts]
oci-hunter = "capacity_hunter.cli:main"
capacity-hunter-ui = "capacity_hunter.ui.launcher:main"