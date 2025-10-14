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
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from thc_devops_toolkit.containerization.docker import docker_pull, docker_run_daemon, docker_stop
from thc_devops_toolkit.infrastructure.minio import get_minio_service, minio_makedir, minio_removedir, mirror_dir_to_bucket
from thc_devops_toolkit.observability import THCLoggerHighlightLevel, thc_logger

minio_example_dir = Path(__file__).resolve().parent
minio_full_image_name = "minio/minio:RELEASE.2025-09-07T16-13-09Z-cpuv1"
minio_container_name = "test-minio-server"
minio_server = "0.0.0.0:9000"
access_key = "minioadmin"
secret_key = "minioadmin"


@contextmanager
def run_minio_server(
    access_key: str,
    secret_key: str,
) -> Iterator[None]:
    docker_pull(full_image_name=minio_full_image_name)
    docker_run_daemon(
        full_image_name=minio_full_image_name,
        remove=True,
        container_name=minio_container_name,
        command=["server", "/data"],
        env_vars=[
            f"MINIO_ROOT_USER={access_key}",
            f"MINIO_ROOT_PASSWORD={secret_key}",
        ],
        port_mappings=["9000:9000"],
    )
    time.sleep(10)

    yield

    docker_stop(obj=minio_container_name)


def main() -> None:
    with run_minio_server(access_key=access_key, secret_key=secret_key):
        thc_logger.highlight(THCLoggerHighlightLevel.INFO, "MinIO server is running.")
        minio_ = get_minio_service(
            s3_server=minio_server,
            s3_access_key=access_key,
            s3_secret_key=secret_key,
            secure=False,
        )
        # make bucket
        minio_makedir(
            minio_=minio_,
            bucket="testbk",
        )
        # make directory
        minio_makedir(
            minio_=minio_,
            bucket="testbk",
            directory="testdir",
        )
        # mirror local directory to bucket
        mirror_dir_to_bucket(
            minio_=minio_,
            source=minio_example_dir,
            bucket="testbk",
            directory="testdir",
        )
        # remove directory
        minio_removedir(minio_=minio_, bucket="testbk", directory="testdir")
        # remove bucket
        minio_removedir(
            minio_=minio_,
            bucket="testbk",
        )
    thc_logger.highlight(THCLoggerHighlightLevel.INFO, "MinIO server is stopped.")


if __name__ == "__main__":
    main()
