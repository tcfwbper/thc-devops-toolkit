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
"""A collection of utilities for DVC version control tasks."""
import bisect
import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from dvc.repo import Repo

from thc_devops_toolkit.observability import LogLevel, logger


@dataclass
class DvcOutput:
    """DVC output file information."""

    path: str
    md5: str
    hash_type: str = "md5"

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "DvcOutput":
        """Create DvcOutput from a dictionary.

        Args:
            data (dict[str, str]): Dictionary containing output information.

        Returns:
            DvcOutput: The created DvcOutput instance.
        """
        return cls(path=data["path"], md5=data["md5"], hash_type=data.get("hash", "md5"))

    def to_dict(self) -> dict[str, str]:
        """Convert the DvcOutput to a dictionary.

        Returns:
            dict[str, str]: Dictionary representation of the output.
        """
        return {"hash": self.hash_type, "md5": self.md5, "path": self.path}


@dataclass
class DvcFile:
    """DVC file representation."""

    outputs: list[DvcOutput] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, list[dict[str, str]]]) -> "DvcFile":
        """Create DvcFile from a dictionary.

        Args:
            data (dict[str, list[dict[str, str]]]): Dictionary containing DVC file data.

        Returns:
            DvcFile: The created DvcFile instance.
        """
        outputs = [DvcOutput.from_dict(out) for out in data.get("outs", [])]
        return cls(outputs=outputs)

    @classmethod
    def from_yaml_file(cls, file_path: str | Path) -> "DvcFile":
        """Load a DVC file from a YAML file.

        Args:
            file_path (str | Path): Path to the YAML file.

        Returns:
            DvcFile: The loaded DvcFile instance.

        Raises:
            FileNotFoundError: If the specified file does not exist.
        """
        file_path = Path(file_path)

        if not file_path.is_file():
            raise FileNotFoundError(f"DVC file not found: {file_path}")

        with file_path.open("r", encoding="utf-8") as file:
            data = yaml.load(file, Loader=yaml.FullLoader)

        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert the DvcFile to a dictionary.

        Returns:
            dict[str, Any]: Dictionary representation of the DvcFile.
        """
        return {"outs": [output.to_dict() for output in self.outputs]}

    def to_yaml_file(self, file_path: str | Path) -> None:
        """Save the DvcFile to a YAML file.

        Args:
            file_path (str | Path): Path to the YAML file.
        """
        file_path = Path(file_path)
        with file_path.open("w", encoding="utf-8") as file:
            yaml.dump(self.to_dict(), file, default_flow_style=False)

    def get_output_by_path(self, path: str | Path) -> DvcOutput | None:
        """Find an output by its path.

        Args:
            path (str | Path): The path to search for.

        Returns:
            DvcOutput | None: The matching DvcOutput, or None if not found.
        """
        path = str(path)
        for output in self.outputs:
            if output.path == path:
                return output
        return None

    def get_all_paths(self) -> list[str]:
        """Get all output paths.

        Returns:
            list[str]: List of all output paths.
        """
        return [output.path for output in self.outputs]

    def get_all_md5s(self) -> list[str]:
        """Get all MD5 hashes.

        Returns:
            list[str]: List of all MD5 hashes.
        """
        return [output.md5 for output in self.outputs]


def merge_dvc_files(
    dvc_files: list[DvcFile],
) -> DvcFile:
    """Merge multiple DVC files into one.

    Args:
        dvc_files (list[DvcFile]): List of DVC file objects.

    Returns:
        DvcFile: Merged DVC file object.
    """
    merged_outputs = []
    for dvc_file in dvc_files:
        merged_outputs.extend(dvc_file.outputs)
    return DvcFile(outputs=merged_outputs)


@dataclass
class DvcTrackedFile:
    """Single DVC tracked file."""

    md5: str
    relpath: str

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "DvcTrackedFile":
        """Create a DvcTrackedFile from a dictionary.

        Args:
            data (dict[str, str]): Dictionary containing tracked file information.

        Returns:
            DvcTrackedFile: The created DvcTrackedFile instance.
        """
        return cls(md5=data["md5"], relpath=data["relpath"])

    def to_dict(self) -> dict[str, str]:
        """Convert the DvcTrackedFile to a dictionary.

        Returns:
            dict[str, str]: Dictionary representation of the tracked file.
        """
        return {"md5": self.md5, "relpath": self.relpath}

    def __lt__(self, other: "DvcTrackedFile") -> bool:
        """Compare two DvcTrackedFile objects for sorting.

        Args:
            other (DvcTrackedFile): The other tracked file.

        Returns:
            bool: True if this object is less than the other.
        """
        return (self.md5, self.relpath) < (other.md5, other.relpath)

    def __eq__(self, other: object) -> bool:
        """Check equality with another object.

        Args:
            other (object): The object to compare.

        Returns:
            bool: True if equal, False otherwise.
        """
        if not isinstance(other, DvcTrackedFile):
            return NotImplemented
        return (self.md5, self.relpath) == (other.md5, other.relpath)


@dataclass
class DvcTrackedFiles:
    """Collection of DVC tracked files."""

    files: list[DvcTrackedFile] = field(default_factory=list)

    @classmethod
    def from_list(cls, data: list[dict[str, str]]) -> "DvcTrackedFiles":
        """Create DvcTrackedFiles from a list of dictionaries.

        Args:
            data (list[dict[str, str]]): List of dictionaries with tracked file data.

        Returns:
            DvcTrackedFiles: The created DvcTrackedFiles instance.
        """
        files = [DvcTrackedFile.from_dict(item) for item in data]
        return cls(files=files)

    @classmethod
    def from_json_file(cls, file_path: str | Path) -> "DvcTrackedFiles":
        """Load DVC tracked files from a JSON file.

        Args:
            file_path (str | Path): Path to the JSON file.

        Returns:
            DvcTrackedFiles: The loaded DvcTrackedFiles instance.
        """
        file_path = Path(file_path)
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return cls.from_list(data)

    def to_list(self) -> list[dict[str, str]]:
        """Convert the tracked files to a list of dictionaries.

        Returns:
            list[dict[str, str]]: List of dictionary representations.
        """
        return [file.to_dict() for file in self.files]

    def to_json_file(self, file_path: str | Path) -> None:
        """Save the tracked files to a JSON file.

        Args:
            file_path (str | Path): Path to the JSON file.
        """
        file_path = Path(file_path)
        with file_path.open("w", encoding="utf-8") as file:
            json.dump(
                self.to_list(),
                file,
            )

    def add_file(self, md5: str, relpath: str) -> None:
        """Add a new tracked file while maintaining sorted order.

        Args:
            md5 (str): MD5 hash of the file.
            relpath (str): Relative path of the file.
        """
        new_file = DvcTrackedFile(md5=md5, relpath=relpath)
        bisect.insort(self.files, new_file)

    def get_all_paths(self) -> list[str]:
        """Get all relative paths of tracked files.

        Returns:
            list[str]: List of all relative paths.
        """
        return [file.relpath for file in self.files]

    def get_all_md5s(self) -> list[str]:
        """Get all MD5 hashes of tracked files.

        Returns:
            list[str]: List of all MD5 hashes.
        """
        return [file.md5 for file in self.files]

    def __len__(self) -> int:
        """Get the number of tracked files.

        Returns:
            int: Number of tracked files.
        """
        return len(self.files)

    def __iter__(self) -> Iterator[DvcTrackedFile]:
        """Iterate over tracked files.

        Returns:
            Iterator[DvcTrackedFile]: Iterator over tracked files.
        """
        return iter(self.files)


class DvcRepo:
    """DVC repository management."""

    def __init__(self, local_path: str | Path) -> None:
        """Initialize the DvcRepo.

        Args:
            local_path (str | Path): Path to the local DVC repository.
        """
        self.local_path: Path = Path(local_path)

    def init(self) -> None:
        """Initialize a DVC repository at the local path."""
        Repo.init(str(self.local_path))
        logger.info("Initialized DVC repository at %s", self.local_path)

    def _get_repo(self) -> Repo:
        """Get a DVC Repo object for the given path.

        Returns:
            Repo: The DVC Repo object.
        """
        return Repo(str(self.local_path))

    def _get_cache_dir(self) -> Path:
        """Get the cache path for a given MD5 hash.

        Returns:
            Path: The DVC cache directory.
        """
        return Path(self.local_path) / ".dvc" / "cache" / "files" / "md5"

    def set_remote(
        self,
        remote_name: str,
        remote_path: str | Path,
    ) -> None:
        """Set the DVC remote configuration for a local path.

        Args:
            remote_name (str): Name of the remote.
            remote_path (str | Path): Local directory for DVC remote storage.
        """
        repo = self._get_repo()
        remote_path = str(Path(remote_path).resolve())
        remote_dict = {"url": remote_path}

        with repo.config.edit() as conf:
            conf["remote"][remote_name] = remote_dict

        logger.info("Set DVC remote '%s' to local path '%s'", remote_name, remote_path)

    def set_remote_s3(  # pylint: disable=too-many-arguments
        self,
        remote_name: str,
        s3_server: str,
        s3_access_key: str,
        s3_secret_key: str,
        s3_bucket: str,
    ) -> None:
        """Set the DVC remote configuration for S3.

        Args:
            remote_name (str): Name of the remote.
            s3_server (str): S3 server URL.
            s3_access_key (str): S3 access key.
            s3_secret_key (str): S3 secret key.
            s3_bucket (str): S3 bucket for DVC remote storage.
        """
        repo = self._get_repo()
        remote_dict = {
            "url": "s3://" + s3_bucket,
            "endpointurl": s3_server,
            "access_key_id": s3_access_key,
            "secret_access_key": s3_secret_key,
        }
        with repo.config.edit() as conf:
            conf["core"] = {"remote": remote_name}
            conf["remote"][remote_name] = remote_dict
        logger.info("Set DVC remote '%s' to S3 bucket '%s'", remote_name, s3_bucket)

    def add_directory(self, directory: str | Path) -> None:
        """Add a directory to DVC tracking.

        Args:
            directory (str | Path): Directory to add.
        """
        directory = Path(directory)
        repo = self._get_repo()
        repo.add(str(self.local_path / directory), force=True)
        logger.highlight(
            level=LogLevel.INFO,
            message=f"Added directory '{directory}' to DVC tracking",
        )

    def add_files(
        self,
        files: list[str | Path],
    ) -> None:
        """Add files to DVC tracking.

        Args:
            files (list[str | Path]): List of files to add.
        """
        full_file_list = [str(self.local_path / file) for file in files]
        repo = self._get_repo()
        repo.add(targets=full_file_list)
        logger.highlight(
            level=LogLevel.INFO,
            message=f"Added {len(files)} files to DVC tracking",
        )

    def get_dvc_file(self, target_path: str | Path) -> DvcFile:
        """Load a DVC file for a given target path.

        Args:
            target_path (str | Path): The target file or directory path.

        Returns:
            DvcFile: The DVC file object.

        Raises:
            FileNotFoundError: If the DVC file does not exist.
        """
        dvc_file_path = (self.local_path / target_path).with_suffix(".dvc")
        if not dvc_file_path.is_file():
            raise FileNotFoundError(f"DVC file not found: {dvc_file_path}")
        return DvcFile.from_yaml_file(dvc_file_path)

    def get_dvc_tracked_files(self, dvc_output: DvcOutput) -> DvcTrackedFiles:
        """Load the tracked files for a given DVC output.

        Args:
            dvc_output (DvcOutput): The DVC output object.

        Returns:
            DvcTrackedFiles: The tracked files object.
        """
        md5_hash = dvc_output.md5
        cache_dir = self._get_cache_dir()
        cached_file = cache_dir / md5_hash[:2] / md5_hash[2:]
        cached_file.parent.mkdir(parents=True, exist_ok=True)
        return DvcTrackedFiles.from_json_file(cached_file)

    def push(self, remote_name: str) -> None:
        """Push tracked files to the DVC remote.

        Args:
            remote_name (str): Name of the remote.
        """
        repo = self._get_repo()
        repo.push(remote=remote_name)
        logger.info("Pushed tracked files to DVC remote '%s'", remote_name)
