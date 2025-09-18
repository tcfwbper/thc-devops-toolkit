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
"""Utilities for interacting with MinIO object storage."""

import logging
from io import BytesIO
from pathlib import Path

from minio import Minio, S3Error


def get_minio_service(
    s3_server: str,
    s3_access_key: str,
    s3_secret_key: str,
    secure: bool = True,
) -> Minio:
    """Connects to the S3 server.

    Args:
        s3_server (str): The S3 server URL.
        s3_access_key (str): The access key.
        s3_secret_key (str): The secret key.
        secure (bool, optional): Use HTTPS if True, HTTP if False. Defaults to True

    Returns:
        Minio: The MinIO client instance.
    """
    endpoint = s3_server.replace("http://", "").replace("https://", "")
    return Minio(
        endpoint=endpoint,
        access_key=s3_access_key,
        secret_key=s3_secret_key,
        secure=secure,
    )


def minio_makedir(minio_: Minio, bucket: str, directory: str | Path | None = None) -> None:
    """Creates a bucket and optionally a directory inside it.

    Args:
        minio_ (Minio): The MinIO client instance.
        bucket (str): The bucket name.
        directory (str | Path | None, optional): Directory to create.
    """
    if not minio_.bucket_exists(bucket):
        minio_.make_bucket(bucket)
    if directory:
        dir_path = str(directory) + "/"
        try:
            minio_.stat_object(bucket, dir_path)
        except S3Error:
            # Directory doesn't exist, create it
            logging.debug(
                "Creating directory %s in bucket %s",
                dir_path,
                bucket,
            )
            minio_.put_object(bucket, dir_path, BytesIO(b""), 0)


def minio_removedir(minio_: Minio, bucket: str, directory: str | Path | None = None) -> None:
    """Removes a directory or bucket from S3.

    Args:
        minio_ (Minio): The MinIO client instance.
        bucket (str): The bucket name.
        directory (str | Path | None, optional): Directory to remove.
            If None, removes the bucket. Defaults to None.
    """
    prefix = str(directory) + "/" if directory else None
    if minio_.bucket_exists(bucket):
        objs = minio_.list_objects(bucket_name=bucket, prefix=prefix, recursive=True)
        for obj in objs:
            minio_.remove_object(bucket, obj.object_name)
    if directory is None:
        minio_.remove_bucket(bucket)


def mirror_dir_to_bucket(
    minio_: Minio,
    source: str | Path,
    bucket: str,
    directory: str | Path | None = None,
) -> None:
    """Mirrors a local directory to a S3 bucket.

    Args:
        minio_ (Minio): The MinIO client instance.
        source (str | Path): Source directory path.
        bucket (str): Bucket name.
        directory (str | Path | None, optional): Target directory in bucket.
            Defaults to None.

    Raises:
        ValueError: If the bucket does not exist.
    """
    if not minio_.bucket_exists(bucket):
        raise ValueError(f"Bucket '{bucket}' does not exist")
    source = Path(source)
    directory = Path(directory) if directory else None
    for file_path in source.rglob("*"):
        if file_path.is_file():
            if directory:
                object_name = str(directory / file_path.relative_to(source))
            else:
                object_name = str(file_path.relative_to(source))
            minio_.fput_object(bucket, object_name, str(file_path))
