#!/bin/bash
# Upload converted datasets to S3 right before a release.
#
# Usage:
#   bash workflow_update_data_for_release.sh <spatialdata-version> <spatialdata-io-version>
#
# This script should be run manually right before a release, once the test
# workflow (either via Airflow or manually) has passed successfully.
#
# Note: after the upload completes successfully, manually add the new version entry
# in dependencies/spatialdata-notebooks/datasets/README.md so that the download
# link appears in the docs.
#
# Parallelization: by default the upload runs sequentially. To run in parallel,
# comment out the sequential section and uncomment the parallel section below.
#
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
COMBINED_VERSION="_spatialdata_${SPATIALDATA_VERSION}_spatialdata_io_${SPATIALDATA_IO_VERSION}"

RUN() {
pixi run python -m spatialdata_data_converter "$@"
}

# "initial setup" and "to_zarr" should be commented if the release is not made, and should
# be uncommented if you already made a release, or if you want to upload the data for an old release

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
#   "RUN to-zarr --dataset merfish"
#   "RUN to-zarr --dataset mibitof"
#   "RUN to-zarr --dataset mouse_liver"
#   "RUN to-zarr --dataset spacem_helanih3t3"
#   "RUN to-zarr --dataset visium_associated_xenium_io"
#   "RUN to-zarr --dataset visium_hd_3.0.0_io"
#   "RUN to-zarr --dataset visium_hd_4.0.1_io"
#   "RUN to-zarr --dataset xenium_2.0.0_io"
#   "RUN to-zarr --dataset xenium_rep1_io"
# )
# run_parallel "${to_zarr_cmds[@]}"


# -------------------- upload released data (for archiving, sequential) --------------------
# To run in parallel instead, comment out this section and uncomment the parallel section below.
RUN upload --dataset visium --dataset-suffix "${COMBINED_VERSION}"
RUN upload --dataset merfish --dataset-suffix "${COMBINED_VERSION}"
RUN upload --dataset mibitof --dataset-suffix "${COMBINED_VERSION}"
RUN upload --dataset mouse_liver --dataset-suffix "${COMBINED_VERSION}"
RUN upload --dataset spacem_helanih3t3 --dataset-suffix "${COMBINED_VERSION}"
RUN upload --dataset visium_associated_xenium_io --dataset-suffix "${COMBINED_VERSION}"
RUN upload --dataset visium_hd_3.0.0_io --dataset-suffix "${COMBINED_VERSION}"
RUN upload --dataset visium_hd_4.0.1_io --dataset-suffix "${COMBINED_VERSION}"
RUN upload --dataset xenium_2.0.0_io --dataset-suffix "${COMBINED_VERSION}"
RUN upload --dataset xenium_rep1_io --dataset-suffix "${COMBINED_VERSION}"

# -------------------- upload released data (for archiving, parallel) --------------------
# Uncomment this section and comment out the sequential section above to run in parallel.
# upload_cmds=(
#   "RUN upload --dataset visium --dataset-suffix ${COMBINED_VERSION}"
#   "RUN upload --dataset merfish --dataset-suffix ${COMBINED_VERSION}"
#   "RUN upload --dataset mibitof --dataset-suffix ${COMBINED_VERSION}"
#   "RUN upload --dataset mouse_liver --dataset-suffix ${COMBINED_VERSION}"
#   "RUN upload --dataset spacem_helanih3t3 --dataset-suffix ${COMBINED_VERSION}"
#   "RUN upload --dataset visium_associated_xenium_io --dataset-suffix ${COMBINED_VERSION}"
#   "RUN upload --dataset visium_hd_3.0.0_io --dataset-suffix ${COMBINED_VERSION}"
#   "RUN upload --dataset visium_hd_4.0.1_io --dataset-suffix ${COMBINED_VERSION}"
#   "RUN upload --dataset xenium_2.0.0_io --dataset-suffix ${COMBINED_VERSION}"
#   "RUN upload --dataset xenium_rep1_io --dataset-suffix ${COMBINED_VERSION}"
# )
# run_parallel "${upload_cmds[@]}"
