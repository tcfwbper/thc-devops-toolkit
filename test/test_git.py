import pytest
from unittest.mock import patch, MagicMock
from thc_devops_toolkit.version_control.git import GitRepo, GitCredential

@pytest.fixture
def git_credential():
    return GitCredential(user="testuser", token="testtoken")

@pytest.fixture
def repo_url():
    return "https://github.com/org/repo.git"

@pytest.fixture
def local_path(tmp_path):
    # Use a temporary path for local repo
    return str(tmp_path / "repo")

@pytest.fixture
def email():
    return "test@example.com"

@pytest.fixture
def git_repo(git_credential, email, repo_url, local_path):
    return GitRepo(git_credential, email, repo_url, local_path)

# Test _get_pat_format_url
def test_get_pat_format_url_masked(git_repo):
    url = git_repo._get_pat_format_url(mask_token=True)
    assert url.startswith("https://testuser:")
    assert "*" in url

def test_get_pat_format_url_unmasked(git_repo):
    url = git_repo._get_pat_format_url(mask_token=False)
    assert url.startswith("https://testuser:testtoken@github.com/org/repo.git")

# Test clone
@patch("subprocess.run")
def test_clone_success(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=0)
    # Patch _set_config and _get_remotes to avoid side effects
    with patch.object(GitRepo, "_set_config"), patch.object(GitRepo, "_get_remotes"):
        git_repo.clone(branch="main")
    args = mock_run.call_args[0][0]
    assert args[:4] == ["git", "clone", "-b", "main"]
    assert args[4].startswith("https://testuser:testtoken@github.com/org/repo.git")

@patch("subprocess.run")
def test_clone_fail(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=1)
    with patch.object(GitRepo, "_set_config"), patch.object(GitRepo, "_get_remotes"):
        with pytest.raises(RuntimeError):
            git_repo.clone(branch="main")

# Test _set_config
@patch("subprocess.run")
def test_set_config_success(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=0)
    git_repo.local_path = "."  # Use current dir for test
    git_repo._set_config()
    assert mock_run.call_count == 2
    args1 = mock_run.call_args_list[0][0][0]
    assert args1 == ["git", "config", "--local", "user.email", git_repo.email]
    args2 = mock_run.call_args_list[1][0][0]
    assert args2 == ["git", "config", "--local", "user.name", git_repo.credential.user]

@patch("subprocess.run")
def test_set_config_fail(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    git_repo.local_path = "."
    with pytest.raises(RuntimeError):
        git_repo._set_config()

# Test _get_remotes
@patch("subprocess.run")
def test_get_remotes_success(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=0, stdout="origin https://github.com/org/repo.git (fetch)\norigin https://github.com/org/repo.git (push)\n")
    git_repo.local_path = "."
    git_repo._get_remotes()
    assert "origin" in git_repo.remotes
    assert git_repo.remotes["origin"].startswith("https://github.com/org/repo.git")

@patch("subprocess.run")
def test_get_remotes_fail(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=1, stderr="fail")
    git_repo.local_path = "."
    with pytest.raises(RuntimeError):
        git_repo._get_remotes()

# Test get_remote_url
def test_get_remote_url_masked(git_repo):
    git_repo.remotes["origin"] = "https://testuser:testtoken@github.com/org/repo.git"
    url = git_repo.get_remote_url(mask_token=True)
    assert "*" in url

def test_get_remote_url_unmasked(git_repo):
    git_repo.remotes["origin"] = "https://testuser:testtoken@github.com/org/repo.git"
    url = git_repo.get_remote_url(mask_token=False)
    assert url == "https://testuser:testtoken@github.com/org/repo.git"

def test_get_remote_url_missing(git_repo):
    url = git_repo.get_remote_url(mask_token=False, remote_name="notfound")
    assert url == ""

# Test set_remote_url
@patch("subprocess.run")
def test_set_remote_url_success(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=0)
    git_repo.local_path = "."
    new_url = "https://github.com/org/repo.git"
    git_repo.set_remote_url(new_url)
    assert git_repo.remotes["origin"] == new_url
    args = mock_run.call_args[0][0]
    assert args == ["git", "remote", "set-url", "origin", new_url]

@patch("subprocess.run")
def test_set_remote_url_fail(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    git_repo.local_path = "."
    with pytest.raises(RuntimeError):
        git_repo.set_remote_url("https://github.com/org/repo.git")

# Test checkout
@patch("subprocess.run")
def test_checkout_success(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=0)
    git_repo.local_path = "."
    git_repo.checkout("feature-branch", new_branch=True)
    args = mock_run.call_args[0][0]
    assert args[:3] == ["git", "checkout", "-B"]
    assert args[3] == "feature-branch"

@patch("subprocess.run")
def test_checkout_fail(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    git_repo.local_path = "."
    with pytest.raises(RuntimeError):
        git_repo.checkout("feature-branch", new_branch=True)

# Test add_all
@patch("subprocess.run")
def test_add_all_success(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=0)
    git_repo.local_path = "."
    git_repo.add_all()
    args = mock_run.call_args[0][0]
    assert args == ["git", "add", "."]

@patch("subprocess.run")
def test_add_all_fail(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    git_repo.local_path = "."
    with pytest.raises(RuntimeError):
        git_repo.add_all()

# Test commit
@patch("subprocess.run")
def test_commit_success(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=0)
    git_repo.local_path = "."
    git_repo.commit(message="test commit")
    args = mock_run.call_args[0][0]
    assert args == ["git", "commit", "-m", "test commit"]

@patch("subprocess.run")
def test_commit_fail(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    git_repo.local_path = "."
    with pytest.raises(RuntimeError):
        git_repo.commit(message="test commit")

# Test pull
@patch("subprocess.run")
def test_pull_success(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=0)
    git_repo.local_path = "."
    git_repo.pull(rebase=True, branch="main")
    args = mock_run.call_args[0][0]
    assert args == ["git", "pull", "--rebase", "origin", "main"]
    mock_run.reset_mock()
    git_repo.pull(rebase=False, branch="main")
    args = mock_run.call_args[0][0]
    assert args == ["git", "pull", "origin", "main"]
    mock_run.reset_mock()
    git_repo.pull(rebase=True, branch="dev", remote_name="upstream")
    args = mock_run.call_args[0][0]
    assert args == ["git", "pull", "--rebase", "upstream", "dev"]

@patch("subprocess.run")
def test_pull_fail(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    git_repo.local_path = "."
    with pytest.raises(RuntimeError):
        git_repo.pull(rebase=True, branch="main")

# Test push
@patch("subprocess.run")
def test_push_success(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=0)
    git_repo.local_path = "."
    git_repo.push(branch="main")
    args = mock_run.call_args[0][0]
    assert args == ["git", "push", "origin", "main"]
    mock_run.reset_mock()
    git_repo.push(branch="dev", remote_name="upstream")
    args = mock_run.call_args[0][0]
    assert args == ["git", "push", "upstream", "dev"]

@patch("subprocess.run")
def test_push_fail(mock_run, git_repo):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    git_repo.local_path = "."
    with pytest.raises(RuntimeError):
        git_repo.push(branch="main")

@patch("subprocess.run")
def test_init_success(mock_run, git_credential, email, repo_url, tmp_path):
    mock_run.return_value = MagicMock(returncode=0)
    local_path = str(tmp_path / "repo")
    repo = GitRepo(git_credential, email, repo_url, local_path)
    with patch.object(GitRepo, "_set_config") as mock_set_config:
        repo.init()
        mock_set_config.assert_called_once()
    args = mock_run.call_args_list[0][0][0]
    assert args == ["git", "init"]

@patch("subprocess.run")
def test_init_fail(mock_run, git_credential, email, repo_url, tmp_path):
    mock_run.return_value = MagicMock(returncode=1)
    local_path = str(tmp_path / "repo")
    repo = GitRepo(git_credential, email, repo_url, local_path)
    with pytest.raises(RuntimeError):
        repo.init()
