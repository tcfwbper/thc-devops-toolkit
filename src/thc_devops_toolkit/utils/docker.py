import logging
import json
import subprocess
from typing import Any
from collections import deque

def docker_login(cr_host: str, username: str, password: str) -> None:
    cmd = ["docker", "login", cr_host, "-u", username, "--password-stdin"]
    process = subprocess.run(cmd, input=password.encode('utf-8'), capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to login to Docker registry {cr_host} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def docker_pull(full_image_name: str) -> None:
    cmd = ["docker", "pull", full_image_name]
    process = subprocess.Popen(cmd)
    process.wait()
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to pull image: {full_image_name} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def docker_push(full_image_name: str) -> None:
    cmd = ["docker", "push", full_image_name]
    process = subprocess.Popen(cmd)
    process.wait()
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to push image: {full_image_name} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def docker_inspect(target_object: str) -> dict[str, Any]:
    cmd = ["docker", "inspect", target_object]
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to inspect: {target_object} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )
    object_info: dict[str, Any] = json.loads(str(process.stdout, 'UTF-8'))[0]
    return object_info

def docker_build(
    full_image_name: str,
    docker_file_path: str,
    build_args: list[dict[str, Any]] | None,
) -> None:
    cmd = ["docker", "build"]
    if build_args:
        for build_arg in build_args:
            cmd.extend(["--build-arg", f"{build_arg['key']}={build_arg['value']}"])
    cmd.extend(["-t", full_image_name])
    cmd.extend(["-f", docker_file_path])
    cmd.append(".")
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to build: {full_image_name} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def docker_tag(
    source_full_image_name: str,
    target_full_image_name: str,
):
    cmd = ["docker", "tag", source_full_image_name, target_full_image_name]
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to tag: {target_full_image_name} from {source_full_image_name} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def docker_run_daemon(
    full_image_name: str,
    remove: bool = False,
    container_name: str | None = None,
    entrypoint: str | None = None,
    command: list[str] | None = None,
) -> str:
    logging.info("Start running image: %s in daemon mode", full_image_name)
    cmd = ["docker", "run", "-d"]
    if remove:
        cmd.append("--rm")
    if container_name:
        cmd.extend(["--name", container_name])
    if entrypoint:
        cmd.extend(["--entrypoint", entrypoint])
    cmd.append(full_image_name)
    if command:
        cmd.extend(command)
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to run image: {full_image_name} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )
    container_id = str(process.stdout, 'UTF-8').strip()
    logging.info("Successfully started container %s", container_id)
    return container_id

def docker_stop(obj: str) -> None:
    cmd = ["docker", "stop", obj]
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to stop: {obj} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def docker_remove(container_name: str, ignore_errors: bool = False) -> None:
    cmd = ["docker", "rm", container_name]
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0 and not ignore_errors:
        raise RuntimeError(
            f"Failed to remove: {container_name} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def docker_copy(source: str, target: str) -> None:
    cmd = ["docker", "cp", source, target]
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to copy {source} to {target} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def docker_exec(
    command: list | None = None,
    workdir: str | None = None,
    obj: str | None = None,
    print_output: bool = False,
) -> None:
    cmd = ["docker", "exec"]
    if workdir:
        cmd.extend(["-w", workdir])
    if obj:
        cmd.append(obj)
    if not command:
        raise ValueError("Must pass command while docker exec")
    cmd.extend(command)
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to exec {command} at {obj}:{workdir} "
            f"(exit code: {process.returncode})\n"
            f"{process.stderr.decode('utf-8')}"
        )
    # print output?
    if print_output:
        if process.stdout:
            logging.info("STDOUT from command %s at %s:%s", " ".join(command), obj, workdir)
            logging.info(process.stdout.decode("utf-8"))
        if process.stderr:
            logging.info("STDERR from command %s at %s:%s", " ".join(command), obj, workdir)
            logging.info(process.stderr.decode("utf-8"))

def get_image_digest(full_image_name: str, precision: int = 6) -> str:
    if precision < 6 or precision > 64:
        raise ValueError("Precision must be between 6 and 64")
    image_info = docker_inspect(full_image_name)
    # example of RepoDigests:
    # "RepoDigests": [
    #     "nginx@sha256:e90ac5331fe095cea01b121a3627174b2e33e06e83720e9a934c7b8ccc9c55a0"
    # ]
    if not image_info["RepoDigests"]:
        return ""
    return image_info["RepoDigests"][0].split('sha256:')[1][:precision]

def get_image_size(full_image_name: str) -> str:
    # get image size
    image_info = docker_inspect(full_image_name)
    size_key = "Size"
    if size_key not in image_info:
        raise KeyError(f"Key '{size_key}' not found in docker inspect output")
    image_size = float(image_info[size_key])
    # process unit
    units = deque(["B", "KB", "MB", "GB", "TB", "PB"])
    while image_size > 1000 and len(units) > 1:
        image_size /= 1000.0
        units.popleft()
    # handle precision
    precision = (
        0 if image_size > 100 else
        1 if image_size > 10 else
        2
    )
    return f"{image_size:.{precision}f}{units.popleft()}"
