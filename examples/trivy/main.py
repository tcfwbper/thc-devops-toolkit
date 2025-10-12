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

from thc_devops_toolkit.containerization.docker import docker_pull
from thc_devops_toolkit.security.trivy.trivy import trivy_convert, trivy_scan

cr_host = "docker.io"
image_name = "busybox"
image_tag = "latest"

mend_example_dir = Path(__file__).resolve().parent
json_output_file = mend_example_dir / "trivy_output.json"
yaml_output_file = mend_example_dir / "trivy_output.yaml"
html_output_file = mend_example_dir / "trivy_output.html"


def main() -> None:
    docker_pull(full_image_name=f"{cr_host}/{image_name}:{image_tag}")
    trivy_scan(
        cr_host=cr_host,
        image_name=image_name,
        image_tag=image_tag,
        output_file=json_output_file,
    )
    trivy_convert(
        input_path=json_output_file,
        output_path=yaml_output_file,
        template="yaml",
    )
    trivy_convert(
        input_path=json_output_file,
        output_path=html_output_file,
        template="html",
    )


if __name__ == "__main__":
    main()
