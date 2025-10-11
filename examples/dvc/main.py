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
import logging
import shutil
from pathlib import Path

from thc_devops_toolkit.version_control.dvc import DvcRepo
from thc_devops_toolkit.version_control.git import GitCredential, GitRepo

# Set up a default logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


dvc_example_dir = Path(__file__).resolve().parent
remote_name = "my_remote"
local_repo_path = dvc_example_dir / "my_repo"
dvc_remote_path = dvc_example_dir / "my_remote"
tracked_dir = Path("tracked")
tracked_file_in_dir = tracked_dir / "test.txt"
tracked_file = Path("test2.txt")


def main() -> None:
    # Initialize dvc repo
    git_credential = GitCredential(
        user="my_user",
        token="my_token",
    )
    git_repo = GitRepo(
        git_credential=git_credential,
        email="my_email@example.com",
        repo_url="",
        local_path=str(local_repo_path),
    )
    git_repo.init()
    dvc_repo = DvcRepo(local_path=str(local_repo_path))
    dvc_repo.init()

    # Set up DVC remote
    dvc_remote_path.mkdir(parents=True, exist_ok=True)
    dvc_repo.set_remote(remote_name=remote_name, remote_path=dvc_remote_path)

    # Add files
    (local_repo_path / tracked_dir).mkdir(parents=True, exist_ok=True)
    with open(local_repo_path / tracked_file_in_dir, "w") as file:
        file.write("This is a test file.")
    dvc_repo.add_directory(directory=tracked_dir)
    with open(local_repo_path / tracked_file, "w") as file:
        file.write("This is another test file.")
    dvc_repo.add_files(files=[tracked_file])

    # Push to remote
    dvc_repo.push(remote_name=remote_name)

    # Access DVC file and tracked files if needed
    dvc_file = dvc_repo.get_dvc_file(tracked_dir)
    dvc_tracked_files = dvc_repo.get_dvc_tracked_files(dvc_file.outputs[0])

    shutil.rmtree(local_repo_path, ignore_errors=True)
    shutil.rmtree(dvc_remote_path, ignore_errors=True)


if __name__ == "__main__":
    main()
