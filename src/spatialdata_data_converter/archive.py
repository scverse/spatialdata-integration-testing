"""Deterministic zip archives and checksums for the upload step, in pure Python.

No shell tools (`zip`, `touch`, `cksum`) and nothing from the `ome_sdc` conda env: this
module only needs the standard library, so it can run as a user that must not execute code
from that (test-writable) env. It reads the dataset and never writes next to it.
"""

import hashlib
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

# Every entry gets the same timestamp and permissions, so identical data gives a byte-identical
# zip (and so an identical checksum) no matter when or by whom the zarr was written.
# 1980-01-01 is the earliest date the zip format can store.
_FIXED_DATE_TIME = (1980, 1, 1, 0, 0, 0)
_FILE_MODE = 0o100644  # regular file, rw-r--r--
_DIR_MODE = 0o040755  # directory, rwxr-xr-x
_MSDOS_DIR_FLAG = 0x10
_CREATE_SYSTEM_UNIX = 3
_COPY_BUFFER = 16 * 1024 * 1024


def _zip_info(arcname: str, is_dir: bool, size: int = 0) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(arcname, date_time=_FIXED_DATE_TIME)
    info.create_system = _CREATE_SYSTEM_UNIX  # ZipInfo defaults to 0 on Windows, 3 elsewhere
    if is_dir:
        info.external_attr = (_DIR_MODE << 16) | _MSDOS_DIR_FLAG
    else:
        info.external_attr = _FILE_MODE << 16
        # Stored, not deflated: zarr chunks are already compressed, so deflate costs a lot of CPU
        # on multi-GB datasets for little gain, and its output can change with the zlib build,
        # which would change the checksum (and trigger a re-upload) for unchanged data.
        info.compress_type = zipfile.ZIP_STORED
        # known up front so zipfile picks zip64 for files > 2 GiB on its own (deterministically)
        info.file_size = size
    return info


def _sorted_tree(root: Path):
    """Yield (path, relative posix name, is_dir) for `root` and everything below it, sorted.

    Follows symlinks, like `zip -r` did.
    """
    yield root, "", True
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        dirnames.sort()
        rel_dir = Path(dirpath).relative_to(root).as_posix()
        prefix = "" if rel_dir == "." else rel_dir + "/"
        # directories are yielded when os.walk descends into them, so the order is a sorted
        # depth-first walk; the files of a directory come before its subdirectories
        if prefix:
            yield Path(dirpath), prefix, True
        for name in sorted(filenames):
            yield Path(dirpath) / name, prefix + name, False


def zip_directory(src_dir: Path, zip_path: Path, arc_root: str | None = None) -> Path:
    """Write `src_dir` into `zip_path` as a deterministic zip and return `zip_path`.

    Entries are named `<arc_root>/...` (default: the name of `src_dir`, e.g. `data.zarr/...`),
    sorted, all with the same timestamp and permissions and stored uncompressed. Zipping the
    same data twice gives byte-identical files. `src_dir` is only read; the zip is written to a
    temporary file next to `zip_path` and moved into place when complete.
    """
    src_dir = Path(src_dir)
    zip_path = Path(zip_path)
    if not src_dir.is_dir():
        raise NotADirectoryError(f"not a directory: {src_dir}")
    arc_root = (arc_root or src_dir.name).strip("/")
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(prefix=zip_path.name + ".", suffix=".partial", dir=zip_path.parent)
    try:
        with os.fdopen(fd, "wb") as fh, zipfile.ZipFile(fh, "w", allowZip64=True) as zf:
            for path, rel, is_dir in _sorted_tree(src_dir):
                arcname = f"{arc_root}/{rel}" if rel else f"{arc_root}/"
                if is_dir:
                    zf.writestr(_zip_info(arcname, is_dir=True), b"")
                    continue
                with open(path, "rb") as src:
                    size = os.fstat(src.fileno()).st_size
                    with zf.open(_zip_info(arcname, is_dir=False, size=size), "w") as dst:
                        shutil.copyfileobj(src, dst, _COPY_BUFFER)
        os.chmod(tmp_name, 0o644)
        os.replace(tmp_name, zip_path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    return zip_path


def sha256_of_file(path: Path) -> str:
    """Hex sha256 of the file at `path`."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(_COPY_BUFFER), b""):
            digest.update(block)
    return digest.hexdigest()
