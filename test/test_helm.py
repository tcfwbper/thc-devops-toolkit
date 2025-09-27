import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from thc_devops_toolkit.containerization import helm as helm_mod

class DummyChart(helm_mod.Chart):
    def __init__(self, name="test", version="1.0.0", path_prefix="/tmp", dependencies=None, check_list=None):
        super().__init__(name, version, path_prefix, dependencies or [], check_list or {})

def test_helm_login_success():
    with patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 0
        helm_mod.helm_login("host", "user", "pass")
        run_mock.assert_called()

def test_helm_login_fail():
    with patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 1
        run_mock.return_value.stderr = b"fail"
        with pytest.raises(RuntimeError):
            helm_mod.helm_login("host", "user", "pass")

def test_helm_pull_success():
    with patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 0
        helm_mod.helm_pull("chart", "1.0.0")
        run_mock.assert_called()

def test_helm_pull_fail():
    with patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 1
        run_mock.return_value.stderr = b"fail"
        with pytest.raises(RuntimeError):
            helm_mod.helm_pull("chart", "1.0.0")

def test_helm_package_success():
    chart = DummyChart()
    with patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 0
        helm_mod.helm_package(chart)
        run_mock.assert_called()

def test_helm_package_fail():
    chart = DummyChart()
    with patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 1
        run_mock.return_value.stderr = b"fail"
        with pytest.raises(RuntimeError):
            helm_mod.helm_package(chart)

def test_helm_push_success():
    chart = DummyChart()
    with patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 0
        helm_mod.helm_push(chart, "repo")
        run_mock.assert_called()

def test_helm_push_fail():
    chart = DummyChart()
    with patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 1
        run_mock.return_value.stderr = b"fail"
        with pytest.raises(RuntimeError):
            helm_mod.helm_push(chart, "repo")

def test_verify_chart_version_match(tmp_path):
    chart_dir = tmp_path / "test"
    chart_dir.mkdir()
    chart_yaml = chart_dir / "Chart.yaml"
    chart_yaml.write_text("version: 1.0.0\n")
    chart = DummyChart(path_prefix=tmp_path, name="test")
    assert helm_mod.verify_chart_version(chart, "1.0.0")

def test_verify_chart_version_mismatch(tmp_path):
    chart_dir = tmp_path / "test"
    chart_dir.mkdir()
    chart_yaml = chart_dir / "Chart.yaml"
    chart_yaml.write_text("version: 2.0.0\n")
    chart = DummyChart(path_prefix=tmp_path, name="test")
    assert not helm_mod.verify_chart_version(chart, "1.0.0")

def test_verify_chart_version_missing(tmp_path):
    chart_dir = tmp_path / "test"
    chart_dir.mkdir()
    chart_yaml = chart_dir / "Chart.yaml"
    chart_yaml.write_text("foo: bar\n")
    chart = DummyChart(path_prefix=tmp_path, name="test")
    assert not helm_mod.verify_chart_version(chart, "1.0.0")

def test_verify_chart_values_match(tmp_path):
    chart_dir = tmp_path / "test"
    chart_dir.mkdir()
    values_yaml = chart_dir / "values.yaml"
    values_yaml.write_text("foo: 1\nbar: 2\n")
    chart = DummyChart(path_prefix=tmp_path, name="test")
    check_list = {"foo": 1, "bar": 2}
    assert helm_mod.verify_chart_values(chart, check_list)

def test_verify_chart_values_mismatch(tmp_path):
    chart_dir = tmp_path / "test"
    chart_dir.mkdir()
    values_yaml = chart_dir / "values.yaml"
    values_yaml.write_text("foo: 1\nbar: 3\n")
    chart = DummyChart(path_prefix=tmp_path, name="test")
    check_list = {"foo": 1, "bar": 2}
    assert not helm_mod.verify_chart_values(chart, check_list)

def test_verify_chart_values_not_found(tmp_path):
    chart_dir = tmp_path / "test"
    chart_dir.mkdir()
    values_yaml = chart_dir / "values.yaml"
    values_yaml.write_text("foo: 1\n")
    chart = DummyChart(path_prefix=tmp_path, name="test")
    check_list = {"bar": 2}
    assert not helm_mod.verify_chart_values(chart, check_list)

def test_verify_chart_values_invalid_checklist(tmp_path):
    chart_dir = tmp_path / "test"
    chart_dir.mkdir()
    values_yaml = chart_dir / "values.yaml"
    values_yaml.write_text("foo: 1\n")
    chart = DummyChart(path_prefix=tmp_path, name="test")
    assert not helm_mod.verify_chart_values(chart, ["foo"])

def test_verify_dependencies_acyclic():
    c1 = DummyChart(name="a", dependencies=["b"])
    c2 = DummyChart(name="b", dependencies=[])
    helm_mod.verify_dependencies([c1, c2])

def test_verify_dependencies_cycle():
    c1 = DummyChart(name="a", dependencies=["b"])
    c2 = DummyChart(name="b", dependencies=["a"])
    with pytest.raises(ValueError):
        helm_mod.verify_dependencies([c1, c2])

def test_verify_dependencies_missing():
    c1 = DummyChart(name="a", dependencies=["b"])
    with pytest.raises(ValueError):
        helm_mod.verify_dependencies([c1])
