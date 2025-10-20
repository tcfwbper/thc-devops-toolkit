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
"""A collection of utilities for Trivy security scanning."""
import subprocess
from importlib import resources
from pathlib import Path

from thc_devops_toolkit.observability import LogLevel, logger


def get_trivy_tpl(name: str) -> str:
    """Get the full path to a Trivy template file.

    Args:
        name (str): The name of the template file.

    Returns:
        str: The full path to the template file, prefixed with '@'.

    Raises:
        FileNotFoundError: If the template file does not exist.
    """
    tpl_filename = resources.files("thc_devops_toolkit.security.trivy.templates") / name

    if not tpl_filename.is_file():
        raise FileNotFoundError(f"Trivy template file not found: {tpl_filename}")

    return "@" + str(tpl_filename)


def trivy_scan(cr_host: str, image_name: str, image_tag: str, output_file: str | Path) -> None:
    """Scan a container image using Trivy and output the result as JSON.

    Args:
        cr_host (str): The container registry host.
        image_name (str): The name of the image.
        image_tag (str): The tag of the image.
        output_file (str | Path): The output file path for the scan result.

    Raises:
        RuntimeError: If the Trivy scan fails.
    """
    full_image_name = f"{cr_host}/{image_name}:{image_tag}"
    output_file = str(Path(output_file).with_suffix(".json"))
    cmd = ["trivy", "image", "--timeout", "60m", "--format", "json", "-o", output_file, full_image_name]
    process = subprocess.run(cmd, capture_output=True, check=False)
    if process.returncode != 0:
        raise RuntimeError(f"Failed to scan image: {full_image_name} (exit code: {process.returncode}){str(process.stderr, 'UTF-8')}")
    logger.highlight(
        level=LogLevel.INFO,
        message=f"Trivy scan completed for image: {full_image_name}",
    )


def trivy_convert(input_path: str | Path, output_path: str | Path, template: str | Path) -> None:
    """Convert a Trivy scan result using a template.

    Args:
        input_path (str | Path): Path to the input Trivy scan result file.
        output_path (str | Path): Path to the output file.
        template (str | Path): Name of the template to use for conversion.

    Raises:
        ValueError: If the template is not found.
        RuntimeError: If the Trivy conversion fails.
    """
    input_path = str(input_path)
    output_path = str(output_path)
    template_filename = str(Path(template).with_suffix(".tpl"))

    try:
        template_path = get_trivy_tpl(template_filename)
    except FileNotFoundError as exception:
        raise FileNotFoundError(f"Template not found: {template_filename}") from exception

    cmd = ["trivy", "convert", "--format", "template", "--template", template_path, "-o", output_path, input_path]
    process = subprocess.run(cmd, capture_output=True, check=False)
    if process.returncode != 0:
        raise RuntimeError(
            f"Failed to convert trivy template: {input_path} (exit code: {process.returncode}){str(process.stderr, 'UTF-8')}"
        )
    logger.highlight(
        level=LogLevel.INFO,
        message=f"Trivy conversion completed: {output_path}",
    )
