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
from pathlib import Path

from thc_devops_toolkit.containerization.docker import (
    docker_build,
    docker_copy,
    docker_exec,
    docker_inspect,
    docker_login,
    docker_pull,
    docker_push,
    docker_remove,
    docker_remove_image,
    docker_run_daemon,
    docker_stop,
    docker_tag,
    get_image_digest,
    get_image_size,
)

# Set up a default logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


cr_host = "docker.io"
image_name = "busybox"
image_tag = "latest"
tmp_tag = "tmp"
full_image_name = f"{cr_host}/{image_name}:{image_tag}"
container_name = "my_busybox"

docker_example_dir = main_path = Path(__file__).resolve().parent
dockerfile_path = docker_example_dir / "Dockerfile"


def main() -> None:
    parser = argparse.ArgumentParser(description="Docker example script")
    parser.add_argument("--username", required=True, help="Docker registry username")
    args = parser.parse_args()
    username = args.username
    password = getpass.getpass("Docker registry password: ")
    new_image = f"{cr_host}/{username}/{image_name}:{image_tag}"
    new_image_tmp = f"{cr_host}/{username}/{image_name}:{tmp_tag}"

    docker_login(cr_host=cr_host, username=username, password=password)
    docker_pull(full_image_name=full_image_name)
    logger.info("Image info: %s", docker_inspect(target_object=full_image_name))
    logger.info("Image size: %s", get_image_size(full_image_name=full_image_name))
    logger.info(
        "Image digest: %s",
        get_image_digest(
            full_image_name=full_image_name,
            precision=64,
        ),
    )
    docker_build(
        full_image_name=new_image,
        docker_file_path=dockerfile_path,
        build_args=[{"key": "ARG1", "value": "Hello World!"}],
    )
    docker_tag(source_full_image_name=new_image, target_full_image_name=new_image_tmp)
    docker_remove_image(full_image_name=new_image)
    docker_remove_image(full_image_name=new_image_tmp)
    # docker_push(full_image_name=new_image)
    container_id = docker_run_daemon(
        full_image_name=full_image_name,
        remove=False,
        container_name=container_name,
        entrypoint="sh",
        command=["-c", "sleep infinity"],
    )
    docker_exec(
        command=["echo", "Hello_World!"],
        workdir="/",
        obj=container_id,
        print_output=True,
    )
    docker_copy(
        source=dockerfile_path,
        target=f"{container_name}:/",
    )
    docker_stop(
        obj=container_id,
        timeout=10,
        poll_interval=1,
    )
    docker_remove(
        obj=container_name,
        timeout=10,
        poll_interval=1,
    )


if __name__ == "__main__":
    main()
