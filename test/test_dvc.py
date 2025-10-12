import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thc_devops_toolkit.version_control import dvc as dvc_mod

@pytest.fixture(scope="function")
def tmp_path():
    # before test
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    # after test
    if Path(dir_path).exists():
        shutil.rmtree(dir_path, ignore_errors=True)

@pytest.fixture
def dvc_repo(tmp_path):
    """Create a DvcRepo instance for testing."""
    return dvc_mod.DvcRepo(tmp_path)

def test_dvc_repo_init():
    with patch("thc_devops_toolkit.version_control.dvc.Repo") as repo_cls:
        dvc_repo = dvc_mod.DvcRepo("/tmp/repo")
        dvc_repo.init()
        repo_cls.init.assert_called_once_with("/tmp/repo")

def test_dvc_repo_get_repo():
    with patch("thc_devops_toolkit.version_control.dvc.Repo") as repo_cls:
        dvc_repo = dvc_mod.DvcRepo("/tmp/repo")
        repo = dvc_repo._get_repo()
        repo_cls.assert_called_once_with("/tmp/repo")
        assert repo == repo_cls.return_value

def test_dvc_repo_set_remote():
    repo_mock = MagicMock()
    config_ctx = {"remote": {}}
    repo_mock.config.edit.return_value.__enter__.return_value = config_ctx
    
    with patch("thc_devops_toolkit.version_control.dvc.Repo", return_value=repo_mock):
        dvc_repo = dvc_mod.DvcRepo("/tmp/repo")
        dvc_repo.set_remote("myremote", "/tmp/remote")
        
        repo_mock.config.edit.assert_called_once()
        assert "myremote" in config_ctx["remote"]
        assert config_ctx["remote"]["myremote"]["url"] == "/tmp/remote"

def test_dvc_repo_set_remote_s3():
    repo_mock = MagicMock()
    config_ctx = MagicMock()
    repo_mock.config.edit.return_value.__enter__.return_value = config_ctx
    
    with patch("thc_devops_toolkit.version_control.dvc.Repo", return_value=repo_mock):
        dvc_repo = dvc_mod.DvcRepo("/tmp/repo")
        dvc_repo.set_remote_s3(
            remote_name="myremote",
            s3_server="https://s3.server",
            s3_access_key="ak",
            s3_secret_key="sk",
            s3_bucket="mybk"
        )
        
        repo_mock.config.edit.assert_called_once()

def test_dvc_repo_add_directory():
    repo_mock = MagicMock()
    with patch("thc_devops_toolkit.version_control.dvc.Repo", return_value=repo_mock):
        dvc_repo = dvc_mod.DvcRepo("/tmp/repo")
        dvc_repo.add_directory("data")
        repo_mock.add.assert_called_once()
        args, kwargs = repo_mock.add.call_args
        assert "/tmp/repo/data" in args[0]

def test_dvc_repo_add_files():
    repo_mock = MagicMock()
    with patch("thc_devops_toolkit.version_control.dvc.Repo", return_value=repo_mock):
        dvc_repo = dvc_mod.DvcRepo("/tmp/repo")
        dvc_repo.add_files(["a.txt", "b.txt"])
        repo_mock.add.assert_called_once()
        args, kwargs = repo_mock.add.call_args
        targets = kwargs.get("targets", [])
        assert "/tmp/repo/a.txt" in targets
        assert "/tmp/repo/b.txt" in targets

def test_dvc_repo_push():
    repo_mock = MagicMock()
    with patch("thc_devops_toolkit.version_control.dvc.Repo", return_value=repo_mock):
        dvc_repo = dvc_mod.DvcRepo("/tmp/repo")
        dvc_repo.push("myremote")
        repo_mock.push.assert_called_once_with(remote="myremote")

def test_DvcOutput_from_to_dict():
    d = {"path": "foo.txt", "md5": "abc", "hash": "md5"}
    out = dvc_mod.DvcOutput.from_dict(d)
    assert out.path == "foo.txt"
    assert out.md5 == "abc"
    assert out.hash_type == "md5"
    assert out.to_dict() == {"hash": "md5", "md5": "abc", "path": "foo.txt"}

def test_DvcFile_from_to_dict():
    d = {"outs": [{"path": "foo.txt", "md5": "abc", "hash": "md5"}]}
    f = dvc_mod.DvcFile.from_dict(d)
    assert len(f.outputs) == 1
    assert f.to_dict() == d

def test_DvcTrackedFile_cmp_eq():
    a = dvc_mod.DvcTrackedFile(md5="a", relpath="x")
    b = dvc_mod.DvcTrackedFile(md5="b", relpath="y")
    assert a < b or b < a
    assert a == dvc_mod.DvcTrackedFile(md5="a", relpath="x")

def test_DvcTrackedFiles_add_file():
    files = dvc_mod.DvcTrackedFiles()
    files.add_file("a", "x")
    files.add_file("b", "y")
    assert len(files.files) == 2
    assert files.get_all_md5s() == ["a", "b"]

def test_merge_dvc_files():
    d1 = dvc_mod.DvcFile(outputs=[dvc_mod.DvcOutput("a", "1")])
    d2 = dvc_mod.DvcFile(outputs=[dvc_mod.DvcOutput("b", "2")])
    merged = dvc_mod.merge_dvc_files([d1, d2])
    assert len(merged.outputs) == 2
    assert {o.path for o in merged.outputs} == {"a", "b"}

def test_dvc_repo_get_dvc_file(tmp_path):
    dvc_path = tmp_path / "foo.dvc"
    dvc_path.write_text("outs:\n  - path: foo\n    md5: abc\n    hash: md5\n")
    dvc_repo = dvc_mod.DvcRepo(tmp_path)
    f = dvc_repo.get_dvc_file("foo")
    assert isinstance(f, dvc_mod.DvcFile)
    assert f.outputs[0].path == "foo"

def test_dvc_repo_get_dvc_file_not_found(tmp_path):
    dvc_repo = dvc_mod.DvcRepo(tmp_path)
    with pytest.raises(FileNotFoundError):
        dvc_repo.get_dvc_file("notfound")

def test_dvc_repo_get_dvc_tracked_files(tmp_path):
    # Create cache directory structure
    cache_dir = tmp_path / ".dvc" / "cache" / "files" / "md5" / "ab" 
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test tracked files data
    tracked_file = cache_dir / "cdef123456"
    tracked_file.write_text('[{"md5": "abc", "relpath": "test.txt"}]')
    
    dvc_repo = dvc_mod.DvcRepo(tmp_path)
    output = dvc_mod.DvcOutput(path="foo", md5="abcdef123456")
    tracked_files = dvc_repo.get_dvc_tracked_files(output)
    
    assert isinstance(tracked_files, dvc_mod.DvcTrackedFiles)
    assert len(tracked_files) == 1
    assert tracked_files.files[0].md5 == "abc"
    assert tracked_files.files[0].relpath == "test.txt"

def test_DvcFile_get_output_by_path_and_all_methods(tmp_path):
    dvc_file = dvc_mod.DvcFile(outputs=[
        dvc_mod.DvcOutput("foo.txt", "abc"),
        dvc_mod.DvcOutput("bar.txt", "def"),
    ])
    # get_output_by_path
    assert dvc_file.get_output_by_path("foo.txt").md5 == "abc"
    assert dvc_file.get_output_by_path("notfound") is None
    # get_all_paths
    assert set(dvc_file.get_all_paths()) == {"foo.txt", "bar.txt"}
    # get_all_md5s
    assert set(dvc_file.get_all_md5s()) == {"abc", "def"}
    # to_yaml_file and from_yaml_file
    yaml_path = tmp_path / "test.dvc"
    dvc_file.to_yaml_file(yaml_path)
    loaded = dvc_mod.DvcFile.from_yaml_file(yaml_path)
    assert loaded.to_dict() == dvc_file.to_dict()

def test_DvcTrackedFiles_to_json_and_from_json(tmp_path):
    files = dvc_mod.DvcTrackedFiles()
    files.add_file("a", "x")
    files.add_file("b", "y")
    json_path = tmp_path / "tracked.json"
    files.to_json_file(json_path)
    loaded = dvc_mod.DvcTrackedFiles.from_json_file(json_path)
    assert loaded.get_all_md5s() == ["a", "b"]
    assert loaded.get_all_paths() == ["x", "y"]
    assert len(loaded) == 2
    assert list(iter(loaded))[0].md5 == "a"

def test_DvcTrackedFile_eq_and_lt():
    a = dvc_mod.DvcTrackedFile(md5="a", relpath="x")
    b = dvc_mod.DvcTrackedFile(md5="b", relpath="y")
    assert (a == a)
    assert not (a == b)
    assert (a < b) != (b < a)
    assert not (a == object())

def test_dvc_repo_get_cache_dir(tmp_path):
    dvc_repo = dvc_mod.DvcRepo(tmp_path)
    cache_dir = dvc_repo._get_cache_dir()
    expected_dir = tmp_path / ".dvc" / "cache" / "files" / "md5"
    assert cache_dir == expected_dir
