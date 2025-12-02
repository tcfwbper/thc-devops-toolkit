"""Utility functions for running subprocess commands."""

import subprocess
from pathlib import Path

from thc_devops_toolkit.observability import LogLevel, logger


def _decode(value: str | bytes | None) -> str | None:
    """Decode bytes to string if necessary.

    Args:
        value: The value to decode.

    Returns:
        The decoded string or None.
    """
    if value is None:
        return None

    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value.strip()


def run_command(  # pylint: disable=too-many-arguments
    cmd: list[str],
    input_: bytes | None = None,
    capture_output: bool = False,
    cwd: str | Path | None = None,
    check: bool = False,
    env: dict[str, str] | None = None,
) -> str | None:
    """Run a system command with optional input and output capture.

    Args:
        cmd: The command to run as a list of strings.
        input_: Optional input to pass to the command's stdin.
        capture_output: Whether to capture the command's stdout.
        cwd: The working directory to run the command in.
        check: Whether to raise an error on non-zero exit codes.
        env: Optional environment variables to set for the command.

    Returns:
        The captured stdout as a string if capture_output is True, otherwise None.

    Raises:
        RuntimeError: If the command fails and check is False.
    """
    process = subprocess.run(cmd, input=input_, capture_output=capture_output, cwd=cwd, check=check, env=env)

    if (not check) and (process.returncode != 0):
        logger.highlight(
            level=LogLevel.ERROR,
            message=(
                f"Command '{' '.join(cmd)}' failed with exit code {process.returncode}\n"
                f"STDOUT: {_decode(process.stdout)}\n"
                f"STDERR: {_decode(process.stderr)}"
            ),
        )
        raise RuntimeError(f"Command '{' '.join(cmd)}' failed with exit code {process.returncode}")

    if capture_output:
        return _decode(process.stdout)
    return None


def get_exit_code(cmd: list[str], input_: bytes | None = None, cwd: str | Path | None = None) -> int:
    """Run a system command and return its exit code.

    Args:
        cmd: The command to run as a list of strings.
        input_: Optional input to pass to the command's stdin.
        cwd: The working directory to run the command in.

    Returns:
        The command's exit code.
    """
    process = subprocess.run(cmd, input=input_, capture_output=False, cwd=cwd, check=False)
    return process.returncode
