import os
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from spatialdata_data_converter.config import Config, get_airflow_default_args, get_cli_command

default_args = get_airflow_default_args()

# List of notebooks
# docs_notebooks = ['aggregation', 'transformations']
EXCLUDED_NOTEBOOKS = ['technology_curio.ipynb', 'technology_stereoseq.ipynb', 'speed_up_illustration.ipynb', 'technology_cosmx.ipynb', '_latest_run_notebook.ipynb']
docs_notebooks = [s[:-len('.ipynb')] for s in os.listdir(Config.DOCS_NOTEBOOKS_FOLDER) if s.endswith('.ipynb') and s not in EXCLUDED_NOTEBOOKS]

for notebook in docs_notebooks:
    # --------- run a single documentation notebook ---------
    dag_id = f'notebook_{notebook}'

    dag = DAG(
        dag_id,
        default_args=default_args,
        description=f'Run notebook {notebook}',
        schedule=None,
        catchup=False
    )

    notebook_task = BashOperator(
        task_id=f'notebook_{notebook}',
        bash_command=get_cli_command(f'run-docs-notebook --notebook {notebook}'),
        dag=dag,
        retries=0,
    )
    globals()[f'notebook_task_{notebook}'] = notebook_task

    # Assign the dag object to a variable that complies with Airflow's naming conventions
    globals()[dag_id] = dag

# --------- call the symlinkers for specific datasets ---------
for dataset in ['napari_rois', 'densenet', 'alignment_using_landmarks', 'spatial_query', 'squidpy_integration', 'technology_merfish', 'technology_mibitof', 'technology_visium', 'technology_visium_hd', 'technology_visium_hd_mouse_4.0.1', 'technology_xenium', 'transformations', 'transformations_advanced', 'technology_spacem']:

    globals()[f'symlinker_{dataset}'] = BashOperator(
        task_id=f'symlinker_{dataset}',
        bash_command=get_cli_command(f'create-symlinks --dataset {dataset}'),
        dag=globals()[f'notebook_{dataset}'],
    )
    globals()[f'symlinker_{dataset}'] >> globals()[f'notebook_task_{dataset}']

# --------- aggregation uses the transformations symlinker ---------
globals()['symlinker_aggregation'] = BashOperator(
    task_id='symlinker_aggregation',
    bash_command=get_cli_command('create-symlinks --dataset transformations'),
    dag=globals()['notebook_aggregation'],
)
globals()['symlinker_aggregation'] >> globals()['notebook_task_aggregation']

globals()['symlinker_intro'] = BashOperator(
    task_id='symlinker_intro',
    bash_command=get_cli_command('create-symlinks --dataset transformations'),
    dag=globals()['notebook_intro'],
)
globals()['symlinker_intro'] >> globals()['notebook_task_intro']

globals()['symlinker_table_queries'] = BashOperator(
    task_id='symlinker_table_queries',
    bash_command=get_cli_command('create-symlinks --dataset technology_mibitof'),
    dag=globals()['notebook_table-queries'],
)
globals()['symlinker_table_queries'] >> globals()['notebook_task_table-queries']

# --------- run all the docs notebooks (lightweight) ---------
notebook_docs_all = DAG(
    'notebook_docs_all',
    default_args=default_args,
    description='Trigger all the notebook tasks for docs notebooks (lightweight)',
    # every day at 12PM
    schedule='0 12 * * *',
    # schedule=None,
    # schedule_interval='@daily',
    catchup=False
)
for notebook in docs_notebooks:
    trigger = TriggerDagRunOperator(
        task_id=f'trigger_notebook_{notebook}_from_notebook_docs_all',
        trigger_dag_id=f'notebook_{notebook}',
        dag=notebook_docs_all,
    )
