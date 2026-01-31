from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from spatialdata_data_converter.config import get_airflow_default_args, get_cli_command

default_args = get_airflow_default_args()
TEST_REPOS = ["spatialdata", "spatialdata-plot", "spatialdata-io", "napari-spatialdata"]

for repo in TEST_REPOS:
    # --------- run tests for a single repository ---------

    dag_id = f'tests_{repo}'

    dag = DAG(
        dag_id,
        default_args=default_args,
        description=f'Run tests {repo}',
        schedule=None,
        catchup=False
    )

    tests_repo = BashOperator(
        task_id=f'tests_{repo}',
        bash_command=get_cli_command(f'run-tests --repo {repo}'),
        dag=dag,
    )

    globals()[f'tests_{repo}'] = tests_repo

    # Assign the dag object to a variable that complies with Airflow's naming conventions
    globals()[dag_id] = dag

# --------- run tests for all repos ---------

tests_all = DAG(
    'tests_all',
    default_args=default_args,
    description='Trigger all pytest tasks',
    schedule=None,
    catchup=False
)

for repo in TEST_REPOS:
    trigger = TriggerDagRunOperator(
        task_id=f'trigger_tests_{repo}_from_tests_all',
        trigger_dag_id=f'tests_{repo}',
        wait_for_completion=True,
        dag=tests_all,
    )