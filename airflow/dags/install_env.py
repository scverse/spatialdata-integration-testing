from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from spatialdata_data_converter.config import get_airflow_default_args, get_cli_command

default_args = get_airflow_default_args()

dag = DAG(
    'config_install_env',
    default_args=default_args,
    description='Install the environment for the project',
    schedule='0 11 * * MON',
    catchup=False
)

run_shell_script = BashOperator(
    task_id='run_install_env_script',
    bash_command=get_cli_command('install-env'),
    dag=dag,
    retries=0,
)

# --------- update repos DAG ---------
dag_update_repos = DAG(
    'config_update_repos',
    default_args=default_args,
    description='Update all repositories to configured branches',
    schedule=None,
    catchup=False
)

update_repos_task = BashOperator(
    task_id='update_repos',
    bash_command=get_cli_command('update-repos'),
    dag=dag_update_repos,
    retries=0,
)

# --------- create symlinks DAG ---------
dag_create_symlinks = DAG(
    'config_create_symlinks',
    default_args=default_args,
    description='Create symlinks between sandbox datasets and notebooks',
    schedule=None,
    catchup=False
)

create_symlinks_task = BashOperator(
    task_id='create_symlinks',
    bash_command=get_cli_command('create-symlinks'),
    dag=dag_create_symlinks,
    retries=0,
)