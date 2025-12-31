import subprocess
from spatialdata_data_converter.utils import update_all_repos
import spatialdata_data_converter.config as sdcc
import shlex
import shutil
import nbformat
from pathlib import Path

# import tempfile


def get_env_var(**kwargs) -> str:
    env_var = ""
    # if 'dag_run' in kwargs:
    #     conf = kwargs['dag_run'].conf
    if "env_vars" in kwargs:
        conf = kwargs["env_vars"]
        for k, v in conf.items():
            print(f"Conf: {k}={v}")
        env_var = " && ".join([f"export {k}={v}" for k, v in conf.items()]) + " && "
    return env_var


def run_subprocess(cmd: str, env: str, update_repos: bool = True, **kwargs) -> str:
    if update_repos:
        update_all_repos()
    env_var = get_env_var(**kwargs)
    cmd_env = (
        # f'source {sdcc.Config.BASHRC} && '
        f"source {sdcc.Config.CONDA_SH} && "
        f"conda activate {env} && {env_var}"
    )
    full_cmd = f'bash -c "{cmd_env}{cmd}"'
    print(full_cmd)

    # prints the stdout at the end of the process
    #     process = subprocess.run(
    #         cmd,
    #         shell=True,
    #         text=True,
    #         capture_output=True,
    #     )
    #     print(process.stdout)
    #     print(process.stderr)
    #     if process.returncode != 0:
    #         raise Exception(f'Python subprocess {cmd} failed to run with return code {process.returncode}')
    #     return process.stdout

    # prints the stdout as it is produced
    process = subprocess.Popen(
        full_cmd,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
    )

    output = []
    try:
        for line in process.stdout:
            print(line, end="")  # Print each line as it is produced
            output.append(line)
    except Exception as e:
        process.kill()
        raise e
    finally:
        process.stdout.close()
        process.wait()

    if process.returncode != 0:
        raise Exception(
            f"Python subprocess {full_cmd} failed to run with return code {process.returncode}"
        )
    return "".join(output)


def run_script(
    script_folder: str, script: str, env: str, update_repos: bool = True, **kwargs
):
    cmd = (
        "pushd . && "
        f"cd {script_folder} && "
        f"python {shlex.quote(script)}.py && "
        "popd "
    )
    run_subprocess(cmd=cmd, env=env, update_repos=update_repos, **kwargs)


def run_notebook(
    notebook_folder: str,
    notebook: str,
    env: str,
    update_repos: bool = True,
    run_inplace: bool = False,
    **kwargs,
):
    if run_inplace:
        output_file = notebook
    else:
        # tmpfile = tempfile.NamedTemporaryFile()
        # output_file = tmpfile.name
        output_file = "_latest_run_notebook"
    print(output_file)
    # method 1: doesn't update the notebook (the result is discarded)
    # notebook_cmd = f"jupyter nbconvert --to notebook --stdout --ExecutePreprocessor.timeout=-1 --execute {shlex.quote(notebook)}.ipynb && "
    # method 2: updates the notebook inplace. Warning! Temporarily disabled because it started causing issues with git
    # notebook_cmd = f'jupyter nbconvert --to notebook --inplace --ExecutePreprocessor.timeout=-1 --execute {shlex.quote(notebook)}.ipynb '
    # method 3: updates the notebook (either inplace or discarding the output). Uses papermill to execute the notebook and show the results in real-time

    notebook_cmd = f"papermill {shlex.quote(notebook)}.ipynb {shlex.quote(output_file)}.ipynb --log-output && "
    cmd = "pushd . && " + f"cd {notebook_folder} && " + notebook_cmd + "popd "
    run_subprocess(cmd=cmd, env=env, update_repos=update_repos, **kwargs)

    notebook_path = Path(notebook_folder) / (notebook + ".ipynb")
    if run_inplace:
        des_path = Path(notebook_folder) / "_latest_run_notebook.ipynb"
        shutil.copyfile(notebook_path, str(des_path))

    if run_inplace:
        delete_execution_dependent_metadata(notebook_path=str(notebook_path))
    # tmpfile.close()

    # in case of method 2
    # # the method 2 above doens't print the notebook content, so we do it here to be able to spot errors from the airflow logs
    # with open(f'{notebook_folder}/{notebook}.ipynb', 'r') as f:
    #     print(f.read())

def _delete_metadata_from_dict(metadata: dict) -> None:
    if "papermill" in metadata:
        c = metadata["papermill"]
        if "duration" in c:
            del c["duration"]
        if "start_time" in c:
            del c["start_time"]
        if "end_time" in c:
            del c["end_time"]
    if "execution" in metadata:
        c = metadata["execution"]
        if "iopub.execute_input" in c:
            del c["iopub.execute_input"]
        if "iopub.status.busy" in c:
            del c["iopub.status.busy"]
        if "iopub.status.idle" in c:
            del c["iopub.status.idle"]
        if "shell.execute_reply" in c:
            del c["shell.execute_reply"]

def delete_execution_dependent_metadata(notebook_path: str) -> None:
    print("Deleting execution-dependent metadata from the notebook:", notebook_path)
    nb = nbformat.read(notebook_path, as_version=nbformat.NO_CONVERT)

    for cell in nb.cells:
        _delete_metadata_from_dict(metadata=cell.metadata)
    _delete_metadata_from_dict(metadata=nb.metadata)

    nbformat.write(nb, notebook_path)


if __name__ == "__main__":
    delete_execution_dependent_metadata(
        notebook_path="/Users/macbook/embl/projects/basel/spatialdata-data-converter/dependencies/spatialdata-notebooks/notebooks/developers_resources/storage_format/multiple_elements.ipynb"
    )
