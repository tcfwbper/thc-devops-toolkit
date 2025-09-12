"""This module provides utility functions and classes for interacting with Git repositories.

Functions include cloning, configuring, committing, pushing, pulling, and managing remotes.
"""

import logging
import subprocess
from dataclasses import dataclass

# Set up a default logger for this module
logger = logging.getLogger(__name__)


@dataclass
class GitCredential:
    """Represents Git credentials for authentication.

    Attributes:
        user (str): The Git username.
        token (str): The personal access token (PAT) for authentication.
    """

    user: str
    token: str


def get_pat_format_url(
    git_credential: GitCredential,
    repo_url: str,
    server_protocol: str = "https",
) -> str:
    """Constructs a repository URL with embedded PAT credentials.

    Args:
        git_credential (GitCredential): The Git credentials.
        repo_url (str): The repository URL (without protocol/user/token).
        server_protocol (str, optional): The protocol to use (default: "https").

    Returns:
        str: The repository URL in PAT format.
    """
    logger.info("Repository URL: %s", repo_url)
    pat_format_url = f"{server_protocol}://{git_credential.user}:{git_credential.token}@{repo_url}"
    return pat_format_url


def git_clone_repo(
    pat_format_url: str,
    branch: str = "main",
) -> None:
    """Clones a Git repository using the provided PAT format URL and branch.

    Args:
        pat_format_url (str | None): The repository URL with PAT credentials.
        branch (str, optional): The branch to clone (default: "main").

    Raises:
        RuntimeError: If the clone operation fails.
    """
    logger.info("Cloning repo from %s on branch %s", pat_format_url, branch)
    cmd = ["git", "clone", "-b", branch, pat_format_url]
    process = subprocess.run(cmd, capture_output=True, check=True)
    if process.returncode != 0:
        logger.error("Failed to clone repo (exit code: %d)", process.returncode)
        raise RuntimeError(f"Failed to clone repo (exit code: {process.returncode})")
    logger.info("Successfully cloned repo from %s", pat_format_url)


def git_set_config(
    user: str,
    email: str,
) -> None:
    """Sets the Git user.name and user.email configuration.

    Args:
        user (str): The Git username.
        email (str): The Git user email.

    Raises:
        RuntimeError: If setting the config fails.
    """
    logger.info("Setting git config user.email to %s", email)
    cmd = ["git", "config", "user.email", email]
    process = subprocess.run(cmd, capture_output=True, check=True)
    if process.returncode != 0:
        logger.error("Failed to set git config email: %s (exit code: %d)", email, process.returncode)
        raise RuntimeError(f"Failed to set git config email: {email} (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}")
    logger.info("Setting git config user.name to %s", user)
    cmd = ["git", "config", "user.name", user]
    process = subprocess.run(cmd, capture_output=True, check=True)
    if process.returncode != 0:
        logger.error("Failed to set git config username: %s (exit code: %d)", user, process.returncode)
        raise RuntimeError(f"Failed to set git config username: {user} (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}")
    logger.info("Successfully set git config for user: %s, email: %s", user, email)


def git_checkout(branch: str) -> None:
    """Checks out a branch, creating it if it does not exist.

    Args:
        branch (str): The branch name to checkout.

    Raises:
        RuntimeError: If checkout fails.
    """
    logger.info("Checking out branch: %s", branch)
    cmd = ["git", "checkout", "-B", branch]
    process = subprocess.run(cmd, capture_output=True, check=True)
    if process.returncode != 0:
        logger.error("Failed to checkout to %s (exit code: %d)", branch, process.returncode)
        raise RuntimeError(f"Failed to checkout to {branch} (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}")
    logger.info("Successfully checked out branch: %s", branch)


def git_add_all() -> None:
    """Adds all changes to the Git staging area.

    Raises:
        RuntimeError: If adding changes fails.
    """
    logger.info("Adding all changes to git staging area")
    cmd = ["git", "add", "."]
    process = subprocess.run(cmd, capture_output=True, check=True)
    if process.returncode != 0:
        logger.error("Failed to add changes (exit code: %d)", process.returncode)
        raise RuntimeError(f"Failed to add changes (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}")
    logger.info("Successfully added all changes to staging area")


def git_commit(message: str = "default commit message") -> None:
    """Commits staged changes with a commit message.

    Args:
        message (str, optional): The commit message (default: "default commit message").

    Raises:
        RuntimeError: If commit fails.
    """
    logger.info("Committing with message: %s", message)
    cmd = ["git", "commit", "-m", message]
    process = subprocess.run(cmd, capture_output=True, check=True)
    if process.returncode != 0:
        logger.error("Failed to commit staged changes (exit code: %d)", process.returncode)
        raise RuntimeError(f"Failed to commit staged changes (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}")
    logger.info("Successfully committed changes")


def git_pull(rebase: bool, branch: str, remote_name: str = "origin") -> None:
    """Pulls changes from a remote branch, optionally using rebase.

    Args:
        rebase (bool): Whether to use rebase during pull.
        branch (str): The branch to pull.
        remote_name (str, optional): The remote name (default: "origin").

    Raises:
        RuntimeError: If pull fails.
    """
    logger.info("Pulling from remote %s branch %s (rebase=%r)", remote_name, branch, rebase)
    cmd = ["git", "pull"]
    if rebase:
        cmd.append("--rebase")
    cmd.append(remote_name)
    cmd.append(branch)
    process = subprocess.run(cmd, capture_output=True, check=True)
    if process.returncode != 0:
        logger.error("Failed to pull from remote (exit code: %d)", process.returncode)
        raise RuntimeError(f"Failed to pull from remote (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}")
    logger.info("Successfully pulled from remote %s branch %s", remote_name, branch)


def git_push(branch: str, remote_name: str = "origin") -> None:
    """Pushes the current branch to the specified remote.

    Args:
        branch (str): The branch to push.
        remote_name (str, optional): The remote name (default: "origin").

    Raises:
        RuntimeError: If push fails.
    """
    logger.info("Pushing to remote %s branch %s", remote_name, branch)
    cmd = ["git", "push"]
    cmd.append(remote_name)
    cmd.append(branch)
    process = subprocess.run(cmd, capture_output=True, check=True)
    if process.returncode != 0:
        logger.error("Failed to push to remote (exit code: %d)", process.returncode)
        raise RuntimeError(f"Failed to push to remote (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}")
    logger.info("Successfully pushed to remote %s branch %s", remote_name, branch)


def get_git_remote_url(remote_name: str = "origin") -> str:
    """Gets the URL of a Git remote.

    Args:
        remote_name (str, optional): The remote name (default: "origin").

    Returns:
        str: The remote URL.

    Raises:
        RuntimeError: If getting the remote URL fails.
    """
    logger.info("Getting git remote url for remote: %s", remote_name)
    cmd = ["git", "remote", "get-url", remote_name]
    process = subprocess.run(cmd, capture_output=True, check=True)
    if process.returncode != 0:
        logger.error("Failed to get remote url (exit code: %d)", process.returncode)
        raise RuntimeError(f"Failed to get remote url (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}")
    logger.info("Remote url: %s", process.stdout.decode("utf-8").strip())
    return process.stdout.decode("utf-8").strip()


def git_set_remote_url(new_url: str, remote_name: str = "origin") -> None:
    """Sets the URL of a Git remote.

    Args:
        new_url (str): The new remote URL.
        remote_name (str, optional): The remote name (default: "origin").

    Raises:
        RuntimeError: If setting the remote URL fails.
    """
    logger.info("Setting git remote url for %s to %s", remote_name, new_url)
    cmd = ["git", "remote", "set-url", remote_name, new_url]
    process = subprocess.run(cmd, capture_output=True, check=True)
    if process.returncode != 0:
        logger.error("Failed to set remote url (exit code: %d)", process.returncode)
        raise RuntimeError(f"Failed to set remote url (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}")
    logger.info("Successfully set remote url for %s to %s", remote_name, new_url)
