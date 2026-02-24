import os

# os.environ['HTTP_PROXY'] = 'http://193.174.53.86:465'
# os.environ['HTTPS_PROXY'] = 'https://193.174.53.86:465'

from datetime import datetime
from pathlib import Path
import subprocess

config_file_path = Path(__file__).parent


def read_envvars_from_sh(envvars_path):
    """Reads environment variables from a shell script by sourcing it."""
    # Use 'set -a' to export all variables, then source the file, then printenv
    command = f"set -a && source \"{envvars_path}\" && python3 -c \"import os, json; print(json.dumps({{k: os.environ[k] for k in ['BASHRC', 'CONDA_SH'] if k in os.environ}}))\""
    result = subprocess.run(
        ["bash", "-c", command], capture_output=True, text=True, check=True
    )
    import json

    return json.loads(result.stdout)


class Config:
    ROOT_FOLDER = config_file_path.parent.parent
    AIRFLOW_FOLDER = ROOT_FOLDER / "airflow"
    DAGS_PATH = AIRFLOW_FOLDER / "dags"
    REPOSITORIES_FOLDER = ROOT_FOLDER / "dependencies"
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
    ]
    DATASETS_NO_DOWNLOAD = []
    # usage:
    # 'main' for main branch
    # 'branch-name' for a specific branch
    # 'pr 329' for pull request 329
    # None for latest release
    REPOSITORIES = {
        "spatialdata": 'main',
        "spatialdata-io": 'pr 370',
        "spatialdata-plot": 'main',
        "napari-spatialdata": 'main',
        "spatialdata-notebooks": 'main',
        "spatialdata-sandbox": 'main',
        "squidpy": 'pr 1068',
    }
    S3_BUCKET_PATH = "embl-s3:/spatialdata/spatialdata-sandbox"
    ENV = "ome_sdc"
    EMAILS = []

    # Read BASHRC and CONDA_SH from envvars.sh; this file should be manually created
    # (see template_envvars.sh in the repository root)
    envvars_path = ROOT_FOLDER / "envvars.sh"
    _env = read_envvars_from_sh(envvars_path)
    BASHRC = os.path.expanduser(_env.get("BASHRC"))
    CONDA_SH = os.path.expanduser(_env.get("CONDA_SH"))


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
    return f'cd {Config.ROOT_FOLDER} && PYTHONUNBUFFERED=1 pixi run python -m spatialdata_data_converter {cli_args}'


if __name__ == "__main__":
    print(Config.BASHRC)
    print(Config.CONDA_SH)
