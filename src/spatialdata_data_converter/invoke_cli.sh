set -e
clear && printf '\e[3J'
# # -------------------- initial setup --------------------
RUN() {
pixi run python -m spatialdata_data_converter "$@"
}
# replaced the python command with a bash one
# RUN install-env
# SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# bash "$SCRIPT_DIR/commands/install_env.sh"
# RUN update-repos \
#   --spatialdata main \
#   --spatialdata-io main \
# #   --spatialdata "pr 968" \
# #   --spatialdata-io None \
#   --spatialdata-plot main \
#   --napari-spatialdata main \
#   --spatialdata-notebooks main \
#   --spatialdata-sandbox main
#
# # -------------------- download --------------------
# datasets from spatialdata-sandbox appearing in the docs
# RUN download --dataset merfish
# RUN download --dataset mibitof
# RUN download --dataset mouse_liver
# RUN download --dataset spacem_helanih3t3
# RUN download --dataset visium
# RUN download --dataset visium_associated_xenium_io
# RUN download --dataset xenium_rep1_io
#
# # skipped: Reason: requires manual data download (skipping it), or skipped workflow
# # RUN download --dataset cosmx_io
# # RUN download --dataset steinbock_io
# # RUN download --dataset xenium_rep2_io
#
# visium datasets
# RUN download --dataset visium_1.0.0_io
# RUN download --dataset visium_1.1.0_io
# RUN download --dataset visium_1.2.0_io
# RUN download --dataset visium_1.3.0_io
# RUN download --dataset visium_2.0.0_1_io
# RUN download --dataset visium_2.0.0_2_io
# RUN download --dataset visium_2.0.1_io
# RUN download --dataset visium_2.1.0_1_io
# RUN download --dataset visium_2.1.0_2_io
#
# visium hd datasets
# RUN download --dataset visium_hd_3.0.0_io
# RUN download --dataset visium_hd_3.1.1_io
#
# xenium datasets
# RUN download --dataset xenium_1.0.2_io
# RUN download --dataset xenium_1.3.0_io
# RUN download --dataset xenium_1.4.0_io
# RUN download --dataset xenium_1.5.0_io
# RUN download --dataset xenium_1.6.0_io
# RUN download --dataset xenium_1.7.0_io
# RUN download --dataset xenium_2.0.0_io
# RUN download --dataset xenium_3.0.0_io
#
# # -------------------- tests --------------------
# RUN run-tests --repo spatialdata
# RUN run-tests --repo spatialdata-io
# if [[ "$OSTYPE" == "linux-gnu"* ]]; then
#     RUN run-tests --repo spatialdata-plot
#     export QT_QPA_PLATFORM=offscreen  # to avoid errors in ubuntu
# fi
# if xvfb-run was available, we could run the tests without "offscreen"
# RUN run-tests --repo napari-spatialdata

# skipped: made explicit in the to-zarr scripts
# RUN run-tests --repo spatialdata-sandbox --test-path test_to_zarr_visium.py

# -------------------- to_zarr other techs --------------------
# RUN to-zarr --dataset merfish
# RUN to-zarr --dataset mibitof
# RUN to-zarr --dataset mouse_liver
# RUN to-zarr --dataset spacem_helanih3t3
# RUN to-zarr --dataset visium
# RUN to-zarr --dataset visium_associated_xenium_io
# RUN to-zarr --dataset xenium_rep1_io

# -------------------- to_zarr visium --------------------
# RUN to-zarr --dataset visium_1.0.0_io
# RUN to-zarr --dataset visium_1.1.0_io
# RUN to-zarr --dataset visium_1.2.0_io
# RUN to-zarr --dataset visium_1.3.0_io
# RUN to-zarr --dataset visium_2.0.0_1_io
# RUN to-zarr --dataset visium_2.0.0_2_io
# RUN to-zarr --dataset visium_2.0.1_io
# RUN to-zarr --dataset visium_2.1.0_1_io
# RUN to-zarr --dataset visium_2.1.0_2_io

# -------------------- to_zarr visium hd --------------------
# RUN to-zarr --dataset visium_hd_3.0.0_io
# RUN to-zarr --dataset visium_hd_3.1.1_io

# -------------------- to_zarr xenium --------------------
# RUN to-zarr --dataset xenium_1.0.2_io
# RUN to-zarr --dataset xenium_1.3.0_io
# RUN to-zarr --dataset xenium_1.4.0_io
# RUN to-zarr --dataset xenium_1.5.0_io
# RUN to-zarr --dataset xenium_1.6.0_io
# RUN to-zarr --dataset xenium_1.7.0_io
# RUN to-zarr --dataset xenium_2.0.0_io
# RUN to-zarr --dataset xenium_3.0.0_io

# does not require data download
# RUN to-zarr --dataset toy

# skipped. Reason: requires manual data download (skipping it)
# RUN to-zarr --dataset cosmx_io
# RUN to-zarr --dataset mcmicro_io

# skipped. Reason: require fixes and it's not used a lot
# RUN to-zarr --dataset steinbock_io

# skipped: redundant
# RUN to-zarr --dataset xenium_rep2_io
# RUN to-zarr --dataset visium_associated_xenium_io

# # -------------------- symlinks setup --------------------
# RUN create-symlinks
#
# -------------------- notebooks --------------------
# RUN run-docs-notebook --notebook aggregation
# RUN run-docs-notebook --notebook alignment_using_landmarks
# RUN run-docs-notebook --notebook intro
# RUN run-docs-notebook --notebook labels_shapes_interchangeability
# RUN run-docs-notebook --notebook models1
# RUN run-docs-notebook --notebook models2
# RUN run-docs-notebook --notebook napari_rois
# RUN run-docs-notebook --notebook sdata_from_scratch
# RUN run-docs-notebook --notebook spatial_query
# RUN run-docs-notebook --notebook squidpy_integration
# RUN run-docs-notebook --notebook tables
# RUN run-docs-notebook --notebook technology_merfish
# RUN run-docs-notebook --notebook technology_mibitof
# RUN run-docs-notebook --notebook technology_spacem
# RUN run-docs-notebook --notebook technology_visium_hd
# RUN run-docs-notebook --notebook technology_visium
# RUN run-docs-notebook --notebook technology_xenium
# RUN run-docs-notebook --notebook transformations_advanced
# RUN run-docs-notebook --notebook transformations
# RUN run-docs-notebook --notebook densenet

# skipped notebooks (requires manual/laborious data download/setup; or it's too slow)
# RUN run-docs-notebook --notebook technology_cosmx
# RUN run-docs-notebook --notebook speed_up_illustration

# skipped notebooks: data is not public
# RUN run-docs-notebook --notebook technology_curio
# RUN run-docs-notebook --notebook technology_stereoseq

# -------------------- dev datasets --------------------
# RUN update-dev-datasets

# -------------------- paper datasets --------------------
# skipped: heavy to run and they are not linked in the docs

# -------------------- upload dev data --------------------
# RUN upload --dataset visium --dataset-suffix _dev
# RUN upload --dataset visium_hd_3.0.0_io --dataset-suffix _dev
# RUN upload --dataset visium_associated_xenium_io --dataset-suffix _dev
# RUN upload --dataset xenium_2.0.0_io --dataset-suffix _dev
# RUN upload --dataset xenium_rep1_io --dataset-suffix _dev
# RUN upload --dataset merfish --dataset-suffix _dev
# RUN upload --dataset mibitof --dataset-suffix _dev
# RUN upload --dataset mouse_liver --dataset-suffix _dev
# RUN upload --dataset spacem_helanih3t3 --dataset-suffix _dev
