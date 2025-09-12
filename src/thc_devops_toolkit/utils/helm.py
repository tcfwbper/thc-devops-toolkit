from collections import defaultdict
from dataclasses import dataclass
import logging
from pathlib import Path
import subprocess
from typing import Any

from ruamel.yaml import YAML

from thc_devops_toolkit.utils.yaml import get_value_from_dict

@dataclass
class Chart:
    name: str
    version: str
    path_prefix: str | Path
    dependencies: list[str]
    check_list: dict[str, Any]

def helm_login(cr_host: str, username: str, password: str) -> None:
    cmd = ["helm", "registry", "login", cr_host, "-u", username, "--password-stdin"]
    process = subprocess.run(cmd, input=password.encode('utf-8'), capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to login to Helm registry {cr_host} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def helm_pull(remote_chart: str, version: str) -> None:
    cmd = ["helm", "pull", remote_chart, "--version", version]
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to pull '{remote_chart}' with version {version} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def helm_package(chart: Chart) -> None:
    chart_path = str(Path(chart.path_prefix) / chart.name)
    cmd = ["helm", "package", chart_path]
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to package Helm chart on path '{chart_path}' (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def helm_push(chart: Chart, repository: str) -> None:
    tgz_file = chart.name + "-" + chart.version + ".tgz"
    cmd = ["helm", "push", tgz_file, repository]
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to push '{tgz_file}' to '{repository}' (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def verify_chart_version(
    chart: Chart,
    expected_chart_version: str,
) -> bool:
    chart_root = Path(chart.path_prefix) / chart.name
    chart_yaml: Path = chart_root / "Chart.yaml"
    yaml = YAML(typ="safe")
    chart_data = yaml.load(chart_yaml)
    if not chart_data or "version" not in chart_data:
        logging.error("Chart version not found in %s/Chart.yaml", chart_root)
        return False
    cur_chart_version = chart_data["version"]
    if cur_chart_version != expected_chart_version:
        logging.error(
            "Chart version mismatch for %s: expected %s, found %s",
            chart_root,
            expected_chart_version,
            cur_chart_version,
        )
        return False
    return True

def verify_chart_values(
    chart: Chart,
    check_list: dict[str, Any],
) -> bool:
    are_values_correct = True
    chart_root = Path(chart.path_prefix) / chart.name
    values_yaml: Path = chart_root / "values.yaml"
    yaml = YAML(typ="safe")
    values_data = yaml.load(values_yaml)
    # Check if the checklist is a dictionary
    if not isinstance(check_list, dict):
        logging.error(
            "Check list for %s is not a dictionary",
            chart_root,
        )
        return False
    # Check if the values match the checklist
    for key, value in check_list.items():
        if not isinstance(key, str):
            logging.error(
                "Key %s in check_list for %s is not a string",
                key,
                chart_root,
            )
            are_values_correct = False
            continue
        cur_value, get_value_success = get_value_from_dict(values_data, key)
        if not get_value_success:
            are_values_correct = False
            continue
        if not cur_value == value:
            logging.error(
                "Values mismatch for %s: expected %s=%s, found %s",
                chart_root,
                key,
                value,
                cur_value,
            )
            are_values_correct = False
    return are_values_correct

def verify_dependencies(charts: list[Chart]) -> None:
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
            raise ValueError("Cyclic dependencies detected")
        # skip?
        if chart_name in visited:
            return
        recursive_stack.add(chart_name)
        
        # handle neighbors
        chart_dependencies = chart.dependencies if chart.dependencies else []
        for dependency in chart_dependencies:
            if dependency not in graph:
                raise ValueError(f"Dependency '{dependency}' of chart '{chart_name}' not found")
            verify_dependencies_dfs(graph[dependency])
        
        # dependencies verified
        recursive_stack.remove(chart_name)
        visited.add(chart_name)
    
    # try dfs
    for chart in graph.values():
        verify_dependencies_dfs(chart)
