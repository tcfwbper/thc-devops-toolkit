from dataclasses import dataclass
import logging
import subprocess

@dataclass
class GitCredential:
    user: str
    token: str

def get_pat_format_url(
    git_credential: GitCredential,
    repo_url: str,
    server_protocol: str = "https",
) -> str:
    logging.info("Repository URL: %s", repo_url)
    pat_format_url = f"{server_protocol}://{git_credential.user}:{git_credential.token}@{repo_url}"
    return pat_format_url

def git_clone_repo(
    pat_format_url: str | None = None,
    branch: str = "main",
) -> None:
    cmd = ["git", "clone", "-b",  branch, pat_format_url]
    process = subprocess.Popen(cmd)
    process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"Failed to clone repo (exit code: {process.returncode})")

def git_set_config(
    user: str,
    email: str,
) -> None:
    cmd = ["git", "config", "user.email", email]
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to set git config email: {email} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )
    cmd = ["git", "config", "user.name", user]
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to set git config username: {user} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def git_checkout(branch: str) -> None:
    cmd = ["git", "checkout", "-B", branch]
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to checkout to {branch} (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def git_add_all() -> None:
    cmd = ["git", "add", "."]
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to add changes (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def git_commit(message: str = "default commit message") -> None:
    cmd = ["git", "commit", "-m", message]
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to commit staged changes (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def git_pull(
    rebase: bool,
    branch: str,
    remote_name: str = "origin"
) -> None:
    cmd = ["git", "pull"]
    if rebase:
        cmd.append("--rebase")
    cmd.append(remote_name)
    cmd.append(branch)
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to pull from remote (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def git_push(branch: str, remote_name: str = "origin") -> None:
    cmd = ["git", "push"]
    cmd.append(remote_name)
    cmd.append(branch)
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to push to remote (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )

def get_git_remote_url(remote_name: str = "origin") -> str:
    cmd = ["git", "remote", "get-url", remote_name]
    process = subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to get remote url (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )
    return process.stdout.strip()

def git_set_remote_url(new_url: str, remote_name: str = "origin") -> None:
    cmd = ["git", "remote", "set-url", remote_name, new_url]
    process = subprocess.run(cmd, capture_output=True)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to set remote url (exit code: {process.returncode})\n"
            f"{str(process.stderr, 'UTF-8')}"
        )
