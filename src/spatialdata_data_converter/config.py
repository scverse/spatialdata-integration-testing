import os

# os.environ['HTTP_PROXY'] = 'http://193.174.53.86:465'
# os.environ['HTTPS_PROXY'] = 'https://193.174.53.86:465'

from datetime import datetime
from pathlib import Path
import getpass
import subprocess
import tempfile

config_file_path = Path(__file__).parent


def read_envvars_from_sh(envvars_path):
    """Reads environment variables from a shell script by sourcing it."""
    # Use 'set -a' to export all variables, then source the file, then printenv
    command = f"set -a && source \"{envvars_path}\" && python3 -c \"import os, json; print(json.dumps({{k: os.environ[k] for k in ['BASHRC', 'CONDA_SH', 'SDC_WORKSPACE', 'SDC_PYTEST_WORKERS', 'SDC_UPLOAD_STAGING'] if k in os.environ}}))\""
    result = subprocess.run(
        ["bash", "-c", command], capture_output=True, text=True, check=True
    )
    import json

    return json.loads(result.stdout)


def _workspace_folder(root_folder: Path, env: dict) -> Path:
    """Folder holding the checked-out repositories (and, inside them, all data).

    Defaults to the `dependencies/` submodules of this repository. Set SDC_WORKSPACE (environment or
    envvars.sh) to keep that mutable state outside the checkout, e.g. on a server where the checkout
    is read-only for the user running the tasks. Repositories missing there are cloned by `update-repos`.
    """
    value = os.environ.get("SDC_WORKSPACE") or env.get("SDC_WORKSPACE")
    if not value:
        return root_folder / "dependencies"
    path = Path(os.path.expanduser(value))
    return path if path.is_absolute() else root_folder / path


def _pytest_workers(env: dict) -> str:
    """Value for pytest-xdist's `-n` in `run-tests`.

    Defaults to `auto` (one worker per CPU). Set SDC_PYTEST_WORKERS (environment or envvars.sh) to a
    number to bound memory: each worker imports the full stack, so `auto` on a 16-core server runs
    16 of them per test suite.
    """
    value = (os.environ.get("SDC_PYTEST_WORKERS") or env.get("SDC_PYTEST_WORKERS") or "auto").strip()
    if not (value.isdigit() or value in ("auto", "logical")):
        raise ValueError(f"SDC_PYTEST_WORKERS must be a number, 'auto' or 'logical', got {value!r}")
    return value


def _upload_staging_folder(env: dict) -> Path:
    """Where `upload` builds the dataset zips before sending them to S3.

    Defaults to a per-user folder in the system temp dir. Set SDC_UPLOAD_STAGING (environment or
    envvars.sh) to put it elsewhere, e.g. on a disk with room for the largest dataset zip. The
    zip is written here instead of next to the dataset, so the upload works with read-only access
    to the workspace; it is deleted after each upload.
    """
    value = os.environ.get("SDC_UPLOAD_STAGING") or env.get("SDC_UPLOAD_STAGING")
    if not value:
        return Path(tempfile.gettempdir()) / f"sdc-upload-staging-{getpass.getuser()}"
    return Path(os.path.expanduser(value)).absolute()


class Config:
    ROOT_FOLDER = config_file_path.parent.parent
    AIRFLOW_FOLDER = ROOT_FOLDER / "airflow"
    DAGS_PATH = AIRFLOW_FOLDER / "dags"
    # Read BASHRC, CONDA_SH and (optionally) SDC_WORKSPACE / SDC_PYTEST_WORKERS /
    # SDC_UPLOAD_STAGING from envvars.sh;
    # this file should be manually created (see template_envvars.sh in the repository root)
    envvars_path = ROOT_FOLDER / "envvars.sh"
    _env = read_envvars_from_sh(envvars_path)
    BASHRC = os.path.expanduser(_env.get("BASHRC"))
    CONDA_SH = os.path.expanduser(_env.get("CONDA_SH"))
    REPOSITORIES_FOLDER = _workspace_folder(ROOT_FOLDER, _env)
    PYTEST_WORKERS = _pytest_workers(_env)
    UPLOAD_STAGING_FOLDER = _upload_staging_folder(_env)
    COMMANDS_FOLDER = config_file_path / "commands"
    DOCS_NOTEBOOKS_FOLDER = os.path.join(
        REPOSITORIES_FOLDER, "spatialdata-notebooks/notebooks/examples"
    )
    REPRODUCIBILITY_NOTEBOOKS_FOLDER = os.path.join(
        REPOSITORIES_FOLDER, "spatialdata-notebooks/notebooks/paper_reproducibility"
    )
    DEV_DATASETS_FOLDER = os.path.join(
        REPOSITORIES_FOLDER,
        "spatialdata-notebooks/notebooks/developers_resources/storage_format",
    )
    DATASETS = [
        "visium",  # symlinked to visium_brain
        "merfish",
        "mibitof",
        "mouse_liver",
        "spacem_helanih3t3",
        "visium_associated_xenium_io",
        "visium_hd_3.0.0_io",
        "visium_hd_4.0.1_io",
        "xenium_2.0.0_io",
        "xenium_rep1_io",
        # raw data for the create_cells_dataset notebook; it is used as-is by the
        # notebook, so it is not converted to zarr nor uploaded (see the lists below)
        "xenium_prime_cervical_3.0.0_io",
    ]
    DATASETS_NO_DOWNLOAD = []
    # datasets that are downloaded but have no to_zarr.py / are not published on S3
    DATASETS_NO_TO_ZARR = ["xenium_prime_cervical_3.0.0_io"]
    DATASETS_NO_UPLOAD = ["xenium_prime_cervical_3.0.0_io"]
    # usage:
    # 'main' for main branch
    # 'branch-name' for a specific branch
    # 'pr 329' for pull request 329
    # None for latest release
    REPOSITORIES = {
        "spatialdata": 'main',
        "spatialdata-io": 'main',
        "spatialdata-plot": 'main',
        "napari-spatialdata": 'main',
        "spatialdata-notebooks": 'main',
        "spatialdata-sandbox": 'main',
        "squidpy": 'main',
    }
    S3_BUCKET_PATH = "embl-s3:/spatialdata/spatialdata-sandbox"
    ENV = "ome_sdc"
    EMAILS = []


def branch_envvar(repo: str) -> str:
    """Env var that overrides Config.REPOSITORIES[repo] for `update-repos` (set by the Airflow DAG params)."""
    return "SDC_BRANCH_" + repo.upper().replace("-", "_")


def full_path_of_sandbox_file(file: str) -> str:
    return os.path.join(Config.REPOSITORIES_FOLDER, "spatialdata-sandbox", file)


def full_path_of_dag_file(dag_file: str) -> str:
    return os.path.join(Config.DAGS_PATH, dag_file)


def get_airflow_default_args():
    return {
        "owner": "airflow",
        "depends_on_past": False,
        "start_date": datetime(2023, 6, 26),
        "email": Config.EMAILS,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 0,
    }


def get_cli_command(cli_args: str) -> str:
    """Build CLI command using pixi."""
    # PYTHONUNBUFFERED=1 ensures real-time log output in Airflow UI
    # --as-is: use the already-installed environment without checking/updating pixi.lock or
    # (re)installing. Tasks then never write to .pixi/, so they can run as a user that has only
    # read access to it (e.g. Airflow's run_as_user / default_impersonation). The environment is
    # installed by whoever starts Airflow (`pixi run airflow ...` or `pixi install`).
    return f'cd {Config.ROOT_FOLDER} && PYTHONUNBUFFERED=1 pixi run --as-is python -m spatialdata_data_converter {cli_args}'


if __name__ == "__main__":
    print(Config.BASHRC)
    print(Config.CONDA_SH)
