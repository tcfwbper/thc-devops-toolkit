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
"""This module provides a utility class for building Cython extensions from Python source files."""

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from Cython.Build import cythonize
from setuptools import setup

from thc_devops_toolkit.observability.logger import LogLevel, logger
from thc_devops_toolkit.utils.timer import timer


class CythonBuilder:
    """A utility class to build Cython extensions from Python source files."""

    def __init__(self, src: str | Path) -> None:
        """Initialize CythonBuilder.

        Args:
            src (str | Path): Source directory containing Python files.

        Raises:
            ValueError: If src is not a directory.
        """
        self._src = Path(src)
        self._dst = Path("build")
        self._validate_arguments()

    def _validate_arguments(self) -> None:
        """Validate all input arguments.

        Raises:
            ValueError: If src is not a directory.
        """
        if not self._src.is_dir():
            raise ValueError(f"Source path {self._src} is not a directory.")

    def _remove_pycache(self) -> None:
        """Remove __pycache__ directories from the source directory."""
        # match all __pycache__ directories
        pattern = "**/__pycache__"
        for pycache in self._src.glob(pattern):
            shutil.rmtree(pycache)
            logger.highlight(level=LogLevel.DEBUG, message=f"[CythonBuilder] Removed __pycache__ directory: {pycache}.")

    def _remove_dst(self) -> None:
        """Remove the destination build directory if it exists."""
        previous_build = self._dst / self._src.name
        if previous_build.is_dir():
            shutil.rmtree(previous_build)
            logger.highlight(level=LogLevel.DEBUG, message=f"[CythonBuilder] Removed build directory: {previous_build}.")

    def _setup_temp_dir(self, temp_src: str | Path) -> None:
        """Copy source files to a temporary directory and transform .py to .pyx.

        Args:
            temp_src (str | Path): Path to the temporary directory.
        """
        temp_src = Path(temp_src)
        for item in self._src.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(self._src)

                # transform .py to .pyx
                if item.suffix == ".py":
                    new_name = item.stem + ".pyx"
                    target_path = temp_src / rel_path.parent / new_name
                else:
                    target_path = temp_src / rel_path

                # copy file to temp directory
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target_path)
                logger.highlight(level=LogLevel.DEBUG, message=f"[CythonBuilder] Copied {item} to temporary directory as {target_path}.")

    @staticmethod
    def _ensure_initializer(temp_src: str | Path) -> None:
        """Ensure that each directory in the temporary directory has an __init__.pyx file.

        Args:
            temp_src (str | Path): Path to the temporary directory.
        """
        temp_src = Path(temp_src)
        all_dirs = [temp_src] + [dir_ for dir_ in temp_src.rglob("*") if dir_.is_dir()]

        for dir_ in all_dirs:
            init_file = dir_ / "__init__.pyx"
            if not init_file.exists():
                init_file.touch()
                logger.highlight(level=LogLevel.DEBUG, message=f"[CythonBuilder] Created missing __init__.pyx in directory: {dir_}.")

    def _copy_non_python_files(self, temp_src: str | Path) -> None:
        """Copy non-Python source files to a built directory.

        Args:
            temp_src (str | Path): Path to the temporary directory.
        """
        temp_src = Path(temp_src)
        built_dir = self._dst / self._src.name
        for item in temp_src.rglob("*"):
            if item.is_file():
                # ignore .py and .pyx files
                if item.suffix == ".py" or item.suffix == ".pyx":
                    continue

                rel_path = item.relative_to(temp_src)
                target_path = built_dir / rel_path

                # copy file to built directory
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target_path)
                logger.highlight(level=LogLevel.DEBUG, message=f"[CythonBuilder] Copied {item} to built directory as {target_path}.")

    def build(self, compiler_directives: dict[str, Any] | None = None) -> None:
        """Build Cython extensions from the source directory.

        Args:
            compiler_directives (dict[str, Any] | None): Optional Cython compiler directives.
        """
        logger.highlight(level=LogLevel.INFO, message=f"[Cython Builder] Start building {self._src}.")
        compiler_directives = {"annotation_typing": False, **(compiler_directives or {})}

        self._remove_pycache()
        self._remove_dst()

        with tempfile.TemporaryDirectory(prefix="cython_build_") as temp_dir, timer(topic="Cython Build"):
            temp_src = Path(temp_dir) / self._src.name
            temp_build = Path(temp_dir) / "build"
            self._setup_temp_dir(temp_src=temp_src)
            self._ensure_initializer(temp_src=temp_src)
            self._copy_non_python_files(temp_src=temp_src)

            # collect all .pyx files
            pyx_files: list[str] = [str(file) for file in temp_src.rglob("*") if file.is_file() and file.suffix == ".pyx"]
            # process arguments for setuptools
            original_argv = sys.argv.copy()
            sys.argv = ["setup.py", "build_ext", "--build-lib", str(self._dst), "--build-temp", str(temp_build)]
            try:
                setup(
                    ext_modules=cythonize(  # type: ignore
                        pyx_files,
                        compiler_directives=compiler_directives,
                    ),
                    zip_safe=False,
                )
            finally:
                sys.argv = original_argv
        logger.highlight(level=LogLevel.INFO, message=f"[Cython Builder] Successfully built {self._src}.")
