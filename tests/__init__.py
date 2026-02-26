import os
import warnings


def _configure_test_runtime():
    flask_env = os.environ.get("FLASK_ENV")
    if os.environ.get("FLASK_DEBUG") is None and flask_env:
        os.environ["FLASK_DEBUG"] = "1" if flask_env.lower() == "development" else "0"
    os.environ.pop("FLASK_ENV", None)

    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", message=r".*FLASK_ENV.*")


_configure_test_runtime()
