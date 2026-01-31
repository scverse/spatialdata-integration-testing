from airflow import DAG
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from spatialdata_data_converter.config import get_airflow_default_args

default_args = get_airflow_default_args()

# --------- First Run Orchestrator ---------
# Executes the initial setup sequence:
# 1. config_update_repos
# 2. config_create_symlinks
# 3. config_install_env
# 4. download_all
orchestrator_first_run = DAG(
    '0_orchestrator_first_run',
    default_args=default_args,
    description='First run: setup repos, symlinks, env, then download all data',
    schedule=None,
    catchup=False
)

first_run_update_repos = TriggerDagRunOperator(
    task_id='trigger_config_update_repos',
    trigger_dag_id='config_update_repos',
    wait_for_completion=True,
    dag=orchestrator_first_run,
)

first_run_create_symlinks = TriggerDagRunOperator(
    task_id='trigger_config_create_symlinks',
    trigger_dag_id='config_create_symlinks',
    wait_for_completion=True,
    dag=orchestrator_first_run,
)

first_run_install_env = TriggerDagRunOperator(
    task_id='trigger_config_install_env',
    trigger_dag_id='config_install_env',
    wait_for_completion=True,
    dag=orchestrator_first_run,
)

first_run_download_all = TriggerDagRunOperator(
    task_id='trigger_download_all',
    trigger_dag_id='download_all',
    wait_for_completion=True,
    dag=orchestrator_first_run,
)

first_run_update_repos >> first_run_create_symlinks >> first_run_install_env >> first_run_download_all

# --------- Test Workflow Orchestrator ---------
# Executes the testing workflow sequence:
# 1. config_update_repos (ensure repos are up-to-date)
# 2. config_install_env (ensure environment is current)
# 3. tests_all
# 4. to_zarr_all
# 5. notebook_docs_all
orchestrator_test_workflow = DAG(
    '0_orchestrator_test_workflow',
    default_args=default_args,
    description='Test workflow: update repos, env, run tests, convert to zarr, run notebooks',
    schedule='0 0 * * *',  # Every day at midnight
    catchup=False
)

test_workflow_update_repos = TriggerDagRunOperator(
    task_id='trigger_config_update_repos',
    trigger_dag_id='config_update_repos',
    wait_for_completion=True,
    dag=orchestrator_test_workflow,
)

test_workflow_install_env = TriggerDagRunOperator(
    task_id='trigger_config_install_env',
    trigger_dag_id='config_install_env',
    wait_for_completion=True,
    dag=orchestrator_test_workflow,
)

test_workflow_tests_all = TriggerDagRunOperator(
    task_id='trigger_tests_all',
    trigger_dag_id='tests_all',
    wait_for_completion=True,
    dag=orchestrator_test_workflow,
)

test_workflow_to_zarr_all = TriggerDagRunOperator(
    task_id='trigger_to_zarr_all',
    trigger_dag_id='to_zarr_all',
    wait_for_completion=True,
    dag=orchestrator_test_workflow,
)

test_workflow_notebook_docs_all = TriggerDagRunOperator(
    task_id='trigger_notebook_docs_all',
    trigger_dag_id='notebook_docs_all',
    wait_for_completion=True,
    dag=orchestrator_test_workflow,
)

test_workflow_update_repos >> test_workflow_install_env >> test_workflow_tests_all >> test_workflow_to_zarr_all >> test_workflow_notebook_docs_all
