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
from pathlib import Path
from typing import Any

from thc_devops_toolkit.infrastructure.ansible import Playbook

ansible_example_dir = Path(__file__).resolve().parent
playbook_file = ansible_example_dir / "helloworld.yml"
inventory_file = ansible_example_dir / "inventory.ini"
MY_ENV_VAR = "SomeValue"
"""An example Ansible playbook environment variable."""


class HelloWorldPlaybook(Playbook):
    """Ansible playbook for Hello World example."""

    def __init__(self, playbook_file: str | Path, inventory_file: str | Path, limit: str, extravars: dict[str, Any]) -> None:
        """Initialize the HelloWorldPlaybook instance.

        Args:
            playbook_file (str | Path): Path to the Ansible playbook file.
            inventory_file (str | Path): Path to the Ansible inventory file.
            limit (str): Limit for the Ansible playbook execution.
            extravars (dict[str, Any]): Extra variables for the Ansible playbook.
        """
        super().__init__(playbook_file=playbook_file, inventory_file=inventory_file, limit=limit, extravars=extravars)

    @property
    def mandatory_vars(self) -> set[str]:
        """Variables that must be provided in extravars.

        Returns:
            set[str]: A set of mandatory variable names.
        """
        return {"ansible_host", "ansible_user", "ansible_password"}

    @property
    def vars_overrides(self) -> dict[str, Any]:
        """Variables that override default values in the playbook.

        Returns:
            dict[str, Any]: A dictionary of variable overrides.
        """
        return {"ansible_become": "no"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Ansible example script")
    parser.add_argument("--username", required=True, help="Localhost username")
    args = parser.parse_args()
    username = args.username
    password = getpass.getpass("Localhost password: ")

    playbook = HelloWorldPlaybook(
        playbook_file=playbook_file,
        inventory_file=inventory_file,
        limit="all",
        extravars={
            "ansible_host": "127.0.0.1",
            "ansible_user": username,
            "ansible_password": password,
            "MY_ENV_VAR": MY_ENV_VAR,
        },
    )
    playbook.run()


if __name__ == "__main__":
    main()
