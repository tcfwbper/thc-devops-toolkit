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
import argparse
import getpass
import logging
import os
import shutil
from pathlib import Path

from thc_devops_toolkit.containerization.helm import (
    Chart,
    helm_login,
    helm_package,
    helm_pull,
    helm_push,
    verify_chart_values,
    verify_chart_version,
    verify_dependencies,
)

# Set up a default logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


example_cr_host = "docker.io"
remote_chart = "oci://ghcr.io/tcfwbper/helm/devpod"  # public chart
chart_name = "devpod"
chart_version = "1.0.0"
chart_tar_file = f"{chart_name}-{chart_version}.tgz"
common_chart_name = "common"
common_chart_version = "2.31.3"


def main() -> None:
    parser = argparse.ArgumentParser(description="Helm example script")
    parser.add_argument("--username", required=True, help="Docker registry username")
    args = parser.parse_args()
    username = args.username
    remote_chart_private = f"oci://{example_cr_host}/{username}/helm"  # private chart
    password = getpass.getpass("Docker registry password: ")

    cwd = os.getcwd()
    helm_example_dir = Path(__file__).resolve().parent
    os.chdir(helm_example_dir)

    helm_login(example_cr_host, username, password)
    helm_pull(
        remote_chart=remote_chart,
        version=chart_version,
        untar=True,
    )
    devpod = Chart.from_path(
        path_prefix=helm_example_dir,
        name=chart_name,
    )
    common = Chart.from_path(
        path_prefix=helm_example_dir / chart_name / "charts",
        name=common_chart_name,
    )
    verify_chart_version(devpod, expected_chart_version=chart_version)
    verify_chart_version(
        common,
        expected_chart_version=common_chart_version,
    )
    verify_chart_values(
        devpod,
        check_list={
            "image.registry": "docker.io",
            "image.repository": "tcfwbper/dev-env",
        },
    )  # values.yaml contains these key-values?
    verify_dependencies(charts=[devpod, common])  # charts are acyclic?
    helm_package(chart=devpod)
    # helm_push(devpod, repository=remote_chart_private)

    shutil.rmtree(helm_example_dir / chart_name)
    (helm_example_dir / chart_tar_file).unlink(missing_ok=True)
    os.chdir(cwd)


if __name__ == "__main__":
    main()
