from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from spatialdata_data_converter.config import Config, get_airflow_default_args, get_cli_command

default_args = get_airflow_default_args()

# List of datasets
for dataset in Config.DATASETS:
    # --------- download a single dataset ---------
    if dataset not in Config.DATASETS_NO_DOWNLOAD:
        dag_id = f'download_{dataset}'

        dag = DAG(
            dag_id,
            default_args=default_args,
            description=f'Download data for {dataset}',
            schedule=None,
            catchup=False
        )

        run_download_script = BashOperator(
            task_id=f'run_download_script_{dataset}',
            bash_command=get_cli_command(f'download --dataset {dataset}'),
            dag=dag,
            retries=0,
        )

        # Assign the dag object to a variable that complies with Airflow's naming conventions
        globals()[dag_id] = dag

    # --------- convert a single dataset to zarr ---------
    dag_id = f'to_zarr_{dataset}'

    dag = DAG(
        dag_id,
        default_args=default_args,
        description=f'Convert data for {dataset} to zarr',
        schedule=None,
        catchup=False
    )

    run_to_zarr_script = BashOperator(
        task_id=f'run_to_zarr_script_{dataset}',
        bash_command=get_cli_command(f'to-zarr --dataset {dataset}'),
        dag=dag,
        retries=0,
    )

    # Assign the dag object to a variable that complies with Airflow's naming conventions
    globals()[dag_id] = dag

    if dataset not in Config.DATASETS_NO_DOWNLOAD:
        trigger_to_zarr_dag = TriggerDagRunOperator(
            task_id=f'trigger_to_zarr_{dataset}_from_download_{dataset}',
            trigger_dag_id=f'to_zarr_{dataset}',
            dag=globals()[f'download_{dataset}'],
        )
        run_download_script >> trigger_to_zarr_dag

    # --------- upload a single dataset to s3 ---------
    dag_id = f'upload_{dataset}'

    dag = DAG(
        dag_id,
        default_args=default_args,
        description=f'Upload data for {dataset}',
        schedule=None,
        catchup=False
    )

    run_upload_script = BashOperator(
        task_id=f'run_upload_script_{dataset}',
        bash_command=get_cli_command(f'upload --dataset {dataset}'),
        dag=dag,
        retries=0,
    )

    # Assign the dag object to a variable that complies with Airflow's naming conventions
    globals()[dag_id] = dag

    trigger_upload_dag = TriggerDagRunOperator(
        task_id=f'trigger_upload_{dataset}_from_to_zarr_{dataset}',
        trigger_dag_id=f'upload_{dataset}',
        dag=globals()[f'to_zarr_{dataset}'],
    )
    run_to_zarr_script >> trigger_upload_dag

# --------- download all datasets ---------
# Creation of a 'download_all' DAG that triggers all 'download_{dataset}' DAGs
download_all = DAG(
    'download_all',
    default_args=default_args,
    description='Trigger all the download tasks',
    schedule='0 12 * * SUN',
    # schedule_interval=None,
    catchup=False
)
for dataset in Config.DATASETS:
    if dataset not in Config.DATASETS_NO_DOWNLOAD:
        trigger = TriggerDagRunOperator(
            task_id=f'trigger_download_{dataset}_from_download_all',
            trigger_dag_id=f'download_{dataset}',
            dag=download_all,
        )

# Also trigger spatialdata-io datasets download
trigger_spatialdata_io_datasets = TriggerDagRunOperator(
    task_id='trigger_download_spatialdata_io_datasets_from_download_all',
    trigger_dag_id='download_spatialdata_io_datasets',
    dag=download_all,
)

# --------- convert all datasets to zarr ---------
# Creation of a 'to_zarr_all' DAG that triggers all 'to_zarr_{dataset}' DAGs and is scheduled to run daily
to_zarr_all = DAG(
    'to_zarr_all',
    default_args=default_args,
    description='Trigger all the to_zarr tasks',
    schedule='@daily',
    catchup=False
)
for dataset in Config.DATASETS:
    trigger = TriggerDagRunOperator(
        task_id=f'trigger_to_zarr_{dataset}_from_to_zarr_all',
        trigger_dag_id=f'to_zarr_{dataset}',
        dag=to_zarr_all,
    )

# # --------- upload all datasets to s3 ---------
# disabled because we don't really use it and each dataset uploader is triggered by the respective to_zarr anyway
# upload_all = DAG(
#     'upload_all',
#     default_args=default_args,
#     description='Trigger all the upload tasks',
#     schedule=None,
#     catchup=False
# )
# for dataset in Config.DATASETS:
#     trigger = TriggerDagRunOperator(
#         task_id=f'trigger_upload_{dataset}_from_upload_all',
#         trigger_dag_id=f'upload_{dataset}',
#         dag=upload_all,
#     )