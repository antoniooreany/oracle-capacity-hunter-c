FROM python:3.12-slim AS base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir --no-deps -e .

# config.yaml and OCI credentials are mounted at runtime, not baked into the image:
#   docker run --rm \
#     -v $(pwd)/config.yaml:/app/config.yaml:ro \
#     -v ~/.oci:/root/.oci:ro \
#     -e OCI_COMPARTMENT_ID=... -e OCI_IMAGE_ID=... -e OCI_SUBNET_ID=... \
#     ghcr.io/you/capacity-hunter:latest --once
ENTRYPOINT ["python", "-m", "capacity_hunter.cli"]
CMD ["--config", "/app/config.yaml"]
