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
"""This module provides utility functions and classes for interacting with Git repositories.

Functions include cloning, configuring, committing, pushing, pulling, and managing remotes.
"""

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

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


class GitRepo:
    """Represents a Git repository."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        git_credential: GitCredential,
        email: str,
        repo_url: str,
        local_path: str,
    ) -> None:
        """Initializes a GitRepo instance.

        Args:
            git_credential (GitCredential): The Git credentials.
            email (str): The email to set in Git config.
            repo_url (str): The URL of the Git repository.
            local_path (str): The local path to clone the repository to.
            branch (str, optional): The branch to checkout. Defaults to "main".

        Raises:
            FileExistsError: If the local_path already exists.
        """
        if Path(local_path).is_dir():
            raise FileExistsError(f"Directory {local_path} already exists.")

        self.credential = git_credential
        self.email = email
        self.url = repo_url
        self.local_path = local_path
        self.remotes: dict[str, str] = {}

    def _get_pat_format_url(self, mask_token: bool) -> str:
        """Constructs a repository URL with embedded PAT credentials.

        Args:
            mask_token (bool): Whether to mask the token in the URL.

        Returns:
            str: The repository URL in PAT format.

        Raises:
            ValueError: If the repository URL does not start with http:// or https://.
        """
        http_protocol = "http://"
        https_protocol = "https://"

        if self.url.startswith(http_protocol):
            protocol = http_protocol
        elif self.url.startswith(https_protocol):
            protocol = https_protocol
        else:
            raise ValueError("Repository URL must start with http:// or https://")

        repo_url = self.url.replace("https://", "").replace("http://", "")
        token = "*" * len(self.credential.token) if mask_token else self.credential.token

        return f"{protocol}{self.credential.user}:{token}@{repo_url}"

    def _set_config(self) -> None:
        """Sets the Git user.name and user.email configuration.

        Raises:
            RuntimeError: If setting the config fails.
        """
        logger.info("Setting local git config user.email to %s", self.email)

        cmd = ["git", "config", "--local", "user.email", self.email]
        process = subprocess.run(cmd, cwd=self.local_path, capture_output=True, check=True)

        if process.returncode != 0:
            logger.error("Failed to set git config email: %s (exit code: %d)", self.email, process.returncode)
            raise RuntimeError(
                f"Failed to set git config email: {self.email} (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}"
            )

        logger.info("Setting local git config user.name to %s", self.credential.user)
        cmd = ["git", "config", "--local", "user.name", self.credential.user]

        process = subprocess.run(cmd, cwd=self.local_path, capture_output=True, check=True)
        if process.returncode != 0:
            logger.error("Failed to set git config username: %s (exit code: %d)", self.credential.user, process.returncode)
            raise RuntimeError(
                f"Failed to set git config username: {self.credential.user} "
                f"(exit code: {process.returncode})\n{process.stderr.decode('utf-8')}"
            )

        logger.info("Successfully set local git config for user: %s, email: %s", self.credential.user, self.email)

    def _get_remotes(self) -> None:
        """Retrieves the Git remotes and their URLs.

        Raises:
            RuntimeError: If getting the remotes fails.
        """
        logger.info("Getting git remotes")
        cmd = ["git", "remote", "-v"]
        process = subprocess.run(
            cmd,
            cwd=self.local_path,
            capture_output=True,
            text=True,
            check=True,
        )

        if process.returncode != 0:
            logger.error("Failed to get git remotes (exit code: %d)", process.returncode)
            raise RuntimeError(f"Failed to get git remotes (exit code: {process.returncode})\n{process.stderr}")

        for remote_info in process.stdout.strip().splitlines():
            parts = remote_info.split()
            if len(parts) >= 2:
                name, url = parts[0], parts[1]
                self.remotes[name] = url

        logger.info("Successfully got git remotes")

    def init(self) -> None:
        """Initializes a new Git repository at the local path.

        Raises:
            RuntimeError: If git init fails.
        """
        logger.info("Initializing new git repo at %s", self.local_path)

        repo_path = Path(self.local_path)
        if not repo_path.is_dir():
            repo_path.mkdir(parents=True)

        cmd = ["git", "init"]
        process = subprocess.run(cmd, cwd=self.local_path, capture_output=True, check=True)

        if process.returncode != 0:
            logger.error("Failed to initialize git repo (exit code: %d)", process.returncode)
            raise RuntimeError(f"Failed to initialize git repo (exit code: {process.returncode})")

        self._set_config()
        logger.info("Successfully initialized git repo at %s", self.local_path)

    def clone(self, branch: str = "main") -> None:
        """Clones a Git repository using the provided PAT format URL and branch.

        Args:
            branch (str, optional): The branch to checkout. Defaults to "main".

        Raises:
            RuntimeError: If the clone operation fails.
            ValueError: If the repository URL is invalid.
        """
        try:
            masked_pat_format_url = self._get_pat_format_url(mask_token=True)
            pat_format_url = self._get_pat_format_url(mask_token=False)
        except ValueError as exception:
            logger.error("Error in repository URL: %s", exception)
            raise

        logger.info("Cloning repo from %s on branch %s to %s", masked_pat_format_url, branch, self.local_path)

        cmd = ["git", "clone", "-b", branch, pat_format_url, self.local_path]
        process = subprocess.run(cmd, capture_output=True, check=True)

        if process.returncode != 0:
            logger.error("Failed to clone repo (exit code: %d)", process.returncode)
            raise RuntimeError(f"Failed to clone repo (exit code: {process.returncode})")

        self._set_config()
        self._get_remotes()
        logger.info("Successfully cloned repo from %s", masked_pat_format_url)

    def get_remote_url(self, mask_token: bool, remote_name: str = "origin") -> str:
        """Gets the URL of a Git remote.

        Args:
            mask_token (bool): Whether to mask the token in the URL.
            remote_name (str, optional): The remote name (default: "origin").

        Returns:
            str: The remote URL, or an empty string if the remote does not exist.
        """
        if remote_name not in self.remotes:
            return ""

        if mask_token:
            return self.remotes[remote_name].replace(self.credential.token, "*" * len(self.credential.token))
        return self.remotes[remote_name]

    def set_remote_url(self, new_url: str, remote_name: str = "origin") -> None:
        """Sets the URL of a Git remote.

        Args:
            new_url (str): The new remote URL.
            remote_name (str, optional): The remote name (default: "origin").

        Raises:
            RuntimeError: If setting the remote URL fails.
        """
        logger.info("Setting git remote url for %s to %s", remote_name, new_url)

        cmd = ["git", "remote", "set-url", remote_name, new_url]
        process = subprocess.run(cmd, cwd=self.local_path, capture_output=True, check=True)

        if process.returncode != 0:
            logger.error("Failed to set remote url (exit code: %d)", process.returncode)
            raise RuntimeError(f"Failed to set remote url (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}")

        self.remotes[remote_name] = new_url
        logger.info("Successfully set remote url for %s to %s", remote_name, new_url)

    def checkout(self, ref: str, new_branch: bool) -> None:
        """Checks out a specific commit or branch.

        Args:
            ref (str): The commit reference (SHA or branch name) to checkout.
            new_branch (bool): Whether to create a new branch.

        Raises:
            RuntimeError: If checkout fails.
        """
        logger.info("Checking out ref: %s", ref)

        cmd = ["git", "checkout"]
        if new_branch:
            cmd.append("-B")
        cmd.append(ref)
        process = subprocess.run(cmd, cwd=self.local_path, capture_output=True, check=True)

        if process.returncode != 0:
            logger.error("Failed to checkout to %s (exit code: %d)", ref, process.returncode)
            raise RuntimeError(f"Failed to checkout to {ref} (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}")

        logger.info("Successfully checked out ref: %s", ref)

    def add_all(self) -> None:
        """Adds all changes to the Git staging area.

        Raises:
            RuntimeError: If adding changes fails.
        """
        logger.info("Adding all changes to git staging area")

        cmd = ["git", "add", "."]
        process = subprocess.run(cmd, cwd=self.local_path, capture_output=True, check=True)

        if process.returncode != 0:
            logger.error("Failed to add changes (exit code: %d)", process.returncode)
            raise RuntimeError(f"Failed to add changes (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}")

        logger.info("Successfully added all changes to staging area")

    def commit(self, message: str = "default commit message") -> None:
        """Commits staged changes with a commit message.

        Args:
            message (str, optional): The commit message (default: "default commit message").

        Raises:
            RuntimeError: If commit fails.
        """
        logger.info("Committing with message: %s", message)

        cmd = ["git", "commit", "-m", message]
        process = subprocess.run(cmd, cwd=self.local_path, capture_output=True, check=True)

        if process.returncode != 0:
            logger.error("Failed to commit staged changes (exit code: %d)", process.returncode)
            raise RuntimeError(f"Failed to commit staged changes (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}")

        logger.info("Successfully committed changes")

    def pull(self, rebase: bool, branch: str, remote_name: str = "origin") -> None:
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
        process = subprocess.run(cmd, cwd=self.local_path, capture_output=True, check=True)

        if process.returncode != 0:
            logger.error("Failed to pull from remote (exit code: %d)", process.returncode)
            raise RuntimeError(f"Failed to pull from remote (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}")

        logger.info("Successfully pulled from remote %s branch %s", remote_name, branch)

    def push(self, branch: str, remote_name: str = "origin") -> None:
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
        process = subprocess.run(cmd, cwd=self.local_path, capture_output=True, check=True)

        if process.returncode != 0:
            logger.error("Failed to push to remote (exit code: %d)", process.returncode)
            raise RuntimeError(f"Failed to push to remote (exit code: {process.returncode})\n{process.stderr.decode('utf-8')}")

        logger.info("Successfully pushed to remote %s branch %s", remote_name, branch)
