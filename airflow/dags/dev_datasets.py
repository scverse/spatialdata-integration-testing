from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from spatialdata_data_converter.config import get_airflow_default_args, get_cli_command

default_args = get_airflow_default_args()

dag = DAG(
    'update_dev_datasets',
    default_args=default_args,
    description='Regenerate dev datasets',
    schedule=None,
    catchup=False
)

update_dev_datasets = BashOperator(
    task_id='update_dev_datasets',
    bash_command=get_cli_command('update-dev-datasets'),
    dag=dag,
    retries=0,
)

globals()['update_dev_datasets'] = update_dev_datasets
globals()['update_dev_datasets_dag'] = dag

# --------- download spatialdata-io datasets ---------
# These are the datasets used in spatialdata-io CI tests
# (from .github/workflows/prepare_test_data.yaml)
download_spatialdata_io_datasets_dag = DAG(
    'download_spatialdata_io_datasets',
    default_args=default_args,
    description='Download spatialdata-io dev/test datasets',
    schedule=None,
    catchup=False
)

download_spatialdata_io_datasets = BashOperator(
    task_id='download_spatialdata_io_datasets',
    bash_command=get_cli_command('download-spatialdata-io-dev-datasets'),
    dag=download_spatialdata_io_datasets_dag,
    retries=0,
)

globals()['download_spatialdata_io_datasets_dag'] = download_spatialdata_io_datasets_dag