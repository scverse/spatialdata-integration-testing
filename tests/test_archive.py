import os
import zipfile
from pathlib import Path

import pytest

from spatialdata_data_converter.archive import sha256_of_file, zip_directory

FILES = {
    "zarr.json": b'{"zarr_format": 3, "node_type": "group"}',
    "images/zarr.json": b"{}",
    "images/img/0/c/0/0/0": os.urandom(4096),
    "images/img/0/c/0/0/1": b"\x00" * 100,
    "points/pts/points.parquet/part.0.parquet": os.urandom(1000),
    "tables/table/obs/.zattrs": b"",  # empty file
}


def _make_tree(root: Path, mtime: int) -> Path:
    zarr = root / "data.zarr"
    for rel, data in FILES.items():
        path = zarr / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (zarr / "labels").mkdir()  # empty directory
    for path in [zarr, *zarr.rglob("*")]:
        os.utime(path, (mtime, mtime))
    return zarr


def test_zip_is_deterministic(tmp_path):
    # same content written at different times (and different source locations) -> same bytes
    zarr_a = _make_tree(tmp_path / "a", mtime=1_000_000_000)
    zarr_b = _make_tree(tmp_path / "b", mtime=1_700_000_000)
    zip_a1 = zip_directory(zarr_a, tmp_path / "out" / "a1.zip")
    zip_a2 = zip_directory(zarr_a, tmp_path / "out" / "a2.zip")
    zip_b = zip_directory(zarr_b, tmp_path / "out" / "b.zip")

    assert zip_a1.read_bytes() == zip_a2.read_bytes() == zip_b.read_bytes()
    assert sha256_of_file(zip_a1) == sha256_of_file(zip_b)
    assert len(sha256_of_file(zip_a1)) == 64


def test_checksum_changes_with_content(tmp_path):
    zarr = _make_tree(tmp_path, mtime=1_000_000_000)
    before = sha256_of_file(zip_directory(zarr, tmp_path / "before.zip"))
    (zarr / "images" / "zarr.json").write_bytes(b'{"changed": true}')
    after = sha256_of_file(zip_directory(zarr, tmp_path / "after.zip"))
    assert before != after


def test_zip_roundtrips(tmp_path):
    zarr = _make_tree(tmp_path / "src", mtime=1_000_000_000)
    zip_path = zip_directory(zarr, tmp_path / "staging" / "ds_spatialdata_0.1.zip")

    with zipfile.ZipFile(zip_path) as zf:
        assert zf.testzip() is None
        names = zf.namelist()
        # layout consumers rely on: everything below data.zarr/, sorted, with directory entries
        assert all(name.startswith("data.zarr/") for name in names)
        assert names[0] == "data.zarr/" and len(names) == len(set(names))
        assert "data.zarr/labels/" in names
        assert {i.date_time for i in zf.infolist()} == {(1980, 1, 1, 0, 0, 0)}
        zf.extractall(tmp_path / "unzipped")

    out = tmp_path / "unzipped" / "data.zarr"
    for rel, data in FILES.items():
        assert (out / rel).read_bytes() == data
    assert (out / "labels").is_dir()
    # nothing was written into the source tree, and no partial files are left in staging
    assert sorted(p.name for p in (tmp_path / "src").iterdir()) == ["data.zarr"]
    assert [p.name for p in (tmp_path / "staging").iterdir()] == [zip_path.name]


def test_arc_root_and_missing_dir(tmp_path):
    zarr = _make_tree(tmp_path, mtime=1_000_000_000)
    with zipfile.ZipFile(zip_directory(zarr, tmp_path / "x.zip", arc_root="other.zarr")) as zf:
        assert all(n.startswith("other.zarr/") for n in zf.namelist())
    with pytest.raises(NotADirectoryError):
        zip_directory(tmp_path / "missing.zarr", tmp_path / "y.zip")
