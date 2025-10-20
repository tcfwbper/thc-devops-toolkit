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
"""This module provides utility functions and classes for interacting with Docker.

Functions include login, pull, push, build, tag, run, stop, remove, copy, exec, and image inspection utilities.
"""

import json
import re
import subprocess
import time
from collections import deque
from typing import Any

from thc_devops_toolkit.observability import LogLevel, logger


def docker_login(cr_host: str, username: str, password: str) -> None:
    """Logs in to a Docker registry.

    Args:
        cr_host (str): The Docker registry host.
        username (str): The username for authentication.
        password (str): The password for authentication.

    Raises:
        RuntimeError: If login fails.
    """
    logger.info("Logging in to Docker registry: %s with user: %s", cr_host, username)
    password = re.sub(r"\x1b\[[0-9;]*[A-Za-z~]", "", password)  # Clean ANSI escape codes
    cmd = ["docker", "login", cr_host, "-u", username, "--password-stdin"]
    process = subprocess.run(cmd, input=password.encode("utf-8"), capture_output=True, check=False)
    if process.returncode != 0:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to login to Docker registry {cr_host}: {process.stderr.decode('utf-8')}",
        )
        raise RuntimeError(
            f"Failed to login to Docker registry {cr_host} (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}"
        )
    logger.info("Successfully logged in to Docker registry: %s", cr_host)


def docker_pull(full_image_name: str) -> None:
    """Pulls a Docker image from a registry.

    Args:
        full_image_name (str): The full image name (including tag).

    Raises:
        RuntimeError: If pull fails.
    """
    logger.info("Pulling Docker image: %s", full_image_name)
    cmd = ["docker", "pull", full_image_name]
    process = subprocess.run(cmd, capture_output=True, check=False)
    if process.returncode != 0:
        stderr = process.stderr.decode("utf-8") if process.stderr else ""
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to pull image: {full_image_name} (exit code: {process.returncode})",
        )
        raise RuntimeError(f"Failed to pull image: {full_image_name} (exit code: {process.returncode})\n{stderr}")
    logger.info("Successfully pulled Docker image: %s", full_image_name)


def docker_push(full_image_name: str) -> None:
    """Pushes a Docker image to a registry.

    Args:
        full_image_name (str): The full image name (including tag).

    Raises:
        RuntimeError: If push fails.
    """
    logger.info("Pushing Docker image: %s", full_image_name)
    cmd = ["docker", "push", full_image_name]
    process = subprocess.run(cmd, capture_output=True, check=False)
    if process.returncode != 0:
        stderr = process.stderr.decode("utf-8") if process.stderr else ""
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to push image: {full_image_name} (exit code: {process.returncode})",
        )
        raise RuntimeError(f"Failed to push image: {full_image_name} (exit code: {process.returncode})\n{stderr}")
    logger.info("Successfully pushed Docker image: %s", full_image_name)


def docker_inspect(target_object: str) -> dict[str, Any]:
    """Inspects a Docker object (image or container).

    Args:
        target_object (str): The name or ID of the Docker object.

    Returns:
        dict[str, Any]: The inspection result as a dictionary.

    Raises:
        RuntimeError: If inspect fails.
    """
    logger.info("Inspecting Docker object: %s", target_object)
    cmd = ["docker", "inspect", target_object]
    process = subprocess.run(cmd, capture_output=True, check=False)
    if process.returncode != 0:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to inspect: {target_object} (exit code: {process.returncode})",
        )
        raise RuntimeError(f"Failed to inspect: {target_object} (exit code: {process.returncode})\n{str(process.stderr, 'UTF-8')}")
    object_info: dict[str, Any] = json.loads(str(process.stdout, "UTF-8"))[0]
    return object_info


def docker_build(
    full_image_name: str,
    docker_file_path: str,
    build_args: list[dict[str, Any]] | None,
) -> None:
    """Builds a Docker image from a Dockerfile.

    Args:
        full_image_name (str): The full image name to tag.
        docker_file_path (str): Path to the Dockerfile.
        build_args (list[dict[str, Any]] | None): Build arguments as a list of dicts with 'key' and 'value'.

    Raises:
        RuntimeError: If build fails.
    """
    logger.info("Building Docker image: %s from %s", full_image_name, docker_file_path)
    cmd = ["docker", "build"]
    if build_args:
        for build_arg in build_args:
            cmd.extend(["--build-arg", f"{build_arg['key']}={build_arg['value']}"])
    cmd.extend(["-t", full_image_name])
    cmd.extend(["-f", docker_file_path])
    cmd.append(".")
    process = subprocess.run(cmd, capture_output=True, check=False)
    if process.returncode != 0:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to build: {full_image_name} (exit code: {process.returncode})",
        )
        raise RuntimeError(f"Failed to build: {full_image_name} (exit code: {process.returncode})\n{str(process.stderr, 'UTF-8')}")
    logger.info("Successfully built Docker image: %s", full_image_name)


def docker_tag(
    source_full_image_name: str,
    target_full_image_name: str,
) -> None:
    """Tags a Docker image with a new name.

    Args:
        source_full_image_name (str): The source image name.
        target_full_image_name (str): The target image name.

    Raises:
        RuntimeError: If tagging fails.
    """
    logger.info("Tagging Docker image: %s as %s", source_full_image_name, target_full_image_name)
    cmd = ["docker", "tag", source_full_image_name, target_full_image_name]
    process = subprocess.run(cmd, capture_output=True, check=False)
    if process.returncode != 0:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to tag: {target_full_image_name} from {source_full_image_name} (exit code: {process.returncode})",
        )
        raise RuntimeError(
            f"Failed to tag: {target_full_image_name} from {source_full_image_name} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )
    logger.info("Successfully tagged Docker image: %s", target_full_image_name)


def docker_run_daemon(  # pylint: disable=too-many-arguments
    full_image_name: str,
    remove: bool = False,
    container_name: str | None = None,
    entrypoint: str | None = None,
    command: list[str] | None = None,
    env_vars: list[str] | None = None,
    port_mappings: list[str] | None = None,
) -> str:
    """Runs a Docker image in daemon mode (detached container).

    Args:
        full_image_name (str): The image to run.
        remove (bool, optional): Remove container after exit. Defaults to False.
        container_name (str | None, optional): Name for the container. Defaults to None.
        entrypoint (str | None, optional): Entrypoint override. Defaults to None.
        command (list[str] | None, optional): Command to run. Defaults to None.
        env_vars (list[str] | None, optional): Environment variables (e.g., ["VAR1=value1", "VAR2=value2"]). Defaults to None.
        port_mappings (list[str] | None, optional): Port mappings (e.g., ["8080:80", "3000:3000"]). Defaults to None.

    Returns:
        str: The container ID.

    Raises:
        RuntimeError: If run fails.
    """
    logger.info("Running Docker image: %s in daemon mode", full_image_name)
    cmd = ["docker", "run", "-d"]
    if remove:
        cmd.append("--rm")
    if container_name:
        cmd.extend(["--name", container_name])
    if env_vars:
        for env_var in env_vars:
            cmd.extend(["-e", env_var])
    if port_mappings:
        for port_mapping in port_mappings:
            cmd.extend(["-p", port_mapping])
    if entrypoint:
        cmd.extend(["--entrypoint", entrypoint])
    cmd.append(full_image_name)
    if command:
        cmd.extend(command)
    process = subprocess.run(cmd, capture_output=True, check=False)
    if process.returncode != 0:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to run image: {full_image_name} (exit code: {process.returncode})",
        )
        raise RuntimeError(f"Failed to run image: {full_image_name} (exit code: {process.returncode})\n{str(process.stderr, 'UTF-8')}")
    container_id = str(process.stdout, "UTF-8").strip()
    logger.info("Successfully started container: %s", container_id)
    return container_id


def docker_stop(obj: str, timeout: int = 10, poll_interval: float = 1.0) -> None:
    """Stops a running Docker container or object and waits until it is stopped.

    Args:
        obj (str): The container or object name/ID.
        timeout (int, optional): Max seconds to wait for stop. Defaults to 10.
        poll_interval (float, optional): Seconds between status checks. Defaults to 1.0.

    Raises:
        RuntimeError: If stop fails or container does not stop in time.
    """
    logger.info("Stopping Docker object: %s", obj)
    cmd = ["docker", "stop", obj]
    process = subprocess.run(cmd, capture_output=True, check=False)
    if process.returncode != 0:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to stop: {obj} (exit code: {process.returncode})",
        )
        raise RuntimeError(f"Failed to stop: {obj} (exit code: {process.returncode})\n{str(process.stderr, 'UTF-8')}")
    # Wait until container is actually stopped
    start = time.time()
    while True:
        try:
            info = docker_inspect(obj)
            state = info.get("State", {})
            if state.get("Status") == "exited":
                break
        except Exception:  # pylint: disable=broad-except
            # If inspect fails, maybe container is gone
            break
        if time.time() - start > timeout:
            logger.highlight(
                level=LogLevel.ERROR,
                message=f"Timeout waiting for container {obj} to stop",
            )
            raise RuntimeError(f"Timeout waiting for container {obj} to stop")
        time.sleep(poll_interval)
    logger.info("Successfully stopped Docker object: %s", obj)


def docker_remove(obj: str, ignore_errors: bool = False, timeout: int = 10, poll_interval: float = 1.0) -> None:
    """Removes a Docker container and waits until it is removed.

    Args:
        obj (str): The container name or ID.
        ignore_errors (bool, optional): Ignore errors if True. Defaults to False.
        timeout (int, optional): Max seconds to wait for removal. Defaults to 30.
        poll_interval (float, optional): Seconds between status checks. Defaults to 1.0.

    Raises:
        RuntimeError: If remove fails and ignore_errors is False, or container not removed in time.
    """
    logger.info("Removing Docker container: %s", obj)
    cmd = ["docker", "rm", obj]
    process = subprocess.run(cmd, capture_output=True, check=False)
    if process.returncode != 0 and not ignore_errors:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to remove: {obj} (exit code: {process.returncode})",
        )
        raise RuntimeError(f"Failed to remove: {obj} (exit code: {process.returncode})\n{str(process.stderr, 'UTF-8')}")
    # Wait until container is actually removed
    start = time.time()
    while True:
        try:
            docker_inspect(obj)
        except Exception:  # pylint: disable=broad-except
            # If inspect fails, container is gone
            break
        if time.time() - start > timeout:
            logger.highlight(
                level=LogLevel.ERROR,
                message=f"Timeout waiting for container {obj} to be removed",
            )
            if not ignore_errors:
                raise RuntimeError(f"Timeout waiting for container {obj} to be removed")
            break
        time.sleep(poll_interval)
    logger.info("Successfully removed Docker container: %s", obj)


def docker_remove_image(full_image_name: str) -> None:
    """Removes a Docker image.

    Args:
        full_image_name (str): The full image name.

    Raises:
        RuntimeError: If remove fails.
    """
    logger.info("Removing Docker image: %s", full_image_name)
    cmd = ["docker", "rmi", full_image_name]
    process = subprocess.run(cmd, capture_output=True, check=False)
    if process.returncode != 0:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to remove image: {full_image_name} (exit code: {process.returncode})",
        )
        raise RuntimeError(f"Failed to remove image: {full_image_name} (exit code: {process.returncode})\n{str(process.stderr, 'UTF-8')}")
    logger.info("Successfully removed Docker image: %s", full_image_name)


def docker_copy(source: str, target: str) -> None:
    """Copies files/folders between a container and the local filesystem.

    Args:
        source (str): Source path.
        target (str): Target path.

    Raises:
        RuntimeError: If copy fails.
    """
    logger.info("Copying from %s to %s", source, target)
    cmd = ["docker", "cp", source, target]
    process = subprocess.run(cmd, capture_output=True, check=False)
    if process.returncode != 0:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to copy {source} to {target} (exit code: {process.returncode})",
        )
        raise RuntimeError(f"Failed to copy {source} to {target} (exit code: {process.returncode})\n{str(process.stderr, 'UTF-8')}")
    logger.info("Successfully copied from %s to %s", source, target)


def docker_exec(
    command: list[str] | None = None,
    workdir: str | None = None,
    obj: str | None = None,
    print_output: bool = False,
) -> None:
    """Executes a command inside a running Docker container.

    Args:
        command (list | None): The command to execute.
        workdir (str | None, optional): Working directory inside the container.
        obj (str | None, optional): Container name or ID.
        print_output (bool, optional): Print command output. Defaults to False.

    Raises:
        ValueError: If command is not provided.
        RuntimeError: If exec fails.
    """
    logger.info(
        "Executing command in Docker container: %s at %s: %s",
        obj,
        workdir,
        " ".join(command) if command else "",
    )
    cmd = ["docker", "exec"]
    if workdir:
        cmd.extend(["-w", workdir])
    if obj:
        cmd.append(obj)
    if not command:
        logger.highlight(
            level=LogLevel.ERROR,
            message="Must pass command while docker exec",
        )
        raise ValueError("Must pass command while docker exec")
    cmd.extend(command)
    process = subprocess.run(cmd, capture_output=True, check=False)
    if process.returncode != 0:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Failed to exec {command} at {obj}:{workdir} (exit code: {process.returncode})",
        )
        raise RuntimeError(
            f"Failed to exec {command} at {obj}:{workdir} (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}"
        )
    # print output?
    if print_output:
        if process.stdout:
            logger.info("STDOUT from command %s at %s:%s", " ".join(command), obj, workdir)
            logger.highlight(
                level=LogLevel.INFO,
                message=process.stdout.decode("utf-8"),
            )
        if process.stderr:
            logger.info("STDERR from command %s at %s:%s", " ".join(command), obj, workdir)
            logger.highlight(
                level=LogLevel.INFO,
                message=process.stderr.decode("utf-8"),
            )


def get_image_digest(full_image_name: str, precision: int = 6) -> str:
    """Gets the image digest (sha256) of a Docker image.

    Args:
        full_image_name (str): The image name.
        precision (int, optional): Number of characters to return. Defaults to 6.

    Returns:
        str: The image digest prefix.

    Raises:
        ValueError: If precision is out of range.
    """
    if precision < 6 or precision > 64:
        logger.highlight(
            level=LogLevel.ERROR,
            message="Precision must be between 6 and 64",
        )
        raise ValueError("Precision must be between 6 and 64")
    image_info = docker_inspect(full_image_name)
    if not image_info["RepoDigests"]:
        logger.highlight(
            level=LogLevel.WARNING,
            message=f"No RepoDigests found for image: {full_image_name}",
        )
        return ""
    digest = image_info["RepoDigests"][0].split("sha256:")
    if len(digest) < 2:
        logger.highlight(
            level=LogLevel.WARNING,
            message=f"Digest format error for image: {full_image_name}",
        )
        return ""
    full_digest = digest[1]
    if not isinstance(full_digest, str):
        logger.highlight(
            level=LogLevel.WARNING,
            message=f"Digest is not a string for image: {full_image_name}",
        )
        return ""
    return full_digest[:precision]


def get_image_size(full_image_name: str) -> str:
    """Gets the size of a Docker image in human-readable format.

    Args:
        full_image_name (str): The image name.

    Returns:
        str: The image size as a string.

    Raises:
        KeyError: If size key is not found in inspect output.
    """
    image_info = docker_inspect(full_image_name)
    size_key = "Size"
    if size_key not in image_info:
        logger.highlight(
            level=LogLevel.ERROR,
            message=f"Key '{size_key}' not found in docker inspect output for image: {full_image_name}",
        )
        raise KeyError(f"Key '{size_key}' not found in docker inspect output")
    image_size = float(image_info[size_key])
    units = deque(["B", "KB", "MB", "GB", "TB", "PB"])
    while image_size > 1000 and len(units) > 1:
        image_size /= 1000.0
        units.popleft()
    precision = 0 if image_size > 100 else 1 if image_size > 10 else 2
    unit = units.popleft() if units else "B"
    return f"{image_size:.{precision}f}{unit}"
