import hashlib
import io
from pathlib import Path

import pytest

from spatialdata_data_converter.s3_publish import get_remote_checksum, publish_zip

BUCKET = "bucket"
PREFIX = "spatialdata/spatialdata-sandbox"


class _Missing(Exception):
    """Stands in for botocore's ClientError on a missing key."""

    response = {"Error": {"Code": "NoSuchKey"}}


class FakeS3:
    """The four calls the uploader makes, backed by a dict."""

    def __init__(self, objects=None):
        self.objects = dict(objects or {})
        self.calls = []

    def get_object(self, Bucket, Key):
        self.calls.append(("get_object", Key))
        if (Bucket, Key) not in self.objects:
            raise _Missing()
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}

    def upload_file(self, Filename, Bucket, Key, ExtraArgs=None):
        self.calls.append(("upload_file", Key))
        self.objects[(Bucket, Key)] = Path(Filename).read_bytes()

    def put_object(self, Bucket, Key, Body, ContentType=None):
        self.calls.append(("put_object", Key))
        self.objects[(Bucket, Key)] = Body


@pytest.fixture
def zip_file(tmp_path):
    path = tmp_path / "visium_spatialdata_0.8.1.zip"
    path.write_bytes(b"PK\x03\x04 not really a zip")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


ZIP_KEY = f"{PREFIX}/visium_spatialdata_0.8.1.zip"


def test_uploads_zip_then_checksum_when_remote_missing(zip_file):
    path, checksum = zip_file
    s3 = FakeS3()
    assert publish_zip(s3, BUCKET, PREFIX, path, checksum) is True
    assert s3.objects[(BUCKET, ZIP_KEY)] == path.read_bytes()
    assert s3.objects[(BUCKET, ZIP_KEY + ".checksum")] == checksum.encode()
    writes = [c for c in s3.calls if c[0] != "get_object"]
    assert writes == [("upload_file", ZIP_KEY), ("put_object", ZIP_KEY + ".checksum")]


def test_skips_when_remote_checksum_matches(zip_file):
    path, checksum = zip_file
    s3 = FakeS3({(BUCKET, ZIP_KEY + ".checksum"): checksum.encode() + b"\n"})
    assert publish_zip(s3, BUCKET, PREFIX, path, checksum) is False
    assert s3.calls == [("get_object", ZIP_KEY + ".checksum")]


@pytest.mark.parametrize("remote", [b"0" * 64, b"3141592653", b""])
def test_reuploads_on_other_or_legacy_checksum(zip_file, remote):
    path, checksum = zip_file
    s3 = FakeS3({(BUCKET, ZIP_KEY + ".checksum"): remote})
    assert publish_zip(s3, BUCKET, PREFIX, path, checksum) is True
    assert s3.objects[(BUCKET, ZIP_KEY + ".checksum")] == checksum.encode()


def test_prefix_slashes_are_normalised(zip_file):
    path, checksum = zip_file
    s3 = FakeS3()
    publish_zip(s3, BUCKET, f"/{PREFIX}/", path, checksum)
    assert (BUCKET, ZIP_KEY) in s3.objects


def test_other_errors_propagate():
    class Denied(Exception):
        response = {"Error": {"Code": "AccessDenied"}}

    class S3:
        def get_object(self, Bucket, Key):
            raise Denied()

    with pytest.raises(Denied):
        get_remote_checksum(S3(), BUCKET, "k")


def test_rejects_non_sha256_checksum(zip_file):
    path, _ = zip_file
    with pytest.raises(ValueError):
        publish_zip(FakeS3(), BUCKET, PREFIX, path, "1234")
