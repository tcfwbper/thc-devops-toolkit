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
"""This module provides utility functions and classes for interacting with Helm charts and registries.

Functions include login, pull, push, package, verify chart versions/values, and dependency checking utilities.
"""

import os
import re
import subprocess
from asyncio.log import logger
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from thc_devops_toolkit.observability import LogLevel, logger
from thc_devops_toolkit.utils.yaml import get_value_from_dict


@dataclass
class Chart:
    """Represents a Helm chart and its metadata.

    Attributes:
        name (str): The chart name.
        version (str): The chart version.
        path_prefix (str | Path): The path prefix to the chart directory.
        dependencies (list[str]): List of chart dependencies.
        check_list (dict[str, Any]): Checklist for value verification.
    """

    name: str
    version: str
    path_prefix: str | Path
    dependencies: list[str]
    check_list: dict[str, Any]

    @classmethod
    def from_path(cls, path_prefix: str | Path, name: str) -> "Chart":
        """Creates a Chart instance by reading Chart.yaml and values.yaml from the specified path.

        Args:
            path_prefix (str | Path): The path prefix to the chart directory.
            name (str): The chart name.

        Returns:
            Chart: The created Chart instance.

        Raises:
            FileNotFoundError: If Chart.yaml or values.yaml is not found.
            ValueError: If required fields are missing in Chart.yaml.
        """
        chart_root = Path(path_prefix) / name
        chart_yaml: Path = chart_root / "Chart.yaml"
        values_yaml: Path = chart_root / "values.yaml"
        yaml = YAML(typ="safe")

        if not chart_yaml.is_file():
            raise FileNotFoundError(f"Chart.yaml not found at {chart_yaml}")
        if not values_yaml.is_file():
            raise FileNotFoundError(f"values.yaml not found at {values_yaml}")

        # Load Chart.yaml
        chart_data = yaml.load(chart_yaml)
        if not chart_data or "version" not in chart_data:
            raise ValueError(f"Chart version not found in {chart_yaml}")
        version = chart_data["version"]
        dependencies = chart_data.get("dependencies", [])
        if dependencies is None:
            dependencies = []
        dependencies = [dependency["name"] for dependency in dependencies if "name" in dependency]

        return cls(
            name=name,
            version=version,
            path_prefix=path_prefix,
            dependencies=dependencies,
            check_list={},
        )


def helm_login(cr_host: str, username: str, password: str) -> None:
    """Logs in to a Helm registry.

    Args:
        cr_host (str): The Helm registry host.
        username (str): The username for authentication.
        password (str): The password for authentication.

    Raises:
        RuntimeError: If login fails.
    """
    logger.info("Logging in to Helm registry: %s", cr_host)
    password = re.sub(r"\x1b\[[0-9;]*[A-Za-z~]", "", password)  # Clean ANSI escape codes
    cmd = ["helm", "registry", "login", cr_host, "-u", username, "--password-stdin"]
    env = os.environ.copy()
    env["HELM_EXPERIMENTAL_OCI"] = "1"
    process = subprocess.run(cmd, input=password.encode("utf-8"), capture_output=True, check=False, env=env)
    if process.returncode != 0:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to login to Helm registry {cr_host} (exit code: {process.returncode})",
        )
        raise RuntimeError(f"Failed to login to Helm registry {cr_host} (exit code: {process.returncode})\n{str(process.stderr, 'UTF-8')}")
    logger.info("Successfully logged in to Helm registry: %s", cr_host)


def helm_pull(remote_chart: str, version: str, untar: bool = False) -> None:
    """Pulls a Helm chart from a remote registry.

    Args:
        remote_chart (str): The remote chart name.
        version (str): The chart version.
        untar (bool): Whether to untar the chart after pulling.

    Raises:
        RuntimeError: If pull fails.
    """
    logger.info("Pulling Helm chart %s with version %s", remote_chart, version)
    cmd = ["helm", "pull", remote_chart, "--version", version]
    if untar:
        cmd.append("--untar")
    env = os.environ.copy()
    env["HELM_EXPERIMENTAL_OCI"] = "1"
    process = subprocess.run(cmd, capture_output=True, check=False, env=env)
    if process.returncode != 0:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to pull '{remote_chart}' with version {version} (exit code: {process.returncode})",
        )
        raise RuntimeError(
            f"Failed to pull '{remote_chart}' with version {version} (exit code: {process.returncode})\n{str(process.stderr, 'UTF-8')}"
        )
    logger.info("Successfully pulled Helm chart: %s", remote_chart)


def helm_package(chart: Chart) -> None:
    """Packages a Helm chart into a .tgz archive.

    Args:
        chart (Chart): The chart to package.

    Raises:
        RuntimeError: If packaging fails.
    """
    chart_path = str(Path(chart.path_prefix) / chart.name)
    logger.info("Packaging Helm chart at path: %s", chart_path)
    cmd = ["helm", "package", chart_path]
    env = os.environ.copy()
    env["HELM_EXPERIMENTAL_OCI"] = "1"
    process = subprocess.run(cmd, capture_output=True, check=False, env=env)
    if process.returncode != 0:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to package Helm chart at path '{chart_path}' (exit code: {process.returncode})",
        )
        raise RuntimeError(
            f"Failed to package Helm chart on path '{chart_path}' (exit code: {process.returncode})\n{str(process.stderr, 'UTF-8')}"
        )
    logger.info("Successfully packaged Helm chart: %s", chart.name)


def helm_push(chart: Chart, repository: str) -> None:
    """Pushes a packaged Helm chart to a remote repository.

    Args:
        chart (Chart): The chart to push.
        repository (str): The repository to push to.

    Raises:
        RuntimeError: If push fails.
    """
    tgz_file = chart.name + "-" + chart.version + ".tgz"
    logger.info("Pushing Helm chart %s to repository: %s", tgz_file, repository)
    cmd = ["helm", "push", tgz_file, repository]
    env = os.environ.copy()
    env["HELM_EXPERIMENTAL_OCI"] = "1"
    process = subprocess.run(cmd, capture_output=True, check=False, env=env)
    if process.returncode != 0:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to push '{tgz_file}' to '{repository}' (exit code: {process.returncode})\n{str(process.stderr, 'UTF-8')}",
        )
        raise RuntimeError(
            f"Failed to push '{tgz_file}' to '{repository}' (exit code: {process.returncode})\n{str(process.stderr, 'UTF-8')}"
        )
    logger.info("Successfully pushed Helm chart: %s", tgz_file)


def verify_chart_version(
    chart: Chart,
    expected_chart_version: str,
) -> bool:
    """Verifies that the chart version matches the expected version.

    Args:
        chart (Chart): The chart to verify.
        expected_chart_version (str): The expected version string.

    Returns:
        bool: True if version matches, False otherwise.
    """
    chart_root = Path(chart.path_prefix) / chart.name
    chart_yaml: Path = chart_root / "Chart.yaml"
    yaml = YAML(typ="safe")
    logger.info("Verifying chart version for %s", chart_yaml)
    chart_data = yaml.load(chart_yaml)
    if not chart_data or "version" not in chart_data:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Chart version not found in {chart_root}/Chart.yaml",
        )
        return False
    cur_chart_version = chart_data["version"]
    if cur_chart_version != expected_chart_version:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Chart version mismatch for {chart_root}: expected {expected_chart_version}, found {cur_chart_version}",
        )
        return False
    logger.info("Chart version verified: %s", cur_chart_version)
    return True


def verify_chart_values(
    chart: Chart,
    check_list: dict[str, Any],
) -> bool:
    """Verifies that chart values match the provided checklist.

    Args:
        chart (Chart): The chart to verify.
        check_list (dict[str, Any]): The checklist of key-value pairs to verify.

    Returns:
        bool: True if all values match, False otherwise.
    """
    are_values_correct = True
    chart_root = Path(chart.path_prefix) / chart.name
    values_yaml: Path = chart_root / "values.yaml"
    yaml = YAML(typ="safe")
    logger.info("Verifying chart values for %s", values_yaml)
    values_data = yaml.load(values_yaml)
    # Check if the checklist is a dictionary
    if not isinstance(check_list, dict):
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Check list for {chart_root} is not a dictionary",
        )
        return False
    # Check if the values match the checklist
    for key, value in check_list.items():
        if not isinstance(key, str):
            logger.highlight(
                level=LogLevel.ERROR,
                message=f"Key {key} in check_list for {chart_root} is not a string",
            )
            are_values_correct = False
            continue
        cur_value, get_value_success = get_value_from_dict(values_data, key)
        if not get_value_success:
            logger.highlight(
                level=LogLevel.ERROR,
                message=f"Key {key} not found in values.yaml for chart {chart_root}",
            )
            are_values_correct = False
            continue
        if not cur_value == value:
            logger.highlight(
                level=LogLevel.ERROR,
                message=f"Values mismatch for {chart_root}: expected {key}={value}, found {cur_value}",
            )
            are_values_correct = False
    if are_values_correct:
        logger.info("All chart values verified for %s", chart_root)
    return are_values_correct


def verify_dependencies(charts: list[Chart]) -> None:
    """Verifies that chart dependencies are valid and acyclic.

    Args:
        charts (list[Chart]): List of charts to verify dependencies for.

    Raises:
        ValueError: If cyclic or missing dependencies are detected.
    """
    logger.info("Verifying chart dependencies...")
    # build graph
    graph: dict[str, Chart] = defaultdict(None)
    for chart in charts:
        graph[chart.name] = chart

    # define dfs
    visited = set()
    recursive_stack = set()

    def verify_dependencies_dfs(chart: Chart) -> None:
        chart_name = chart.name
        # cycle detected?
        if chart_name in recursive_stack:
            logger.error("Cyclic dependencies detected at %s", chart_name)
            raise ValueError("Cyclic dependencies detected")
        # skip?
        if chart_name in visited:
            return
        recursive_stack.add(chart_name)

        # handle neighbors
        chart_dependencies = chart.dependencies if chart.dependencies else []
        for dependency in chart_dependencies:
            if dependency not in graph:
                logger.error("Dependency '%s' of chart '%s' not found", dependency, chart_name)
                raise ValueError(f"Dependency '{dependency}' of chart '{chart_name}' not found")
            verify_dependencies_dfs(graph[dependency])

        # dependencies verified
        recursive_stack.remove(chart_name)
        visited.add(chart_name)
        logger.debug("Dependencies verified for chart: %s", chart_name)

    # try dfs
    for chart in graph.values():
        verify_dependencies_dfs(chart)
    logger.info("All chart dependencies verified successfully.")
