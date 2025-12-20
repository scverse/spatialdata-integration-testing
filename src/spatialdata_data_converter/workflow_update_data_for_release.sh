#!/bin/bash
# TODO: turn this bash script into a Python script
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/bash_parallel_lib.sh"
clear && printf '\e[3J'

# -------------------- require two version arguments --------------------
if [[ -z "$1" || -z "$2" ]]; then
    echo "Usage: $0 <spatialdata-version> <spatialdata-io-version>"
    exit 1
fi

SPATIALDATA_VERSION="$1"
SPATIALDATA_IO_VERSION="$2"

echo "Running uploader with:"
echo "  spatialdata version: $SPATIALDATA_VERSION"
echo "  spatialdata-io version:      $SPATIALDATA_IO_VERSION"
COMBINED_VERSION="${SPATIALDATA_VERSION}_${SPATIALDATA_IO_VERSION}"

RUN() {
pixi run python -m spatialdata_data_converter "$@"
}

# -------------------- initial setup --------------------
# RUN update-repos \
#   --spatialdata "tag $SPATIALDATA_VERSION" \
#   --spatialdata-io "tag $SPATIALDATA_IO_VERSION" \
#   --spatialdata-plot None \
#   --napari-spatialdata None \
#   --spatialdata-notebooks main \
#   --spatialdata-sandbox main

# -------------------- to_zarr (parallel) --------------------
# to_zarr_cmds=(
#   "RUN to-zarr --dataset visium"
#   "RUN to-zarr --dataset visium_hd_3.0.0_io"
#   "RUN to-zarr --dataset visium_associated_xenium_io"
#   "RUN to-zarr --dataset xenium_2.0.0_io"
#   "RUN to-zarr --dataset xenium_rep1_io"
#   "RUN to-zarr --dataset merfish"
#   "RUN to-zarr --dataset mibitof"
#   "RUN to-zarr --dataset mouse_liver"
#   "RUN to-zarr --dataset spacem_helanih3t3"
# )
# run_parallel "${to_zarr_cmds[@]}"


# -------------------- upload released data (for archiving) --------------------
# TODO: add the visium dataset to datasets.md
# RUN upload --dataset visium --dataset-suffix "${COMBINED_VERSION}"
# RUN upload --dataset visium_hd_3.0.0_io --dataset-suffix "${COMBINED_VERSION}"
# RUN upload --dataset visium_associated_xenium_io --dataset-suffix "${COMBINED_VERSION}"
# RUN upload --dataset xenium_2.0.0_io --dataset-suffix "${COMBINED_VERSION}"
# RUN upload --dataset xenium_rep1_io --dataset-suffix "${COMBINED_VERSION}"
# RUN upload --dataset merfish --dataset-suffix "${COMBINED_VERSION}"
# RUN upload --dataset mibitof --dataset-suffix "${COMBINED_VERSION}"
# RUN upload --dataset mouse_liver --dataset-suffix "${COMBINED_VERSION}"
# RUN upload --dataset spacem_helanih3t3 --dataset-suffix "${COMBINED_VERSION}"

# uploading the datasets twice, probably we can do better
# -------------------- upload released data (ready to download) --------------------
upload_cmds=(
  "RUN upload --dataset visium"
  "RUN upload --dataset visium_hd_3.0.0_io"
  "RUN upload --dataset visium_associated_xenium_io"
  "RUN upload --dataset xenium_2.0.0_io"
  "RUN upload --dataset xenium_rep1_io"
  "RUN upload --dataset merfish"
  "RUN upload --dataset mibitof"
  "RUN upload --dataset mouse_liver"
  "RUN upload --dataset spacem_helanih3t3"
)
run_parallel "${upload_cmds[@]}"
