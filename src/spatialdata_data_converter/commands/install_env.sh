#!/bin/bash                                                                                                                             

# these values are defined in config.py and passed here as environment variables
# source "${BASHRC}"
# source "${CONDA_SH}"
#!/bin/bash

set -e

# 1. Get the path of this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 2. Go three folders up
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../" && pwd)"

# 3. Look for envvars.sh two folders up and source it
ENVVARS_FILE="$ROOT_DIR/envvars.sh"

if [[ ! -f "$ENVVARS_FILE" ]]; then
    echo "ERROR: envvars.sh not found at $ENVVARS_FILE"
    exit 1
fi

# shellcheck source=/dev/null
source "$ENVVARS_FILE"

# 4. Check that BASHRC and CONDA_SH are set
if [[ -z "${BASHRC:-}" ]]; then
    echo "ERROR: BASHRC environment variable is not set in envvars.sh"
    exit 1
fi

if [[ -z "${CONDA_SH:-}" ]]; then
    echo "ERROR: CONDA_SH environment variable is not set in envvars.sh"
    exit 1
fi

echo "envvars.sh loaded successfully."
echo "BASHRC: $BASHRC"
echo "CONDA_SH: $CONDA_SH"

set +e
echo "sourcing BASHRC"
source "$BASHRC"

echo "sourcing CONDA_SH"
source "$CONDA_SH"
set -e

ENV=ome_sdc

# option 1 (only for debug)
# conda activate $ENV

# option 2 (default)
echo "-------- remove old env --------"
if [[ "$CONDA_DEFAULT_ENV" == "$ENV" ]]; then
    conda deactivate
fi
# only if it exists: on a fresh setup there is no env yet, and `remove` would fail (set -e)
if conda env list | awk '{print $1}' | grep -qx "$ENV"; then
    conda remove -n $ENV --all -y
fi

echo "-------- create new env --------"
mamba create -n $ENV -c conda-forge python==3.13 -y
# conda init
conda activate
conda activate $ENV

# echo "-------- installing supporting libraries --------"
# TODO: ideally we won't need all these packages. They should either be dependencies of spatialdata-data-converter or add as extras when installing the (napari-)spatialdata(-io|-plot) packages
# fontconfig is a requirement of vispy when running pytest
# no conda-forge `pyqt` here: it is PyQt5 (Qt 5.15), but napari>=0.10 needs Qt>=6.7, and qtpy would pick PyQt5
# over a Qt6 binding; napari[pyqt6] (pip, below) provides the Qt binding instead
mamba install pytorch torchvision torchaudio cpuonly rclone joblib -c pytorch -c conda-forge -y
mamba install -c conda-forge nbconvert pytest pytest-xdist jupyter ipywidgets jupyterlab chardet unzip papermill watermark python-igraph leidenalg rclone pytorch-lightning monai fontconfig -y
pip install jupyter-black watermark

echo "-------- installing spatialdata and related libraries --------"
# 1. Find the absolute path of the .sh file being run
SCRIPT_PATH="$(readlink -f "$0")"

# 2. Find the folder 3 folders up (../../../), so we need to call dirname 4 times
PACKAGE_PATH="$(dirname "$(dirname "$(dirname "$(dirname "$SCRIPT_PATH")")")")"

# 3. Print these 2 paths
echo "Script path: $SCRIPT_PATH"
echo "Path of the spatialdata-data-converter package: $PACKAGE_PATH"

# # 4. Use the absolute path in pip install commands
# install spatialdata first so other packages use local version instead of PyPI
# same default as Config.REPOSITORIES_FOLDER in config.py (SDC_WORKSPACE may come from envvars.sh)
WORKSPACE="${SDC_WORKSPACE:-$PACKAGE_PATH/dependencies}"
WORKSPACE="${WORKSPACE/#\~/$HOME}"
[[ "$WORKSPACE" = /* ]] || WORKSPACE="$PACKAGE_PATH/$WORKSPACE"
echo "Repositories (workspace): $WORKSPACE"

PACKAGES=(
    -e "$WORKSPACE/spatialdata" --group "$WORKSPACE/spatialdata/pyproject.toml:test"
    -e "$WORKSPACE/spatialdata-io" --group "$WORKSPACE/spatialdata-io/pyproject.toml:test"
    -e "$WORKSPACE/spatialdata-plot" --group "$WORKSPACE/spatialdata-plot/pyproject.toml:test"
    -e "$WORKSPACE/squidpy" --group "$WORKSPACE/squidpy/pyproject.toml:test"
    -e "$WORKSPACE/napari-spatialdata[test]"  # still a setup.cfg extra, not a dependency group
    "napari[pyqt6]"  # Qt binding for napari(-spatialdata) tests; napari pins compatible PyQt6/Qt versions
)
# one call: a conflict with the local spatialdata fails instead of silently pulling it from PyPI
set -o pipefail
{ pip install "${PACKAGES[@]}" 2>&1 1>&3 | awk '{print > "/dev/stderr"} /does not provide the extra/ {bad=1} END {exit bad}'; } 3>&1  # fail if pip warns about a missing extra (stderr only)
echo "success!"
