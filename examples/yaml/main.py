# Copyright 2025 Tsung-Han Chang. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
from pathlib import Path

from ruamel.yaml import YAML

from thc_devops_toolkit.utils.yaml import get_value_from_dict, set_value_to_dict

yaml_example_dir = Path(__file__).resolve().parent
yaml_file: str = str(yaml_example_dir / "example.yaml")


def main() -> None:
    yaml = YAML()
    with open(yaml_file) as f:
        data = yaml.load(f)
    get_value_from_dict(data, key_path="foo.bar[0].baz")
    set_value_to_dict(data, key_path="foo.bar[0].baz", value="new value")
    get_value_from_dict(data, key_path="foo.bar[0].baz")

    get_value_from_dict(data, "foo.'complex.key'.baz")
    set_value_to_dict(data, "foo.'complex.key'.baz", "new complex value")
    get_value_from_dict(data, "foo.'complex.key'.baz")

    get_value_from_dict(data, "foo.empty_list")
    set_value_to_dict(data, "foo.empty_list[0]", "first item")
    get_value_from_dict(data, "foo.empty_list")

    get_value_from_dict(data, "foo.nested_array[1][0]")
    set_value_to_dict(data, "foo.nested_array[1][0]", 99)
    get_value_from_dict(data, "foo.nested_array[1][0]")


if __name__ == "__main__":
    main()
