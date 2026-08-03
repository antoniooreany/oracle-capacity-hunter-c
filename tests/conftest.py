import sys
import types


try:
    import oci  # noqa: F401

except ModuleNotFoundError:

    fake_oci = types.ModuleType("oci")


    class FakeServiceError(Exception):
        def __init__(
            self,
            status=500,
            code="FakeError",
            message="fake oci error",
        ):
            super().__init__(message)

            self.status = status
            self.code = code
            self.message = message


    class DummyClient:
        """
        Minimal OCI client replacement.
        Allows tests to import code without OCI SDK installed.
        """

        def __init__(self, *args, **kwargs):
            pass


    class DummyModel:
        """
        Minimal OCI model replacement.
        Stores provided attributes.
        """

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


    # ----------------------------
    # oci.exceptions
    # ----------------------------

    fake_exceptions = types.ModuleType(
        "oci.exceptions"
    )

    fake_exceptions.ServiceError = FakeServiceError


    # ----------------------------
    # oci.config
    # ----------------------------

    fake_config = types.ModuleType(
        "oci.config"
    )

    fake_config.from_file = (
        lambda *args, **kwargs: {}
    )


    # ----------------------------
    # oci.retry
    # ----------------------------

    fake_retry = types.ModuleType(
        "oci.retry"
    )

    fake_retry.DEFAULT_RETRY_STRATEGY = object()


    # ----------------------------
    # oci.core.models
    # ----------------------------

    fake_models = types.ModuleType(
        "oci.core.models"
    )

    fake_models.LaunchInstanceDetails = DummyModel
    fake_models.LaunchInstanceShapeConfigDetails = DummyModel
    fake_models.InstanceSourceViaImageDetails = DummyModel
    fake_models.CreateVnicDetails = DummyModel


    # ----------------------------
    # oci.core
    # ----------------------------

    fake_core = types.ModuleType(
        "oci.core"
    )

    fake_core.ComputeClient = DummyClient
    fake_core.VirtualNetworkClient = DummyClient
    fake_core.models = fake_models


    # ----------------------------
    # oci.identity
    # ----------------------------

    fake_identity = types.ModuleType(
        "oci.identity"
    )

    fake_identity.IdentityClient = DummyClient


    # ----------------------------
    # assemble OCI package
    # ----------------------------

    fake_oci.config = fake_config
    fake_oci.exceptions = fake_exceptions
    fake_oci.retry = fake_retry

    fake_oci.core = fake_core
    fake_oci.identity = fake_identity


    fake_oci.wait_until = (
        lambda *args, **kwargs: None
    )


    # ----------------------------
    # register fake modules
    # ----------------------------

    sys.modules["oci"] = fake_oci

    sys.modules["oci.config"] = fake_config
    sys.modules["oci.exceptions"] = fake_exceptions
    sys.modules["oci.retry"] = fake_retry

    sys.modules["oci.core"] = fake_core
    sys.modules["oci.core.models"] = fake_models

    sys.modules["oci.identity"] = fake_identity
    