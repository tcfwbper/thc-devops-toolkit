# Copyright 2025 Tsung-Han Chang. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import argparse
import getpass
import shutil
from pathlib import Path

from thc_devops_toolkit.observability import THCLoggerHighlightLevel, thc_logger
from thc_devops_toolkit.version_control.git import GitCredential, GitRepo

repo_url = "https://github.com/tcfwbper/devpod.git"
repo_dir = "devpod"
repo_dir_tmp = "devpod-tmp"

git_example_dir = Path(__file__).resolve().parent
local_repo_path = git_example_dir / repo_dir
local_repo_path_tmp = git_example_dir / repo_dir_tmp


def main() -> None:
    parser = argparse.ArgumentParser(description="Git example script")
    parser.add_argument("--username", required=True, help="GitHub username")
    parser.add_argument("--email", required=True, help="GitHub email")
    args = parser.parse_args()
    username = args.username
    email = args.email
    branch = "main"
    new_branch = "feat/add-file"

    password = getpass.getpass("GitHub personal access token: ")

    git_credential = GitCredential(user=username, token=password)
    git_repo = GitRepo(
        git_credential=git_credential,
        email=email,
        repo_url=repo_url,
        local_path=str(local_repo_path),
    )

    # Clone the repository
    git_repo.clone(branch=branch)

    # Git remotes
    thc_logger.highlight(THCLoggerHighlightLevel.INFO, f"git remotes: {git_repo.get_remote_url(mask_token=True)}")

    # Git pull
    git_repo.pull(rebase=True, branch=branch, remote_name="origin")

    # Temporary local path as remote
    shutil.copytree(local_repo_path, local_repo_path_tmp)
    git_repo.set_remote_url(new_url=str(local_repo_path_tmp))
    thc_logger.highlight(THCLoggerHighlightLevel.INFO, f"git remotes: {git_repo.get_remote_url(mask_token=True)}")

    # Edit files at the new branch
    git_repo.checkout(ref=new_branch, new_branch=True)
    with (local_repo_path / "tmp").open("w") as tmp_file:
        tmp_file.write("temporary file")
    git_repo.add_all()
    git_repo.commit(message="add a temporary file")

    # Push to local path
    git_repo.push(branch=new_branch, remote_name="origin")

    shutil.rmtree(local_repo_path, ignore_errors=True)
    shutil.rmtree(local_repo_path_tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
