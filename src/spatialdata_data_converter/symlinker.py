# create symlinks and download data for the xenium_visium notebooks
import os
from spatialdata_data_converter.subprocess_runner import run_subprocess
import spatialdata_data_converter.config as sdcc
from pathlib import Path

R = Path(sdcc.Config.REPOSITORIES_FOLDER)


def create_symlink(src, dst):
    # check if dst does not already exist
    src = str(src)
    dst = str(dst)
    if os.path.lexists(dst):
        print(f"Symlink: {dst} already exists, removing it.")
        os.remove(dst)
    # create the symbolic link
    os.symlink(src, dst)
    print(f"Symlink created at {dst} pointing to {src}.")


def xenium_visium_make_symlinks():
    create_symlink(
        R / "spatialdata-sandbox",
        R / "spatialdata-notebooks/notebooks/paper_reproducibility/spatialdata-sandbox",
    )

    # download data needed for the xenium_visium notebook
    for file in [
        "BC_atlas_xe.h5ad",
        "manual_annotations.zarr.zip",
        "sandbox.zarr.zip",
        "visium_annotated_cell2location.h5ad",
        "visium_copyKat.h5ad",
    ]:
        f = (
            f"rclone -v copy embl-s3:spatialdata/spatialdata-sandbox/generated_data/xenium_visium_integration/{file} "
            + str(R / "spatialdata-sandbox/generated_data/xenium_visium_integration/")
        )
        run_subprocess(cmd=f, env=sdcc.Config.ENV, update_repos=False)
    zip_path = (
        R
        / "spatialdata-sandbox/generated_data/xenium_visium_integration/sandbox.zarr.zip"
    )
    out_path = R / "spatialdata-sandbox/generated_data/xenium_visium_integration/"
    run_subprocess(
        cmd=f'unzip -o "{zip_path}" -d "{out_path}"', env=sdcc.Config.ENV, update_repos=False
    )

def transformations_symlinks():
    create_symlink(R / 'spatialdata-sandbox/mouse_liver/data.zarr', R / 'spatialdata-notebooks/notebooks/examples/mouse_liver.zarr')


def alignment_using_landmarks_make_symlinks():
    create_symlink(
        R / "spatialdata-sandbox/xenium_rep1_io/data.zarr",
        R / "spatialdata-notebooks/notebooks/examples/xenium.zarr",
    )
    create_symlink(
        R / "spatialdata-sandbox/visium_associated_xenium_io/data.zarr",
        R / "spatialdata-notebooks/notebooks/examples/visium.zarr",
    )

def densenet_make_symlinks():
    alignment_using_landmarks_make_symlinks()


def visium_brain_make_symlinks():
    create_symlink(
        R / "spatialdata-sandbox/visium/data.zarr",
        R / "spatialdata-notebooks/notebooks/examples/visium_brain.zarr",
    )

def napari_rois_make_symlinks():
    create_symlink(
        R / "spatialdata-sandbox/visium_associated_xenium_io/data.zarr",
        R / "spatialdata-notebooks/notebooks/examples/visium.zarr",
    )


def squidpy_integration_make_symlinks():
    create_symlink(
        R / "spatialdata-sandbox/xenium_rep1_io/data.zarr",
        R / "spatialdata-notebooks/notebooks/examples/xenium.zarr",
    )


def technology_cosmx_make_symlinks():
    create_symlink(
        R / "spatialdata-sandbox/cosmx_io/data.zarr",
        R / "spatialdata-notebooks/notebooks/examples/cosmx.zarr",
    )


def technology_merfish_make_symlinks():
    create_symlink(
        R / "spatialdata-sandbox/merfish/data.zarr",
        R / "spatialdata-notebooks/notebooks/examples/merfish.zarr",
    )


def technology_mibitof_make_symlinks():
    create_symlink(
        R / "spatialdata-sandbox/mibitof/data.zarr",
        R / "spatialdata-notebooks/notebooks/examples/mibitof.zarr",
    )

def speed_up_illustration_make_symlinks():
    create_symlink(R / 'spatialdata-sandbox/visium_associated_xenium_io/data.zarr', R / 'spatialdata-notebooks/notebooks/examples/visium.zarr')

def technology_visium_hd_make_symlinks():
     create_symlink(R / 'spatialdata-sandbox/visium_hd_3.0.0_io/data.zarr', R / 'spatialdata-notebooks/notebooks/examples/visium_hd.zarr')

def technology_visium_hd_mouse_4_0_1_make_symlinks():
        create_symlink(R / 'spatialdata-sandbox/visium_hd_4.0.1_io/data.zarr', R / 'spatialdata-notebooks/notebooks/examples/visium_hd_4.0.1.zarr')

def technology_xenium_make_symlinks():
     create_symlink(R / 'spatialdata-sandbox/xenium_2.0.0_io/data.zarr', R / 'spatialdata-notebooks/notebooks/examples/xenium_2.0.0.zarr')

def technology_spacem_make_symlinks():
    create_symlink(R / 'spatialdata-sandbox/spacem_helanih3t3/data.zarr', R / 'spatialdata-notebooks/notebooks/examples/spacem_helanih3t3.zarr')

def make_symlinks(dataset: str):
    if dataset in ['transformations', 'transformations_advanced']:
        return transformations_symlinks
    elif dataset == 'densenet':
        return densenet_make_symlinks
    elif dataset == 'alignment_using_landmarks':
        return alignment_using_landmarks_make_symlinks
    elif dataset == "spatial_query":
        return visium_brain_make_symlinks
    elif dataset == "squidpy_integration":
        return squidpy_integration_make_symlinks
    elif dataset == "technology_cosmx":
        return technology_cosmx_make_symlinks
    elif dataset == "technology_merfish":
        return technology_merfish_make_symlinks
    elif dataset == "technology_mibitof":
        return technology_mibitof_make_symlinks
    elif dataset == "technology_visium":
        return visium_brain_make_symlinks
    elif dataset == 'napari_rois':
        return napari_rois_make_symlinks
    elif dataset == 'technology_visium_hd':
        return technology_visium_hd_make_symlinks
    elif dataset == 'technology_visium_hd_mouse_4.0.1':
        return technology_visium_hd_mouse_4_0_1_make_symlinks
    elif dataset == 'technology_xenium':
        return technology_xenium_make_symlinks
    elif dataset == 'technology_spacem':
        return technology_spacem_make_symlinks
    else:
        raise ValueError(f"No symlinker available for dataset = {dataset}")


def make_all_symlinks():
    for dataset in ['transformations', 'densenet', 'transformations_advanced', 'alignment_using_landmarks', "spatial_query", "napari_rois", "squidpy_integration", "technology_cosmx", "technology_merfish", "technology_mibitof", "technology_visium", 'technology_visium_hd', 'technology_visium_hd_mouse_4.0.1', 'technology_xenium', 'technology_spacem']:
        make_symlinks(dataset)()
