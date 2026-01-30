import re

from spatialdata_data_converter.subprocess_runner import run_notebook, run_subprocess
import spatialdata_data_converter.config as sdcc


def update_dev_datasets_func(update_repos: bool = False):
    notebooks = ["multiple_elements"]
    # update all the datasets
    for notebook in notebooks:
        run_notebook(
            notebook_folder=sdcc.Config.DEV_DATASETS_FOLDER,
            notebook=notebook,
            env=sdcc.Config.ENV,
            update_repos=update_repos,
            run_inplace=True,
        )
        # update only once
        if update_repos:
            update_repos = False
    # commit the changes
    cmd = f"python -c \\\"from spatialdata import __version__; print('BEGIN' + __version__ + 'END')\\\" "
    spatialdata_version_raw = run_subprocess(cmd, env=sdcc.Config.ENV, update_repos=False)
    spatialdata_version = re.search(r"BEGIN(.*?)END", spatialdata_version_raw).group(1)
    cmd = (
        f"cd {sdcc.Config.REPOSITORIES_FOLDER}/spatialdata && "
        # "(git log -1 --oneline | awk '{print $1}') "
        "(git log -1 --oneline | cut -d ' ' -f 1) "
    )
    spatialdata_commit = run_subprocess(cmd, env=sdcc.Config.ENV, update_repos=False).replace(
        "\n", ""
    )
    commit_message = f"autorun: storage format; spatialdata from {spatialdata_commit} ({spatialdata_version})"
    print(f'commit_message = "{commit_message}"')

    cmd = f"cd {sdcc.Config.DEV_DATASETS_FOLDER} && git add . "
    run_subprocess(cmd, env=sdcc.Config.ENV, update_repos=False)

    cmd = f"cd {sdcc.Config.DEV_DATASETS_FOLDER} && git diff --cached --numstat | wc -l "
    has_changes = run_subprocess(cmd, env=sdcc.Config.ENV, update_repos=False).replace(
        "\n", ""
    ).replace(
        " ", ""
    )
    print(f"has_changes = {has_changes!r}")
    if has_changes != "0":
        print("CHANGES DETECTED")
        cmd = (
            f"cd {sdcc.Config.DEV_DATASETS_FOLDER} && "
            f"git commit -m '{commit_message}' && git pull && git push "
        )
        _ = run_subprocess(cmd, env=sdcc.Config.ENV, update_repos=False)
    else:
        print("no changes detected")