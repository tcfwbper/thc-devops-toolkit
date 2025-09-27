import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil
import tempfile

import thc_devops_toolkit.security.trivy.trivy as trivy_mod

@pytest.fixture(scope="function")
def tmp_path():
    # before test
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    # after test
    if Path(dir_path).exists():
        shutil.rmtree(dir_path, ignore_errors=True)

def test_get_trivy_tpl_found():
    with patch("importlib.resources.files") as files_mock:
        tpl_path = MagicMock()
        tpl_path.is_file.return_value = True
        files_mock.return_value.__truediv__.return_value = tpl_path
        result = trivy_mod.get_trivy_tpl("foo.tpl")
        assert result.startswith("@")

def test_get_trivy_tpl_not_found():
    with patch("importlib.resources.files") as files_mock:
        tpl_path = MagicMock()
        tpl_path.is_file.return_value = False
        files_mock.return_value.__truediv__.return_value = tpl_path
        with pytest.raises(FileNotFoundError):
            trivy_mod.get_trivy_tpl("foo.tpl")

def test_trivy_scan_success(tmp_path):
    with patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 0
        cr_host = "host"
        image_name = "busybox"
        image_tag = "latest"
        output_file = tmp_path / "out"
        trivy_mod.trivy_scan(
            cr_host=cr_host,
            image_name=image_name,
            image_tag=image_tag,
            output_file=output_file
        )
        run_mock.assert_called_once()
        args = run_mock.call_args[0][0]
        assert args == [
            "trivy",
            "image",
            "--timeout",
            "60m",
            "--format",
            "json",
            "-o",
            str(output_file.with_suffix(".json")),
            f"{cr_host}/{image_name}:{image_tag}"
        ]

def test_trivy_scan_failure(tmp_path):
    with patch("subprocess.run") as run_mock:
        proc = MagicMock()
        cr_host = "host"
        image_name = "busybox"
        image_tag = "latest"
        output_file = tmp_path / "out"
        proc.returncode = 1
        proc.stderr = b"fail"
        run_mock.return_value = proc
        with pytest.raises(RuntimeError):
            trivy_mod.trivy_scan(
                cr_host=cr_host,
                image_name=image_name,
                image_tag=image_tag,
                output_file=output_file
            )

def test_trivy_convert_success():
    input_path = "in.json"
    output_path = "out.yaml"
    template_path = "@/some/path.tpl"
    template = "yaml"
    template_filename = template + ".tpl"
    with patch(
        "subprocess.run"
    ) as run_mock, patch(
        "thc_devops_toolkit.security.trivy.trivy.get_trivy_tpl"
    ) as tpl_mock:
        run_mock.return_value.returncode = 0
        tpl_mock.return_value = template_path
        trivy_mod.trivy_convert(
            input_path=input_path,
            output_path=output_path,
            template=template
        )
        tpl_mock.assert_called_once_with(template_filename)
        run_mock.assert_called_once()
        args = run_mock.call_args[0][0]
        assert args == [
            "trivy",
            "convert",
            "--format",
            "template",
            "--template",
            template_path,
            "-o",
            output_path,
            input_path
        ]

def test_trivy_convert_template_not_found():
    input_path = "in.json"
    output_path = "out.yaml"
    template = "yaml"
    with patch("thc_devops_toolkit.security.trivy.trivy.get_trivy_tpl", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            trivy_mod.trivy_convert(
                input_path=input_path,
                output_path=output_path,
                template=template
            )

def test_trivy_convert_failure():
    with patch(
        "subprocess.run"
    ) as run_mock, patch(
        "thc_devops_toolkit.security.trivy.trivy.get_trivy_tpl"
    ) as tpl_mock:
        proc = MagicMock()
        proc.returncode = 1
        proc.stderr = b"fail"
        run_mock.return_value = proc
        tpl_mock.return_value = "@/some/path.tpl"
        with pytest.raises(RuntimeError):
            trivy_mod.trivy_convert("in.json", "out.txt", "tpl")
