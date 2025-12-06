"""Utility functions for running subprocess commands."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from subprocess import CalledProcessError

from thc_devops_toolkit.observability import LogLevel, logger


@dataclass
class SubprocessResult:
    """Dataclass to hold subprocess command results."""

    stdout: str
    stderr: str
    returncode: int


def _decode(value: str | bytes | None) -> str:
    """Decode bytes to string if necessary.

    Args:
        value: The value to decode.

    Returns:
        The decoded string.
    """
    if value is None:
        return ""

    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value.strip()


def run_command(  # pylint: disable=too-many-arguments
    cmd: list[str],
    input_: bytes | None = None,
    capture_output: bool = False,
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    log_on_errors: bool = True,
    raise_on_errors: bool = True,
) -> SubprocessResult:
    """Run a system command with optional input and output capture.

    Args:
        cmd: The command to run as a list of strings.
        input_: Optional input to pass to the command's stdin.
        capture_output: Whether to capture stdout and stderr.
        cwd: The working directory to run the command in.
        env: Optional environment variables to set for the command.
        log_on_errors: Whether to log errors if the command fails.
        raise_on_errors: Whether to raise an exception if the command fails.

    Returns:
        A SubprocessResult object containing stdout, stderr, and the return code.

    Raises:
        CalledProcessError: If the command fails and raise_on_errors is True.
    """
    process = subprocess.run(cmd, input=input_, capture_output=capture_output, cwd=cwd, check=False, env=env)

    result = SubprocessResult(
        stdout=_decode(process.stdout),
        stderr=_decode(process.stderr),
        returncode=process.returncode,
    )

    # Run commands with log_on_error=False if they contain sensitive information
    # Or sensitive information might be logged here if the command fails
    if result.returncode != 0 and log_on_errors:
        logger.highlight(
            level=LogLevel.ERROR,
            message=(
                f"Command '{' '.join(cmd)}' failed with exit code {result.returncode}\n"
                f"STDOUT: {result.stdout}\n"
                f"STDERR: {result.stderr}"
            ),
        )

    if result.returncode != 0 and raise_on_errors:
        raise CalledProcessError(
            returncode=result.returncode,
            cmd=cmd,
            output=result.stdout,
            stderr=result.stderr,
        )

    return result


__all__ = [
    "CalledProcessError",
]
