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
"""Utilities for running Ansible playbooks."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import ansible_runner

from thc_devops_toolkit.observability.logger import LogLevel, logger


class Playbook(ABC):
    """Abstract base class for Ansible playbooks."""

    def __init__(
        self,
        playbook_file: str | Path,
        inventory_file: str | Path,
        limit: str,
        extravars: dict[str, Any],
    ) -> None:
        """Initialize the Playbook instance.

        Args:
            playbook_file (str | Path): Path to the Ansible playbook file.
            inventory_file (str | Path): Path to the Ansible inventory file.
            limit (str): Limit for the Ansible playbook execution.
            extravars (dict[str, Any]): Extra variables for the Ansible playbook.
        """
        self.playbook_file = str(playbook_file)
        self.inventory_file = str(inventory_file)
        self.limit = limit
        self.extravars = extravars

    @property
    @abstractmethod
    def vars_overrides(self) -> dict[str, Any]:
        """Variables to override in extravars.

        Returns:
            dict[str, Any]: A dictionary of variables to override.
        """

    @property
    @abstractmethod
    def mandatory_vars(self) -> set[str]:
        """Set of mandatory extravars.

        Returns:
            set[str]: A set of mandatory extravars.
        """

    def verify_extravars(self) -> None:
        """Verify that all mandatory extravars are present.

        Raises:
            ValueError: If any mandatory extravars are missing.
        """
        missing_vars = self.mandatory_vars.difference(set(self.extravars.keys()))
        if missing_vars:
            logger.highlight(level=LogLevel.ERROR, message=f"Missing mandatory extravars: {', '.join(missing_vars)}")
            raise ValueError(f"Missing mandatory extravars: {', '.join(missing_vars)}")

    def override_vars(self) -> None:
        """Override extravars with vars from vars_overrides."""
        self.extravars.update(self.vars_overrides)
        logger.highlight(level=LogLevel.DEBUG, message=f"Override vars: {self.vars_overrides.keys()}")

    def run(self) -> str:
        """Run the Ansible playbook.

        Returns:
            str: The standard output from the playbook execution.

        Raises:
            ValueError: If mandatory extravars are missing.
            RuntimeError: If the playbook execution fails.
        """
        self.override_vars()
        self.verify_extravars()

        # execute the playbook
        logger.info("Run playbook %s with inventory %s and limit %s", self.playbook_file, self.inventory_file, self.limit)
        runner = ansible_runner.run(playbook=self.playbook_file, inventory=self.inventory_file, extravars=self.extravars, limit=self.limit)

        stdout_lines = []
        for event in runner.events:
            if "stdout" in event:
                stdout_lines.append(event["stdout"])

        message = "\n".join(stdout_lines)

        if runner.rc != 0:
            logger.highlight(level=LogLevel.ERROR, message=f"Playbook execution failed: {message}")
            raise RuntimeError(f"Playbook execution failed: {message}")
        logger.info("Playbook executed successfully")
        return message
