from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import Param
from spatialdata_data_converter.config import Config, branch_envvar, get_airflow_default_args, get_cli_command

default_args = get_airflow_default_args()

dag = DAG(
    'config_install_env',
    default_args=default_args,
    description='Install the environment for the project',
    schedule=None,
    catchup=False
)

run_shell_script = BashOperator(
    task_id='run_install_env_script',
    bash_command=get_cli_command('install-env'),
    dag=dag,
    retries=0,
)

# --------- update repos DAG ---------
# Per-run branch overrides ("Trigger DAG w/ config"); empty = use Config.REPOSITORIES.
# Same syntax as Config.REPOSITORIES: 'main', 'branch-name', 'pr 329', 'tag v0.4.0', 'None' (latest release).
REPOSITORY_PARAMS = {
    repo: Param(
        None,
        type=["null", "string"],  # nullable, so the trigger form doesn't mark it required
        description=f"Branch / 'pr <n>' / 'tag <t>' / 'None' for {repo}; empty = config.py ({Config.REPOSITORIES[repo]!r})",
    )
    for repo in Config.REPOSITORIES
}

dag_update_repos = DAG(
    'config_update_repos',
    default_args=default_args,
    description='Update all repositories to configured branches',
    schedule=None,
    catchup=False,
    params=REPOSITORY_PARAMS,
)

update_repos_task = BashOperator(
    task_id='update_repos',
    bash_command=get_cli_command('update-repos'),
    # passed via env vars (read by the click options) rather than CLI args, to avoid shell quoting
    env={branch_envvar(repo): "{{ params['%s'] or '' }}" % repo for repo in REPOSITORY_PARAMS},
    append_env=True,
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