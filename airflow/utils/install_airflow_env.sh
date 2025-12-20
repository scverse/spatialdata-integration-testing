source ~/.bashrc
set -e
conda remove -n airflow --all -y
mamba create -c conda-forge -n airflow python==3.10 airflow firefox selenium geckodriver rclone unzip flask-appbuilder -y
