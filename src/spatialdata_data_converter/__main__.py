import click
from spatialdata_data_converter.subprocess_runner import (
    run_subprocess,
    run_script,
    run_notebook,
)
import spatialdata_data_converter.config as sdcc  # we import this so if Config is changed (via code), the changes are available
from spatialdata_data_converter.utils import update_all_repos
from spatialdata_data_converter.symlinker import make_all_symlinks
from spatialdata_data_converter.uploader import upload_to_s3
from pathlib import Path


@click.group()
def cli():
    """Spatialdata Data Converter CLI"""
    pass


@cli.command()
def install_env():
    """Install the environment."""
    path = sdcc.Config.COMMANDS_FOLDER / "install_env.sh"
    run_subprocess(
        cmd=f"bash {path}",
        env="base",
        update_repos=False,
        # env_vars={"BASHRC": sdcc.Config.BASHRC, "CONDA_SH": sdcc.Config.CONDA_SH},
    )

@cli.command()
@click.option("--spatialdata", default="<unchanged>", help="Branch for spatialdata (default: <unchanged>)")
@click.option("--spatialdata-io", default="<unchanged>", help="Branch for spatialdata-io (default: <unchanged>)")
@click.option("--spatialdata-plot", default="<unchanged>", help="Branch for spatialdata-plot (default: <unchanged>)")
@click.option("--napari-spatialdata", default="<unchanged>", help="Branch for napari-spatialdata (default: <unchanged>)")
@click.option("--spatialdata-notebooks", default="<unchanged>", help="Branch for spatialdata-notebooks (default: <unchanged>)")
@click.option("--spatialdata-sandbox", default="<unchanged>", help="Branch for spatialdata-sandbox (default: <unchanged>)")
@click.option("--squidpy", default="<unchanged>", help="Branch for squidpy (default: <unchanged>)")
def update_repos(
    spatialdata,
    spatialdata_io,
    spatialdata_plot,
    napari_spatialdata,
    spatialdata_notebooks,
    spatialdata_sandbox,
    squidpy,
):
    """Update all repositories with specified branches/prs."""
    args = {
        "spatialdata": spatialdata,
        "spatialdata-io": spatialdata_io,
        "spatialdata-plot": spatialdata_plot,
        "napari-spatialdata": napari_spatialdata,
        "spatialdata-notebooks": spatialdata_notebooks,
        "spatialdata-sandbox": spatialdata_sandbox,
        "squidpy": squidpy,
    }

    changed = False
    for repo, new_branch in args.items():
        current_branch = sdcc.Config.REPOSITORIES.get(repo)
        # Acceptable: string (no spaces), string with "pr <number>", or None
        if new_branch == "<unchanged>":
            continue
        if new_branch == "None":
            new_branch = None
        if current_branch != new_branch:
            print(f"Changing {repo}: {current_branch!r} -> {new_branch!r}")
            sdcc.Config.REPOSITORIES[repo] = new_branch
            changed = True

    if not changed:
        print("No changes made to repository configuration.")

    print("\nCurrent repository configuration:")
    for repo, branch in sdcc.Config.REPOSITORIES.items():
        print(f"  {repo}: {branch!r}")
    update_all_repos()


@cli.command()
@click.option(
    "--dataset",
    default=None,
)
def download(dataset: str):
    """Download dataset listed in spatialdata-sandbox."""
    script_folder = sdcc.Config.REPOSITORIES_FOLDER / "spatialdata-sandbox" / dataset
    if not script_folder.exists():
        raise click.ClickException(
            f"Dataset {dataset} does not exist in spatialdata-sandbox."
        )
    run_script(
    script_folder=script_folder, script="download", env=sdcc.Config.ENV, update_repos=False
    )


@cli.command()
@click.option(
    "--dataset",
    default=None,
    help="Specific dataset to create symlinks for. If not provided, creates all symlinks.",
)
def create_symlinks(dataset: str):
    if dataset:
        from spatialdata_data_converter.symlinker import make_symlinks
        make_symlinks(dataset)()
    else:
        make_all_symlinks()


@cli.command()
@click.option(
    "--dataset",
    default=None,
)
def to_zarr(dataset: str):
    """Convert to Zarr format."""
    script_folder = sdcc.Config.REPOSITORIES_FOLDER / "spatialdata-sandbox" / dataset
    if not script_folder.exists():
        raise click.ClickException(
            f"Dataset {dataset} does not exist in spatialdata-sandbox."
        )
    run_script(
        script_folder=script_folder, script="to_zarr", env=sdcc.Config.ENV, update_repos=False
    )


@cli.command()
@click.option(
    "--notebook",
    default=None,
)
def run_docs_notebook(notebook: str):
    """Run a documentation notebook."""
    run_notebook(
        notebook_folder=sdcc.Config.DOCS_NOTEBOOKS_FOLDER,
        notebook=notebook,
        env=sdcc.Config.ENV,
        update_repos=False,
    )


@cli.command()
@click.option(
    "--notebook",
    default=None,
)
def run_reproducibility_notebook(notebook: str):
    """Run a reproducibility notebook."""
    run_notebook(
        notebook_folder=sdcc.Config.REPRODUCIBILITY_NOTEBOOKS_FOLDER,
        notebook=notebook,
        env=sdcc.Config.ENV,
        update_repos=False,
    )


def _run_tests(repo, test_path, docker=None):
    """Run pytest for the given repo in dependencies, optionally on a specific test file."""
    import platform
    import subprocess

    repo_path = sdcc.Config.REPOSITORIES_FOLDER / repo

    # Handle Docker option for spatialdata-plot
    # docker=None (default): auto-detect, use Docker on macOS
    # docker=True: force Docker
    # docker=False: don't use Docker
    use_docker = docker
    if docker is None and repo == "spatialdata-plot":
        # Auto-detect: use Docker on macOS
        use_docker = platform.system() == "Darwin"
        if use_docker:
            print("Detected macOS, using Docker for spatialdata-plot tests.")

    if use_docker and repo == "spatialdata-plot":
        # Check if Docker image exists
        result = subprocess.run(
            ["docker", "images", "-q", "sit-spatialdata-plot:latest"],
            capture_output=True,
            text=True,
        )
        if not result.stdout.strip():
            raise click.ClickException(
                "Docker image 'sit-spatialdata-plot:latest' not found.\n"
                "Please build it by running:\n\n"
                f"  cd {repo_path}\n"
                "  docker build --build-arg TARGETPLATFORM=linux/arm64 --tag sit-spatialdata-plot -f test.Dockerfile .\n"
            )

        # Run tests in Docker
        docker_cmd = "docker run --rm sit-spatialdata-plot python -m pytest"
        if test_path:
            full_test_path = Path(ssdc.Config.REPOSITORIES_FOLDER) / 'spatialdata-plot' / 'tests' / test_path
            docker_cmd += f" {full_test_path}"
        subprocess.run(docker_cmd, shell=True, check=True)
        return

    path = repo_path / "tests"
    if test_path:
        path = path / test_path
    run_subprocess(
        cmd=f"pushd . && cd {repo_path} && python -m pytest -v {str(path)} && popd",
        env=sdcc.Config.ENV,
        update_repos=False,
    )


@cli.command()
@click.option(
    "--repo",
    required=True,
    type=click.Choice(
        [
            "spatialdata",
            "spatialdata-io",
            "spatialdata-plot",
            "napari-spatialdata",
            "spatialdata-sandbox",
        ],
        case_sensitive=True,
    ),
    help="Name of the repo to test.",
)
@click.option(
    "--test-path",
    required=False,
    default=None,
    help="Optional path to a specific test file (relative to the repo's tests directory).",
)
@click.option(
    "--docker/--no-docker",
    default=None,
    help="Run tests in Docker. Default: auto-detect (use Docker on macOS for spatialdata-plot).",
)
def run_tests(repo, test_path, docker):
    """Run pytest for the given repo in dependencies, optionally on a specific test file."""
    _run_tests(repo, test_path, docker)


# @cli.command()
# def run_tests_spatialdata_sandbox_visium():
#     _run_tests(repo="spatialdata-sandbox", test_path="test_to_zarr_visium.py")
#
#
# @cli.command()
# def run_tests_spatialdata_sandbox_visium_hd():
#     _run_tests(repo="spatialdata-sandbox", test_path="test_to_zarr_visium_hd.py")
#
#
# @cli.command()
# def run_tests_spatialdata_sandbox_xenium():
#     _run_tests(repo="spatialdata-sandbox", test_path="test_to_zarr_xenium.py")


@cli.command()
def update_dev_datasets():
    """Update development datasets."""
    from spatialdata_data_converter.dev_datasets import update_dev_datasets_func

    update_dev_datasets_func()


@cli.command()
def download_spatialdata_io_dev_datasets():
    """Download spatialdata-io dev/test datasets (from prepare_test_data.yaml workflow)."""
    from spatialdata_data_converter.spatialdata_io_datasets import download_spatialdata_io_dev_datasets_func

    download_spatialdata_io_dev_datasets_func()


@cli.command()
@click.option(
    "--dataset",
    default=None,
)
@click.option(
    "--zarr-name",
    default="data.zarr",
    help="Name of the zarr file to upload (default: data.zarr).",
)
@click.option(
    "--dataset-suffix",
    default="_dev",
    help="Suffix for the dataset name, e.g., '_dev' or '_spatialdata_v0.7.0_spatialdata_io_v0.6.0'. Default: '_dev'.",
)
def upload(dataset: str, zarr_name: str = "data.zarr", dataset_suffix: str = "_dev"):
    """Upload dataset to S3."""

    if not dataset:
        raise click.ClickException("Dataset name is required.")

    upload_to_s3(dataset=dataset, zarr_name=zarr_name, dataset_suffix=dataset_suffix)


if __name__ == "__main__":
    cli()
