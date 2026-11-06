from spatialdata_data_converter.archive import sha256_of_file, zip_directory
from spatialdata_data_converter.s3_publish import make_client, publish_zip
import spatialdata_data_converter.config as sdcc
from pathlib import Path
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


def upload_to_s3(
    dataset: str, zarr_name: str = "data.zarr",
) -> None:
    """Zip the dataset and publish it to Config.S3_BUCKET/Config.S3_PREFIX (see s3_publish.py).

    Only Python from this repository's environment runs here (no conda env, no shell, no rclone):
    on manny this runs as the user holding the S3 key, which must not execute anything the test
    tasks can write. Only the zip is published (as before); publishing the zarr itself is left
    for later.
    """
    sdata_path = Path(sdcc.full_path_of_sandbox_file(dataset)) / zarr_name
    dataset_suffix = get_data_versions_suffix(sdata_path=sdata_path)
    zip_path = _zip_dataset(dataset, zarr_name, dataset_suffix)
    try:
        checksum = _compute_checksum(zip_path)
        publish_zip(
            make_client(sdcc.Config.S3_REGION),
            bucket=sdcc.Config.S3_BUCKET,
            prefix=sdcc.Config.S3_PREFIX,
            zip_path=zip_path,
            checksum=checksum,
        )
        print(f"public URL: {sdcc.Config.S3_PUBLIC_URL}/{zip_path.name}")
    finally:
        # the zip is rebuilt on every run; don't let one per dataset/version pile up in staging
        zip_path.unlink(missing_ok=True)

def get_data_versions_suffix(sdata_path: Path) -> str:
    # read-only: the uploader must never modify the dataset (and may lack write access to it)
    store = LocalStore(str(sdata_path), read_only=True)
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
