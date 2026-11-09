import signal
import subprocess
import sys
import time
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


SIGNAL_HINTS = {
    signal.SIGTERM: (
        "Airflow stops tasks with SIGTERM when they hit their execution_timeout, when "
        "someone marks the run/task as failed or success or clears it, or when the "
        "worker shuts down. It was not an error inside the command itself."
    ),
    signal.SIGKILL: "Killed with SIGKILL, typically by the kernel's out-of-memory killer (check `dmesg`).",
}


class SubprocessFailed(Exception):
    """A command run via run_subprocess exited non-zero (the banner has already been printed)."""

    def __init__(self, returncode: int, cmd: str):
        self.returncode = returncode
        self.cmd = cmd
        super().__init__(f"command failed with return code {returncode}: {cmd}")


def _failure_excerpt(lines: list[str], max_lines: int = 80) -> list[str]:
    """The part of the output that explains the failure, best guess."""
    # pytest: everything from its final summary on
    for i in range(len(lines) - 1, -1, -1):
        if "short test summary info" in lines[i]:
            return lines[i:][-max_lines:]
    # papermill / python: the last traceback
    for marker in ("Exception encountered at", "Traceback (most recent call last)"):
        for i in range(len(lines) - 1, -1, -1):
            if marker in lines[i]:
                return lines[i:][-max_lines:]
    return lines[-30:]


def _print_banner(title: str, body: list[str]) -> None:
    bar = "=" * 30
    print()
    print(f"{bar} {title} {bar}")
    for line in body:
        print(line.rstrip("\n"))
    print("=" * (len(title) + 2 * len(bar) + 2), flush=True)


def _describe_returncode(returncode: int) -> tuple[str, list[str]]:
    # negative: the child was killed by a signal (Popen convention);
    # 128+N: bash reporting that its child was killed by signal N
    signum = -returncode if returncode < 0 else returncode - 128 if returncode > 128 else None
    if signum:
        try:
            name = signal.Signals(signum).name
        except ValueError:
            name = f"signal {signum}"
        return f"KILLED ({name})", [SIGNAL_HINTS.get(signum, "")]
    return f"FAILED (exit code {returncode})", []


def run_subprocess(cmd: str, env: str | None, update_repos: bool = True, **kwargs) -> str:
    """Run `cmd` in bash, inside the conda env `env`; `env=None` runs it without activating one."""
    if update_repos:
        update_all_repos()
    env_var = get_env_var(**kwargs)
    if env is None:
        cmd_env = env_var
    else:
        cmd_env = (
            # f'source {sdcc.Config.BASHRC} && '
            f"source {sdcc.Config.CONDA_SH} && "
            f"conda activate {env} && {env_var}"
        )
    full_cmd = f'bash -c "{cmd_env}{cmd}"'

    # prints the stdout as it is produced
    print(full_cmd, flush=True)
    process = subprocess.Popen(
        full_cmd,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
    )

    # If Airflow terminates the task, it signals the whole process group. Make sure
    # we still say so (and why) at the end of the log instead of vanishing silently.
    started = time.monotonic()
    output = []

    def _on_term(signum, frame):
        process.terminate()
        minutes = (time.monotonic() - started) / 60
        title, hints = _describe_returncode(-signum)
        _print_banner(title, [f"after {minutes:.1f} min while running: {cmd[:200]}", *hints, "", "Last output:", *output[-15:]])
        sys.exit(128 + signum)

    try:
        previous = signal.signal(signal.SIGTERM, _on_term)
    except ValueError:  # not in the main thread; keep the default behaviour
        previous = None
    try:
        for line in process.stdout:
            print(line, end="")  # Print each line as it is produced
            output.append(line)
    except Exception:
        process.kill()
        raise
    finally:
        process.stdout.close()
        process.wait()
        if previous is not None:
            signal.signal(signal.SIGTERM, previous)

    if process.returncode != 0:
        title, hints = _describe_returncode(process.returncode)
        _print_banner(title, [f"command: {cmd[:200]}", *[h for h in hints if h], "", *_failure_excerpt(output)])
        raise SubprocessFailed(process.returncode, full_cmd)
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

    # -k python3 forces the kernel of the active conda env, ignoring the kernelspec the
    # notebook was authored with (which often refers to a kernel that exists only on the
    # author's machine)
    notebook_cmd = f"papermill {shlex.quote(notebook)}.ipynb {shlex.quote(output_file)}.ipynb -k python3 --log-output && "
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
