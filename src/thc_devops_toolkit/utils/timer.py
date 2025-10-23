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
"""This module provides utility functions for timing code execution."""

import time
from collections.abc import Iterator
from contextlib import contextmanager

from thc_devops_toolkit.observability.logger import LogLevel, logger


@contextmanager
def timer(topic: str) -> Iterator[None]:
    """Context manager to measure and log the execution time of a code block.

    Args:
        topic (str): Description of the code block being timed.
    """
    # start time
    start_time = time.time()
    # task execution
    yield
    # calculate elapsed time
    elapsed_time = time.time() - start_time
    logger.highlight(level=LogLevel.INFO, message=f"[Timer] {topic} completed in {elapsed_time:.2f} seconds.")
