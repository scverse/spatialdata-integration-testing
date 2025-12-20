from spatialdata_data_converter.subprocess_runner import run_subprocess
import spatialdata_data_converter.config as sdcc

def _zip_dataset(dataset: str, zarr_name: str, dataset_suffix: str) -> None:
    bash_command = (
        f"cd {sdcc.full_path_of_sandbox_file(dataset)} && "
        # we need to force a single timestamp (let's use an arbitrary one) otherwise the checksup will always be different
        f"touch -d 1970-01-01T00:00:00Z {zarr_name}/zmetadata && "
        # let's be explicit and delete the old zip file
        f"rm -f {dataset}{dataset_suffix}.zip && "
        # let's force zip not to add new timestamps and to set all the timestamps to the oldest one (the one above)
        f"zip -r -oX {dataset}{dataset_suffix}.zip {zarr_name} "
    )
    run_subprocess(cmd=bash_command, env=sdcc.Config.ENV, update_repos=False)


def _compute_checksum(dataset: str, dataset_suffix: str) -> int:
    bash_command = (
        f"cd {sdcc.full_path_of_sandbox_file(dataset)} && "
        f"cksum {dataset}{dataset_suffix}.zip"
    )
    output = run_subprocess(cmd=bash_command, env=sdcc.Config.ENV, update_repos=False)
    splits = output.split(" ")
    assert splits[-1] == f"{dataset}{dataset_suffix}.zip\n"
    checksum = int(splits[0])
    return checksum


def _remote_checksum_exists(dataset: str, dataset_suffix: str) -> bool:
    bash_command = f'rclone -v lsf {sdcc.Config.S3_BUCKET_PATH}/{dataset}{dataset_suffix}.zip.checksum --password-command \\"echo $ABCR8\\"'
    output = run_subprocess(cmd=bash_command, env=sdcc.Config.ENV, update_repos=False)
    return output != ""


def _get_remote_checksum(dataset: str, dataset_suffix: str) -> int:
    bash_command = f'rclone -v cat {sdcc.Config.S3_BUCKET_PATH}/{dataset}{dataset_suffix}.zip.checksum --password-command \\"echo $ABCR8\\"'
    output = run_subprocess(cmd=bash_command, env=sdcc.Config.ENV, update_repos=False)
    # print(f'remote_checksum="{output}"')
    if not output.isdigit():
        raise ValueError(
            f'Remote checksum does not appear to be a non-negative integer: "{output}"'
        )
    return int(output)


def _upload_data(dataset: str, zarr_name: str, dataset_suffix: str) -> None:
    # check if old zip exists (deletefile will fail if the file doesn't exist)
    bash_command = (
        f"cd {sdcc.full_path_of_sandbox_file(dataset)} && "
        f'rclone -v lsf {sdcc.Config.S3_BUCKET_PATH}/{dataset}{dataset_suffix}.zip --password-command \\"echo $ABCR8\\" '
    )
    output = run_subprocess(cmd=bash_command, env=sdcc.Config.ENV, update_repos=False)

    # remove old zip (in theory not needed, but let's be explicit)
    print(f'output of lsf: "{output}"')
    if output == f"{dataset}{dataset_suffix}.zip\n":
        bash_command = (
            f"cd {sdcc.full_path_of_sandbox_file(dataset)} && "
            f'rclone -v deletefile {sdcc.Config.S3_BUCKET_PATH}/{dataset}{dataset_suffix}.zip --password-command \\"echo $ABCR8\\" '
        )
        output = run_subprocess(cmd=bash_command, env=sdcc.Config.ENV, update_repos=False)

    bash_command = (
        f"cd {sdcc.full_path_of_sandbox_file(dataset)} && "
        # upload zip
        f'rclone -v copy {dataset}{dataset_suffix}.zip {sdcc.Config.S3_BUCKET_PATH}/ --password-command \\"echo $ABCR8\\" '
        # when re-enabling the code below, add && to the previous line
        # temporarily disabled because the EMBL S3 bucket does not enable CORS, so we can't make use of the Zarr data
        # Note: when moving to a new S3 bucket we should use sharding to speed up the upload
        # # remove old zarr (in theory not needed, but let's be explicit)
        # f'rclone -v purge {sdcc.Config.S3_BUCKET_PATH}/{dataset}{dataset_suffix}.zarr --password-command \\"echo $ABCR8\\" && '
        # # upload zarr
        # f'rclone -v copy {zarr_name} {sdcc.Config.S3_BUCKET_PATH}/{dataset}{dataset_suffix}.zarr --password-command \\"echo $ABCR8\\" '
    )
    run_subprocess(cmd=bash_command, env=sdcc.Config.ENV, update_repos=False)


def _upload_checksum(dataset: str, checksum: int, dataset_suffix: str) -> None:
    bash_command = f'echo -n "{checksum}" | rclone -v rcat {sdcc.Config.S3_BUCKET_PATH}/{dataset}{dataset_suffix}.zip.checksum --password-command \\"echo $ABCR8\\" '
    run_subprocess(cmd=bash_command, env=sdcc.Config.ENV, update_repos=False)


def upload_to_s3(
    dataset: str, zarr_name: str = "data.zarr", dataset_suffix: str = ""
) -> None:
    _zip_dataset(dataset, zarr_name, dataset_suffix)
    checksum = _compute_checksum(dataset, dataset_suffix)

    if not _remote_checksum_exists(dataset, dataset_suffix):
        print("remote checksum does not exist, uploading the data")
        upload = True
    else:
        remote_checksum = _get_remote_checksum(dataset, dataset_suffix)
        print(f"checksum = {checksum}, remote_checksum = {remote_checksum}")
        if checksum != remote_checksum:
            upload = True
        else:
            upload = False

    if upload:
        _upload_data(dataset, zarr_name, dataset_suffix)
        _upload_checksum(
            dataset=dataset, checksum=checksum, dataset_suffix=dataset_suffix
        )
        print("successfully uploaded the data and updated the remote checksum")
    else:
        print("the remote data is already up-to-date")


if __name__ == "__main__":
    upload_to_s3(dataset="visium", zarr_name="data.zarr", dataset_suffix="_dev")
