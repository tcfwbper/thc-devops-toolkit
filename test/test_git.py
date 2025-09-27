import pytest
from unittest.mock import patch, MagicMock

from thc_devops_toolkit.version_control import git as git_mod

@pytest.fixture
def git_credential():
    return git_mod.GitCredential(user="testuser", token="testtoken")

def test_get_pat_format_url(git_credential):
    url = git_mod.get_pat_format_url(git_credential, "github.com/org/repo.git")
    assert url.startswith("https://testuser:testtoken@github.com/org/repo.git")

@patch("subprocess.run")
def test_git_clone_repo_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    repo_url = "https://testuser:testtoken@github.com/org/repo.git"
    branch = "main"
    git_mod.git_clone_repo(repo_url, branch=branch)
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    # Check the command is exactly as expected
    assert args[:4] == ["git", "clone", "-b", branch]
    assert args[4] == repo_url

@patch("subprocess.run")
def test_git_clone_repo_fail(mock_run):
    mock_run.return_value = MagicMock(returncode=1)
    with pytest.raises(RuntimeError):
        git_mod.git_clone_repo("https://testuser:testtoken@github.com/org/repo.git")

@patch("subprocess.run")
def test_git_set_config_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    user = "testuser"
    email = "test@example.com"
    git_mod.git_set_config(user, email)
    assert mock_run.call_count == 2
    # Check the first call sets user.email
    args1 = mock_run.call_args_list[0][0][0]
    assert args1 == ["git", "config", "user.email", email]
    # Check the second call sets user.name
    args2 = mock_run.call_args_list[1][0][0]
    assert args2 == ["git", "config", "user.name", user]

@patch("subprocess.run")
def test_git_set_config_fail(mock_run):
    # Fail on email
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        git_mod.git_set_config("testuser", "test@example.com")

@patch("subprocess.run")
def test_git_checkout_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    branch = "feature-branch"
    git_mod.git_checkout(branch)
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    # Check the command is exactly as expected
    assert args[:4] == ["git", "checkout", "-B", branch]

@patch("subprocess.run")
def test_git_checkout_fail(mock_run):
    # Fail on checkout
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        git_mod.git_checkout("feature-branch")

@patch("subprocess.run")
def test_git_add_all_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    git_mod.git_add_all()
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    # Check the command is exactly as expected
    assert args[:3] == ["git", "add", "."]

@patch("subprocess.run")
def test_git_add_all_fail(mock_run):
    # Fail on add
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        git_mod.git_add_all()

@patch("subprocess.run")
def test_git_commit_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    message = "test commit"
    git_mod.git_commit(message)
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    # Check the command is exactly as expected
    assert args[:4] == ["git", "commit", "-m", message]

@patch("subprocess.run")
def test_git_commit_fail(mock_run):
    # Fail on commit
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        git_mod.git_commit("test commit")

@patch("subprocess.run")
def test_git_pull_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    # rebase
    git_mod.git_pull(rebase=True, branch="main")
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    # Check the command is exactly as expected
    assert args[:2] == ["git", "pull"]
    assert args[2:] == ["--rebase", "origin", "main"]
    # not rebase
    mock_run.reset_mock()
    git_mod.git_pull(rebase=False, branch="main")
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    # Check the command is exactly as expected
    assert args[:2] == ["git", "pull"]
    assert args[2:] == ["origin", "main"]
    # branch and remote name
    mock_run.reset_mock()
    branch = "testbranch"
    origin = "testorigin"
    git_mod.git_pull(rebase=True, branch=branch, remote_name=origin)
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    # Check the command is exactly as expected
    assert args[:2] == ["git", "pull"]
    assert args[2:] == ["--rebase", origin, branch]

@patch("subprocess.run")
def test_git_pull_fail(mock_run):
    # Fail on pull
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        git_mod.git_pull(rebase=True, branch="testbranch", remote_name="testorigin")

@patch("subprocess.run")
def test_git_push_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    branch = "testbranch"
    git_mod.git_push(branch=branch)
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    # Check the command is exactly as expected
    assert args[:2] == ["git", "push"]
    assert args[2:] == ["origin", branch]
    # remote name
    mock_run.reset_mock()
    origin = "testorigin"
    git_mod.git_push(branch=branch, remote_name=origin)
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    # Check the command is exactly as expected
    assert args[:2] == ["git", "push"]
    assert args[2:] == [origin, branch]

@patch("subprocess.run")
def test_git_push_fail(mock_run):
    # Fail on push
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        git_mod.git_push(branch="testbranch", remote_name="testorigin")

@patch("subprocess.run")
def test_get_git_remote_url_success(mock_run):
    remote_url = "https://github.com/org/repo.git"
    remote_url_bytes = remote_url.encode('utf-8')
    mock_run.return_value = MagicMock(returncode=0, stdout=remote_url_bytes)
    url = git_mod.get_git_remote_url()
    mock_run.assert_called_once()
    assert url == remote_url
    args = mock_run.call_args[0][0]
    # Check the command is exactly as expected
    assert args == ["git", "remote", "get-url", "origin"]
    # remote name
    mock_run.reset_mock()
    remote_name = "testorigin"
    mock_run.return_value = MagicMock(returncode=0, stdout=remote_url_bytes)
    url = git_mod.get_git_remote_url(remote_name=remote_name)
    mock_run.assert_called_once()
    assert url == remote_url
    args = mock_run.call_args[0][0]
    # Check the command is exactly as expected
    assert args == ["git", "remote", "get-url", remote_name]

@patch("subprocess.run")
def test_get_git_remote_url_fail(mock_run):
    # Fail on get remote url
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        git_mod.get_git_remote_url(remote_name="testorigin")

@patch("subprocess.run")
def test_set_git_remote_url_success(mock_run):
    remote_url = "https://github.com/org/repo.git"
    mock_run.return_value = MagicMock(returncode=0)
    git_mod.set_git_remote_url(remote_url)
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    # Check the command is exactly as expected
    assert args == ["git", "remote", "set-url", "origin", remote_url]
    # remote name
    mock_run.reset_mock()
    remote_name = "testorigin"
    git_mod.set_git_remote_url(remote_url, remote_name=remote_name)
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    # Check the command is exactly as expected
    assert args == ["git", "remote", "set-url", remote_name, remote_url]

@patch("subprocess.run")
def test_set_git_remote_url_fail(mock_run):
    # Fail on set remote url
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        git_mod.set_git_remote_url("https://github.com/org/repo.git", remote_name="testorigin")
