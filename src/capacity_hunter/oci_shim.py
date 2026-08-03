from __future__ import annotations

import sys
import types


def _build_fake_oci() -> types.ModuleType:
    fake_oci = types.ModuleType("oci")

    class FakeServiceError(Exception):
        def __init__(self, status: int = 500, code: str = "FakeError", message: str = "fake oci error") -> None:
            super().__init__(message)
            self.status = status
            self.code = code
            self.message = message

    class _Dummy:
        def __init__(self, *args, **kwargs) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

        def __getattr__(self, name):
            # Anything not explicitly set becomes another dummy.
            d = _Dummy()
            setattr(self, name, d)
            return d

        def __call__(self, *args, **kwargs):
            return _Dummy()

    fake_oci.config = types.SimpleNamespace(
        from_file=lambda *args, **kwargs: {},
    )

    fake_oci.exceptions = types.SimpleNamespace(
        ServiceError=FakeServiceError,
    )

    fake_oci.retry = types.SimpleNamespace(
        DEFAULT_RETRY_STRATEGY=object(),
    )

    fake_oci.wait_until = lambda *args, **kwargs: None
    fake_oci.wait_until_progress = lambda *args, **kwargs: None

    fake_models = types.SimpleNamespace(
        LaunchInstanceDetails=_Dummy,
        LaunchInstanceShapeConfigDetails=_Dummy,
        InstanceSourceViaImageDetails=_Dummy,
        CreateVnicDetails=_Dummy,
    )

    fake_core = types.SimpleNamespace(
        ComputeClient=_Dummy,
        VirtualNetworkClient=_Dummy,
        models=fake_models,
    )

    fake_identity = types.SimpleNamespace(
        IdentityClient=_Dummy,
    )

    fake_oci.core = fake_core
    fake_oci.identity = fake_identity

    return fake_oci


try:
    import oci as _oci  # type: ignore[assignment]
    # quick smoke check: some submodules may still blow up on import
    from oci import base_client as _base_client  # noqa: F401
    oci = _oci  # noqa: E305
except Exception:
    oci = _build_fake_oci()
    sys.modules["oci"] = oci
