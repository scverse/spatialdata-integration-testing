import os
import subprocess
import spatialdata_data_converter.config as sdcc


def update_repo(repo_name: str, branch: str):
    f = os.path.join(sdcc.Config.REPOSITORIES_FOLDER, repo_name)
    os.chdir(f)
    print('updating:', repo_name)
    #if branch is not None:
    #    assert re.fullmatch(r'[a-zA-Z0-9/_-]*', branch), "String contains disallowed characters"

    try:
        subprocess.check_output(['git', 'checkout', '--', '.'], stderr=subprocess.STDOUT)
        subprocess.check_output(['git', 'fetch', '--all'], stderr=subprocess.STDOUT)
        if branch is not None:
            if "pr " in branch:
                pr_number = branch.split(" ")[-1]
                subprocess.check_output(['gh', 'pr', 'checkout', pr_number], stderr=subprocess.STDOUT)
            elif "tag " in branch:
                tag_name = branch.split(" ")[-1]
                subprocess.check_output(['git', 'checkout', tag_name], stderr=subprocess.STDOUT)
            else:
                subprocess.check_output(['git', 'switch', branch], stderr=subprocess.STDOUT)
                subprocess.check_output(['git', 'pull'], stderr=subprocess.STDOUT)
        else:
            # Find and checkout the latest tag starting with 'v' if branch is None
            latest_tag = subprocess.check_output(
                "git tag -l 'v*' --sort=-v:refname | head -n 1",
                shell=True, text=True
            ).strip()
            if latest_tag:
                subprocess.check_output(['git', 'checkout', latest_tag], stderr=subprocess.STDOUT)
            else:
                print("No tag found starting with 'v'")
    except subprocess.CalledProcessError as e:
        print("subprocess.check_outout failed with:\n", e.output.decode())
        raise e

def update_all_repos():
    for repo_name, branch in sdcc.Config.REPOSITORIES.items():
        update_repo(repo_name, branch)
