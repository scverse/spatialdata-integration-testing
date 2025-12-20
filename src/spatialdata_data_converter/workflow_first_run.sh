set -e
clear && printf '\e[3J'

# -------------------- initial setup --------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

RUN() {
pixi run python -m spatialdata_data_converter "$@"
}

RUN update-repos \
  --spatialdata main \
  --spatialdata-io main \
  --spatialdata-plot main \
  --napari-spatialdata main \
  --spatialdata-notebooks main \
  --spatialdata-sandbox main

# bash "$SCRIPT_DIR/commands/install_env.sh"
# -------------------- download --------------------
# RUN download --dataset merfish

# -------------------- tests --------------------
# RUN run-tests --repo spatialdata
# RUN run-tests --repo spatialdata-io
# if [[ "$OSTYPE" == "linux-gnu"* ]]; then
#     python -m spatialdata_data_converter run-tests --repo spatialdata-plot
#     export QT_QPA_PLATFORM=offscreen  # to avoid errors in ubuntu
# fi
# if xvfb-run was available, we could run the tests without "offscreen"
# RUN run-tests --repo napari-spatialdata

# -------------------- to_zarr other techs --------------------
# RUN to-zarr --dataset merfish

# -------------------- symlinks setup --------------------
# RUN create-symlinks

# -------------------- notebooks --------------------
# RUN run-docs-notebook --notebook technology_merfish
# RUN run-docs-notebook --notebook transformations