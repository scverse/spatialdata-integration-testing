from spatialdata_data_converter.subprocess_runner import run_subprocess
from spatialdata_data_converter.archive import sha256_of_file, zip_directory
import spatialdata_data_converter.config as sdcc
from pathlib import Path
import re
import shlex
import zarr
from zarr.storage import LocalStore


def _zip_name(dataset: str, dataset_suffix: str) -> str:
    return f"{dataset}{dataset_suffix}.zip"


def _zip_dataset(dataset: str, zarr_name: str, dataset_suffix: str) -> Path:
    """Zip `<dataset>/<zarr_name>` into the upload staging folder and return the zip's path.

    Pure Python (see archive.py): the dataset folder is only read, nothing runs in the conda env,
    and identical data always gives a byte-identical zip, so the checksum only changes when the
    data does. The entries keep the `<zarr_name>/...` layout that downstream consumers unzip.
    """
    zarr_path = Path(sdcc.full_path_of_sandbox_file(dataset)) / zarr_name
    zip_path = sdcc.Config.UPLOAD_STAGING_FOLDER / _zip_name(dataset, dataset_suffix)
    print(f"zipping {zarr_path} -> {zip_path}")
    return zip_directory(zarr_path, zip_path, arc_root=zarr_name)


def _compute_checksum(zip_path: Path) -> str:
    """Hex sha256 of the zip (stored remotely as `<name>.zip.checksum`)."""
    return sha256_of_file(zip_path)


def _remote_checksum_exists(dataset: str, dataset_suffix: str) -> bool:
    bash_command = f'rclone -v lsf {sdcc.Config.S3_BUCKET_PATH}/{dataset}{dataset_suffix}.zip.checksum --password-command \\"echo $ABCR8\\"'
    output = run_subprocess(cmd=bash_command, env=sdcc.Config.ENV, update_repos=False)
    return output != ""


def _get_remote_checksum(dataset: str, dataset_suffix: str) -> str | None:
    """The remote sha256, or None if the remote file holds something else (e.g. a legacy `cksum` int)."""
    bash_command = f'rclone -v cat {sdcc.Config.S3_BUCKET_PATH}/{dataset}{dataset_suffix}.zip.checksum --password-command \\"echo $ABCR8\\"'
    output = run_subprocess(cmd=bash_command, env=sdcc.Config.ENV, update_repos=False).strip()
    if not re.fullmatch(r"[0-9a-f]{64}", output):
        print(f'remote checksum is not a sha256 hex digest: "{output}"; treating it as outdated')
        return None
    return output


def _upload_data(dataset: str, zarr_name: str, dataset_suffix: str, zip_path: Path) -> None:
    # rclone copy overwrites the existing file; S3 handles this atomically
    # (the old object remains available until the new upload completes),
    # so there is no need to delete the old file first.
    bash_command = (
        f"cd {sdcc.full_path_of_sandbox_file(dataset)} && "
        # upload zip (built in the staging folder, see _zip_dataset)
        f'rclone -v copy {shlex.quote(str(zip_path))} {sdcc.Config.S3_BUCKET_PATH}/ --password-command \\"echo $ABCR8\\" '
        # when re-enabling the code below, add && to the previous line
        # temporarily disabled because the EMBL S3 bucket does not enable CORS, so we can't make use of the Zarr data
        # Note: when moving to a new S3 bucket we should use sharding to speed up the upload
        # # remove old zarr (in theory not needed, but let's be explicit)
        # f'rclone -v purge {sdcc.Config.S3_BUCKET_PATH}/{dataset}{dataset_suffix}.zarr --password-command \\"echo $ABCR8\\" && '
        # # upload zarr
        # f'rclone -v copy {zarr_name} {sdcc.Config.S3_BUCKET_PATH}/{dataset}{dataset_suffix}.zarr --password-command \\"echo $ABCR8\\" '
    )
    run_subprocess(cmd=bash_command, env=sdcc.Config.ENV, update_repos=False)


def _upload_checksum(dataset: str, checksum: str, dataset_suffix: str) -> None:
    bash_command = f'echo -n "{checksum}" | rclone -v rcat {sdcc.Config.S3_BUCKET_PATH}/{dataset}{dataset_suffix}.zip.checksum --password-command \\"echo $ABCR8\\" '
    run_subprocess(cmd=bash_command, env=sdcc.Config.ENV, update_repos=False)


def upload_to_s3(
    dataset: str, zarr_name: str = "data.zarr",
) -> None:
    sdata_path = Path(sdcc.full_path_of_sandbox_file(dataset)) / zarr_name
    dataset_suffix = get_data_versions_suffix(sdata_path=sdata_path)
    zip_path = _zip_dataset(dataset, zarr_name, dataset_suffix)
    try:
        checksum = _compute_checksum(zip_path)

        if not _remote_checksum_exists(dataset, dataset_suffix):
            print("remote checksum does not exist, uploading the data")
            upload = True
        else:
            remote_checksum = _get_remote_checksum(dataset, dataset_suffix)
            print(f"checksum = {checksum}, remote_checksum = {remote_checksum}")
            upload = checksum != remote_checksum

        if upload:
            _upload_data(dataset, zarr_name, dataset_suffix, zip_path)
            _upload_checksum(
                dataset=dataset, checksum=checksum, dataset_suffix=dataset_suffix
            )
            print("successfully uploaded the data and updated the remote checksum")
        else:
            print("the remote data is already up-to-date")
    finally:
        # the zip is rebuilt on every run; don't let one per dataset/version pile up in staging
        zip_path.unlink(missing_ok=True)

def get_data_versions_suffix(sdata_path: Path) -> str:
    store = LocalStore(str(sdata_path))
    group = zarr.open(store=store, mode='r')
    spatialdata_attrs = group.attrs.get("spatialdata_attrs")
    if spatialdata_attrs is None:
        raise ValueError("spatialdata_attrs not found in the metadata")
    spatialdata_software_version = spatialdata_attrs.get("spatialdata_software_version")
    if spatialdata_software_version is None:
        raise ValueError("spatialdata version not found in the metadata")
    spatialdata_io_software_version = group.attrs.get("spatialdata_io_software_version")
    if spatialdata_io_software_version is None:
        suffix = f'_spatialdata_{spatialdata_software_version}'
    else:
        suffix = f'_spatialdata_{spatialdata_software_version}_spatialdata_io_{spatialdata_io_software_version}'
    return suffix

if __name__ == "__main__":
    upload_to_s3(dataset="xenium_rep1_io", zarr_name="data.zarr")
