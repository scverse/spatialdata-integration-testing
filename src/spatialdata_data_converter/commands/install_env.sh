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
conda remove -n $ENV --all -y

echo "-------- create new env --------"
mamba create -n $ENV -c conda-forge python==3.13 -y
# conda init
conda activate
conda activate $ENV

# echo "-------- installing supporting libraries --------"
# TODO: ideally we won't need all these packages. They should either be dependencies of spatialdata-data-converter or add as extras when installing the (napari-)spatialdata(-io|-plot) packages
# fontconfig is a requirement of vispy when running pytest
mamba install pytorch torchvision torchaudio cpuonly rclone joblib -c pytorch -c conda-forge -y
mamba install -c conda-forge nbconvert pytest jupyter ipywidgets jupyterlab chardet unzip papermill watermark python-igraph leidenalg rclone pytorch-lightning monai pyqt fontconfig -y
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
pip install -e "$PACKAGE_PATH/dependencies/spatialdata[test,docs]"
pip install -e "$PACKAGE_PATH/dependencies/spatialdata-io[test,doc]"
pip install -e "$PACKAGE_PATH/dependencies/spatialdata-plot[test]"
pip install -e "$PACKAGE_PATH/dependencies/napari-spatialdata[test]"
pip install -e "$PACKAGE_PATH/dependencies/squidpy[test]"
# pip install squidpy
echo "success!"
