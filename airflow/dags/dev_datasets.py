from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from spatialdata_data_converter.config import get_airflow_default_args, get_cli_command

default_args = get_airflow_default_args()

dag = DAG(
    'update_dev_datasets',
    default_args=default_args,
    description='Regenerate dev datasets',
    schedule='0 0 * * *',  # Every day at midnight
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