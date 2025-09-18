import shutil
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from minio.error import S3Error

from thc_devops_toolkit.infrastructure import minio as minio_mod

@pytest.fixture(scope="function")
def temp_dir():
    # before test
    dir_path = tempfile.mkdtemp()
    yield dir_path
    # after test
    if Path(dir_path).exists():
        shutil.rmtree(dir_path, ignore_errors=True)

def test_get_minio_service():
    with patch("thc_devops_toolkit.infrastructure.minio.Minio") as minio_cls:
        minio_mod.get_minio_service(
            "https://s3.server.com",
            "access_key",
            "secret_key",
            secure=True
        )
        minio_cls.assert_called_once()
        kwargs = minio_cls.call_args.kwargs
        assert "endpoint" in kwargs
        assert "https://" not in kwargs["endpoint"]
        assert "http://" not in kwargs["endpoint"]

def test_minio_makedir_bucket_and_dir():
    minio_ = MagicMock()
    minio_.bucket_exists.return_value = False
    minio_.stat_object.side_effect = S3Error("NoSuchKey", "msg", "req", "host", "id", "response")
    minio_mod.minio_makedir(minio_, "mybk", "mydir")
    minio_.make_bucket.assert_called_once_with("mybk")
    minio_.put_object.assert_called_once()
    args, kwargs = minio_.put_object.call_args
    assert args[0] == "mybk"
    assert args[1] == "mydir/"
    assert isinstance(args[2], BytesIO)
    assert args[3] == 0

def test_minio_makedir_bucket_exists_dir_exists():
    minio_ = MagicMock()
    minio_.bucket_exists.return_value = True
    minio_.stat_object.return_value = True
    minio_mod.minio_makedir(minio_, "mybk", "mydir")
    minio_.make_bucket.assert_not_called()
    minio_.put_object.assert_not_called()

def test_minio_makedir_bucket_exists_dir_not_exists():
    minio_ = MagicMock()
    minio_.bucket_exists.return_value = True
    minio_.stat_object.side_effect = S3Error("NoSuchKey", "msg", "req", "host", "id", "response")
    minio_mod.minio_makedir(minio_, "mybk", "mydir")
    minio_.make_bucket.assert_not_called()
    minio_.put_object.assert_called_once()

def test_minio_makedir_only_bucket():
    minio_ = MagicMock()
    minio_.bucket_exists.return_value = False
    minio_mod.minio_makedir(minio_, "mybk")
    minio_.make_bucket.assert_called_once_with("mybk")
    minio_.stat_object.assert_not_called()
    minio_.put_object.assert_not_called()

def test_minio_removedir_remove_dir():
    minio_ = MagicMock()
    minio_.bucket_exists.return_value = True
    obj1 = MagicMock()
    obj1.object_name = "mydir/file1"
    obj2 = MagicMock()
    obj2.object_name = "mydir/file2"
    minio_.list_objects.return_value = [obj1, obj2]
    minio_mod.minio_removedir(minio_, "mybk", "mydir")
    minio_.remove_object.assert_any_call("mybk", "mydir/file1")
    minio_.remove_object.assert_any_call("mybk", "mydir/file2")
    minio_.remove_bucket.assert_not_called()

def test_minio_removedir_remove_bucket():
    minio_ = MagicMock()
    minio_.bucket_exists.return_value = True
    minio_.list_objects.return_value = []
    minio_mod.minio_removedir(minio_, "mybk")
    minio_.remove_bucket.assert_called_once_with("mybk")

def test_mirror_dir_to_bucket_success(temp_dir):
    minio_ = MagicMock()
    minio_.bucket_exists.return_value = True

    source = Path(temp_dir)
    file1 = source / "a.txt"
    file1.write_text("hello")
    file2 = source / "b.txt"
    file2.write_text("world")

    minio_mod.mirror_dir_to_bucket(minio_, source, "mybk")

    calls = [
        ("mybk", "a.txt", str(file1)),
        ("mybk", "b.txt", str(file2)),
    ]
    actual_calls = [call[0] for call in minio_.fput_object.call_args_list]
    assert set(actual_calls) == set(calls)

def test_mirror_dir_to_bucket_with_directory(temp_dir):
    minio_ = MagicMock()
    minio_.bucket_exists.return_value = True

    source = Path(temp_dir)
    file1 = source / "a.txt"
    file1.write_text("hello")
    
    minio_mod.mirror_dir_to_bucket(minio_, source, "mybk", "mydir")
    minio_.fput_object.assert_called_once()
    args = minio_.fput_object.call_args[0]
    assert args[0] == "mybk"
    assert args[1] == "mydir/a.txt"
    assert args[2] == str(file1)

def test_mirror_dir_to_bucket_bucket_not_exist(temp_dir):
    minio_ = MagicMock()
    minio_.bucket_exists.return_value = False

    source = Path(temp_dir)

    with pytest.raises(ValueError):
        minio_mod.mirror_dir_to_bucket(minio_, source, "mybk")
