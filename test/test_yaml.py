import pytest

from thc_devops_toolkit.utils import yaml as yaml_mod

@pytest.mark.parametrize(
    "key_path,expected",
    [
        ("foo.bar", ["foo", "bar"]),
        ("foo.bar[0]", ["foo", "bar", 0]),
        ("foo.bar[0].baz", ["foo", "bar", 0, "baz"]),
        ("foo.'complex.key'.baz", ["foo", "complex.key", "baz"]),
        ('foo."another.key"[2]', ["foo", "another.key", 2]),
        ("foo.bar[10][2]", ["foo", "bar", 10, 2]),
        ("foo..bar", ["foo", "bar"]),
    ],
)
def test_parse_key_path(key_path, expected):
    assert yaml_mod.parse_key_path(key_path) == expected

@pytest.fixture
def nested_dict():
    return {
        "foo": {
            "bar": [
                {"baz": 1},
                {"baz": 2},
            ],
            "simple": 42,
            "complex.key": {"baz": 99},
            "another.key": [0, 1, 2],
        }
    }

def test_get_value_from_dict_simple(nested_dict):
    val, ok = yaml_mod.get_value_from_dict(nested_dict, "foo.simple")
    assert ok
    assert val == 42

def test_get_value_from_dict_nested(nested_dict):
    val, ok = yaml_mod.get_value_from_dict(nested_dict, "foo.bar[1].baz")
    assert ok
    assert val == 2

def test_get_value_from_dict_quoted_key(nested_dict):
    val, ok = yaml_mod.get_value_from_dict(nested_dict, "foo.'complex.key'.baz")
    assert ok
    assert val == 99

def test_get_value_from_dict_double_quoted_key(nested_dict):
    val, ok = yaml_mod.get_value_from_dict(nested_dict, 'foo."another.key"[2]')
    assert ok
    assert val == 2

def test_get_value_from_dict_not_found(nested_dict):
    val, ok = yaml_mod.get_value_from_dict(nested_dict, "foo.notfound")
    assert not ok
    assert val is None

def test_set_value_to_dict_simple(nested_dict):
    yaml_mod.set_value_to_dict(nested_dict, "foo.simple", 100)
    assert nested_dict["foo"]["simple"] == 100

def test_set_value_to_dict_nested(nested_dict):
    yaml_mod.set_value_to_dict(nested_dict, "foo.bar", [{"baz": 10}])
    assert nested_dict["foo"]["bar"] == [{"baz": 10}]
