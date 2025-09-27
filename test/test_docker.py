import pytest
from unittest.mock import patch, MagicMock
from thc_devops_toolkit.containerization import docker as docker_mod

def _mock_inspect_output():
    return MagicMock(returncode=0, stdout=b'[{"RepoDigests": ["repo@sha256:abcdef1234567890"], "Size": 1234567}]')

@patch("subprocess.run")
def test_docker_login_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    docker_mod.docker_login("docker.io", "user", "pass")
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[:3] == ["docker", "login", "docker.io"]
    assert "--password-stdin" in args

@patch("subprocess.run")
def test_docker_login_fail(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        docker_mod.docker_login("docker.io", "user", "pass")

@patch("subprocess.run")
def test_docker_pull_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    docker_mod.docker_pull("repo/image:tag")
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args == ["docker", "pull", "repo/image:tag"]

@patch("subprocess.run")
def test_docker_pull_fail(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        docker_mod.docker_pull("repo/image:tag")

@patch("subprocess.run")
def test_docker_push_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    docker_mod.docker_push("repo/image:tag")
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args == ["docker", "push", "repo/image:tag"]

@patch("subprocess.run")
def test_docker_push_fail(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        docker_mod.docker_push("repo/image:tag")

@patch("subprocess.run")
def test_docker_inspect_success(mock_run):
    mock_run.return_value = _mock_inspect_output()
    result = docker_mod.docker_inspect("repo/image:tag")
    assert "RepoDigests" in result
    assert "Size" in result

@patch("subprocess.run")
def test_docker_inspect_fail(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        docker_mod.docker_inspect("repo/image:tag")

@patch("subprocess.run")
def test_docker_build_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    docker_mod.docker_build("repo/image:tag", "Dockerfile", [{"key": "ARG1", "value": "val1"}])
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "--build-arg" in args
    assert "-t" in args
    assert "-f" in args
    assert args[-1] == "."

@patch("subprocess.run")
def test_docker_build_fail(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        docker_mod.docker_build("repo/image:tag", "Dockerfile", None)

@patch("subprocess.run")
def test_docker_tag_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    docker_mod.docker_tag("repo/image:tag", "repo/image:newtag")
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args == ["docker", "tag", "repo/image:tag", "repo/image:newtag"]

@patch("subprocess.run")
def test_docker_tag_fail(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        docker_mod.docker_tag("repo/image:tag", "repo/image:newtag")

@patch("subprocess.run")
def test_docker_run_daemon_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout=b"containerid\n")
    cid = docker_mod.docker_run_daemon("repo/image:tag", remove=True, container_name="cname", entrypoint="/bin/sh", command=["echo", "hi"])
    mock_run.assert_called_once()
    assert cid == "containerid"
    args = mock_run.call_args[0][0]
    assert "-d" in args
    assert "--rm" in args
    assert "--name" in args
    assert "--entrypoint" in args
    assert "echo" in args

@patch("subprocess.run")
def test_docker_run_daemon_fail(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        docker_mod.docker_run_daemon("repo/image:tag")

@patch("subprocess.run")
def test_docker_stop_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    docker_mod.docker_stop("cname")
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args == ["docker", "stop", "cname"]

@patch("subprocess.run")
def test_docker_stop_fail(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        docker_mod.docker_stop("cname")

@patch("subprocess.run")
def test_docker_remove_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    docker_mod.docker_remove("cname")
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args == ["docker", "rm", "cname"]

@patch("subprocess.run")
def test_docker_remove_fail(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        docker_mod.docker_remove("cname")
    # ignore_errors True should not raise
    docker_mod.docker_remove("cname", ignore_errors=True)

@patch("subprocess.run")
def test_docker_copy_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    docker_mod.docker_copy("src", "dst")
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args == ["docker", "cp", "src", "dst"]

@patch("subprocess.run")
def test_docker_copy_fail(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        docker_mod.docker_copy("src", "dst")

@patch("subprocess.run")
def test_docker_exec_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout=b"out", stderr=b"")
    docker_mod.docker_exec(command=["ls"], workdir="/app", obj="cname", print_output=True)
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "exec" in args
    assert "-w" in args
    assert "ls" in args

@patch("subprocess.run")
def test_docker_exec_fail(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"fail")
    with pytest.raises(RuntimeError):
        docker_mod.docker_exec(command=["ls"], obj="cname")

@patch("subprocess.run")
def test_docker_exec_no_command(mock_run):
    with pytest.raises(ValueError):
        docker_mod.docker_exec(command=None, obj="cname")

@patch("thc_devops_toolkit.containerization.docker.docker_inspect")
def test_get_image_digest_success(mock_inspect):
    mock_inspect.return_value = {"RepoDigests": ["repo@sha256:abcdef1234567890"]}
    digest = docker_mod.get_image_digest("repo/image:tag", precision=8)
    assert digest == "abcdef12"

@patch("thc_devops_toolkit.containerization.docker.docker_inspect")
def test_get_image_digest_fail(mock_inspect):
    mock_inspect.return_value = {"RepoDigests": []}
    assert docker_mod.get_image_digest("repo/image:tag") == ""
    mock_inspect.return_value = {"RepoDigests": ["repo@sha256:"]}
    assert docker_mod.get_image_digest("repo/image:tag") == ""
    mock_inspect.return_value = {"RepoDigests": ["repo@sha256:123"]}
    assert docker_mod.get_image_digest("repo/image:tag", precision=6) == "123"
    with pytest.raises(ValueError):
        docker_mod.get_image_digest("repo/image:tag", precision=4)

@patch("thc_devops_toolkit.containerization.docker.docker_inspect")
def test_get_image_size_success(mock_inspect):
    mock_inspect.return_value = {"Size": 1234567, "RepoDigests": ["repo@sha256:abcdef1234567890"]}
    size = docker_mod.get_image_size("repo/image:tag")
    assert size.endswith("MB") or size.endswith("KB") or size.endswith("B")

@patch("thc_devops_toolkit.containerization.docker.docker_inspect")
def test_get_image_size_fail(mock_inspect):
    mock_inspect.return_value = {"RepoDigests": ["repo@sha256:abcdef1234567890"]}
    with pytest.raises(KeyError):
        docker_mod.get_image_size("repo/image:tag")
