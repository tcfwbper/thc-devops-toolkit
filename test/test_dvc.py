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

def test_init_dvc_repo():
    with patch("thc_devops_toolkit.version_control.dvc.Repo") as repo_cls:
        dvc_mod.init_dvc_repo("/tmp/repo")
        repo_cls.init.assert_called_once_with("/tmp/repo")

def test_get_dvc_repo():
    with patch("thc_devops_toolkit.version_control.dvc.Repo") as repo_cls:
        repo = dvc_mod.get_dvc_repo("/tmp/repo")
        repo_cls.assert_called_once_with("/tmp/repo")
        assert repo == repo_cls.return_value

def test_set_dvc_remote_s3():
    repo_mock = MagicMock()
    config_ctx = MagicMock()
    repo_mock.config.edit.return_value.__enter__.return_value = config_ctx
    with patch("thc_devops_toolkit.version_control.dvc.get_dvc_repo", return_value=repo_mock):
        dvc_mod.set_dvc_remote_s3(
            repo_path="/tmp/repo",
            remote_name="myremote",
            s3_server="https://s3.server",
            s3_access_key="ak",
            s3_secret_key="sk",
            s3_bucket="mybk"
        )
        # Check that config_ctx["core"] = {"remote": "myremote"} was set
        config_ctx.__setitem__.assert_any_call("core", {"remote": "myremote"})
        # Check that config_ctx["remote"]["myremote"] = ... was set
        config_ctx.__getitem__.return_value.__setitem__.assert_any_call(
            "myremote",
            {
                "url": "s3://mybk",
                "endpointurl": "https://s3.server",
                "access_key_id": "ak",
                "secret_access_key": "sk",
            },
        )

def test_get_dvc_cache_path(tmp_path):
    md5 = "abcdef1234567890"
    cache_path = dvc_mod.get_dvc_cache_path(tmp_path, md5)
    assert cache_path.parent.exists()
    assert str(cache_path).endswith(md5[2:])

def test_dvc_add_directory():
    repo_mock = MagicMock()
    with patch("thc_devops_toolkit.version_control.dvc.get_dvc_repo", return_value=repo_mock):
        dvc_mod.dvc_add_directory("/tmp/repo", "data")
        repo_mock.add.assert_called_once()
        args, kwargs = repo_mock.add.call_args
        assert "data" in args[0]

def test_dvc_add_files():
    repo_mock = MagicMock()
    with patch("thc_devops_toolkit.version_control.dvc.get_dvc_repo", return_value=repo_mock):
        dvc_mod.dvc_add_files("/tmp/repo", ["a.txt", "b.txt"])
        repo_mock.add.assert_called_once()
        args, kwargs = repo_mock.add.call_args
        targets = kwargs.get("targets", [])
        assert "/tmp/repo/a.txt" in targets
        assert "/tmp/repo/b.txt" in targets
        repo_mock.reset_mock()
        dvc_mod.dvc_add_files(
            repo_path="/tmp/repo",
            files=["a.txt", "b.txt"],
            directory="mydir"
        )
        repo_mock.add.assert_called_once()
        args, kwargs = repo_mock.add.call_args
        targets = kwargs.get("targets", [])
        assert "/tmp/repo/mydir/a.txt" in targets
        assert "/tmp/repo/mydir/b.txt" in targets

def test_dvc_push():
    repo_mock = MagicMock()
    with patch("thc_devops_toolkit.version_control.dvc.get_dvc_repo", return_value=repo_mock):
        dvc_mod.dvc_push("/tmp/repo", "myremote")
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

def test_get_dvc_output_md5_found():
    dvc_file = dvc_mod.DvcFile(outputs=[dvc_mod.DvcOutput("foo", "abc")])
    md5 = dvc_mod.get_dvc_output_md5(dvc_file, "foo")
    assert md5 == "abc"

def test_get_dvc_output_md5_not_found():
    dvc_file = dvc_mod.DvcFile(outputs=[dvc_mod.DvcOutput("foo", "abc")])
    md5 = dvc_mod.get_dvc_output_md5(dvc_file, "bar")
    assert md5 == ""

def test_load_dvc_file(tmp_path):
    dvc_path = tmp_path / "foo.dvc"
    dvc_path.write_text("outs:\n  - path: foo\n    md5: abc\n    hash: md5\n")
    f = dvc_mod.load_dvc_file(dvc_path)
    assert isinstance(f, dvc_mod.DvcFile)
    assert f.outputs[0].path == "foo"

def test_load_dvc_file_not_found(tmp_path):
    dvc_path = tmp_path / "notfound.dvc"
    with pytest.raises(FileNotFoundError):
        dvc_mod.load_dvc_file(dvc_path)

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

def test_dvc_track_directory(tmp_path):
    # Setup
    repo_path = tmp_path
    directory = "mydir"
    tracked = dvc_mod.DvcTrackedFiles()
    tracked.add_file("abc", "file1.txt")
    # Patch get_dvc_cache_path to a writable file
    with patch("thc_devops_toolkit.version_control.dvc.get_dvc_cache_path") as get_cache:
        cache_file = tmp_path / "abc.dir"
        get_cache.return_value = cache_file
        dvc_mod.dvc_track_directory(repo_path, directory, tracked)
        assert cache_file.exists()
        # DVC file should be written
        dvc_file_path = tmp_path / "mydir.dvc"
        assert dvc_file_path.exists()
