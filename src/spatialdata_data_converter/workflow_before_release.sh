#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/bash_parallel_lib.sh"
clear && printf '\e[3J'

# -------------------- initial setup --------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# bash "$SCRIPT_DIR/commands/install_env.sh"

# pixi run python -m spatialdata_data_converter "$@" update-repos \
#   --spatialdata None \
#   --spatialdata-io None \
#   --spatialdata-plot None \
#   --napari-spatialdata None \
#   --spatialdata-notebooks None \
#   --spatialdata-sandbox None


# -------------------- tests (parallel) --------------------
test_cmds=(
  "pixi run python -m spatialdata_data_converter "$@" run-tests --repo spatialdata"
  "pixi run python -m spatialdata_data_converter "$@" run-tests --repo spatialdata-io"
  "if [[ \"\$OSTYPE\" == \"linux-gnu\"* ]]; then pixi run python -m spatialdata_data_converter "$@" run-tests --repo spatialdata-plot; fi"
  "if [[ \"\$OSTYPE\" == \"linux-gnu\"* ]]; then export QT_QPA_PLATFORM=offscreen && pixi run python -m spatialdata_data_converter "$@" run-tests --repo napari-spatialdata; fi"
  "if [[ \"\$OSTYPE\" != \"linux-gnu\"* ]]; then pixi run python -m spatialdata_data_converter "$@" run-tests --repo napari-spatialdata; fi"
)
run_parallel "${test_cmds[@]}"

# -------------------- to_zarr (parallel) --------------------
to_zarr_cmds=(
  "pixi run python -m spatialdata_data_converter "$@" to-zarr --dataset merfish"
  "pixi run python -m spatialdata_data_converter "$@" to-zarr --dataset mibitof"
  "pixi run python -m spatialdata_data_converter "$@" to-zarr --dataset mouse_liver"
  "pixi run python -m spatialdata_data_converter "$@" to-zarr --dataset spacem_helanih3t3"
  "pixi run python -m spatialdata_data_converter "$@" to-zarr --dataset visium"
  "pixi run python -m spatialdata_data_converter "$@" to-zarr --dataset visium_associated_xenium_io"
  "pixi run python -m spatialdata_data_converter "$@" to-zarr --dataset xenium_rep1_io"
  "pixi run python -m spatialdata_data_converter "$@" to-zarr --dataset visium_2.1.0_2_io"
  "pixi run python -m spatialdata_data_converter "$@" to-zarr --dataset visium_hd_3.1.1_io"
  "pixi run python -m spatialdata_data_converter "$@" to-zarr --dataset xenium_2.0.0_io"
  "pixi run python -m spatialdata_data_converter "$@" to-zarr --dataset xenium_3.0.0_io"
  "pixi run python -m spatialdata_data_converter "$@" to-zarr --dataset toy"
)
# run_parallel "${to_zarr_cmds[@]}" --no-parallel

# -------------------- symlinks setup --------------------
# pixi run python -m spatialdata_data_converter "$@" create-symlinks

# -------------------- notebooks (parallel) --------------------
notebook_names=(
  aggregation
  alignment_using_landmarks
  intro
  labels_shapes_interchangeability
  models1
  models2
  napari_rois
  sdata_from_scratch
  spatial_query
  squidpy_integration
  tables
  technology_merfish
  technology_mibitof
  technology_spacem
  technology_visium_hd
  technology_visium
  technology_xenium
  transformations_advanced
  transformations
  densenet
)
notebook_cmds=()
for n in "${notebook_names[@]}"; do
  notebook_cmds+=( "pixi run python -m spatialdata_data_converter "$@" run-docs-notebook --notebook $n" )
done
# run_parallel "${notebook_cmds[@]}" --no-parallel

# heavy notebook, better to run it alone otherwise it can give a "too many open files" error
# pixi run python -m spatialdata_data_converter "$@" run-docs-notebook --notebook densenet
