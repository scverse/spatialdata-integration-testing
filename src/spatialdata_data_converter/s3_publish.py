"""Publish a dataset zip (+ its sha256 in `<name>.checksum`) to S3 with boto3.

Kept free of `config` (which sources envvars.sh on import) so it can be unit-tested with a fake
client. Credentials come from boto3's standard chain (env vars, ~/.aws/credentials, ...); nothing
secret lives in this repository, in envvars.sh, or on a command line.
"""

from __future__ import annotations

import re
from pathlib import Path

SHA256_HEX = re.compile(r"[0-9a-f]{64}")


def make_client(region: str):
    import boto3  # imported lazily: only the upload command needs it

    return boto3.client("s3", region_name=region)


def _is_missing(error: Exception) -> bool:
    response = getattr(error, "response", None) or {}
    return response.get("Error", {}).get("Code") in ("NoSuchKey", "404", "NotFound")


def get_remote_checksum(s3, bucket: str, key: str) -> str | None:
    """The sha256 stored at `key`, or None if there is none or it holds something else
    (e.g. a legacy `cksum` integer), in which case the data counts as outdated."""
    try:
        body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    except Exception as e:  # botocore.exceptions.ClientError; not imported to keep this boto3-free
        if _is_missing(e):
            return None
        raise
    value = body.decode("utf-8", errors="replace").strip()
    if not SHA256_HEX.fullmatch(value):
        print(f'remote checksum is not a sha256 hex digest: "{value}"; treating it as outdated')
        return None
    return value


def publish_zip(s3, bucket: str, prefix: str, zip_path: Path, checksum: str) -> bool:
    """Upload `zip_path` to `s3://bucket/prefix/<zip name>` unless the remote checksum already
    matches. Returns True if it uploaded.

    The zip goes first and the checksum last, so a failed or interrupted upload leaves the old
    (or no) checksum and the next run uploads again. S3 replaces an object atomically: readers
    see the old zip until the new one is complete.
    """
    if not SHA256_HEX.fullmatch(checksum):
        raise ValueError(f"not a sha256 hex digest: {checksum!r}")
    zip_key = f"{prefix.strip('/')}/{zip_path.name}"
    checksum_key = f"{zip_key}.checksum"

    remote = get_remote_checksum(s3, bucket, checksum_key)
    print(f"checksum = {checksum}, remote_checksum = {remote}")
    if remote == checksum:
        print(f"s3://{bucket}/{zip_key} is already up to date")
        return False

    print(f"uploading {zip_path} -> s3://{bucket}/{zip_key}")
    # upload_file switches to a multipart upload for large files (the biggest zips are several GB)
    s3.upload_file(str(zip_path), bucket, zip_key, ExtraArgs={"ContentType": "application/zip"})
    s3.put_object(
        Bucket=bucket, Key=checksum_key, Body=checksum.encode(), ContentType="text/plain"
    )
    print(f"uploaded s3://{bucket}/{zip_key} and its checksum")
    return True
