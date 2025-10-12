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
"""This module provides utility functions for parsing and manipulating YAML data."""

import logging
import re
from typing import Any

# Set up a default logger for this module
logger = logging.getLogger(__name__)


def parse_key_path(key_path: str) -> list[str | int]:
    """Parses a key path string into a list of keys and indices.

    Args:
        key_path (str): The key path string (e.g., 'foo.bar[0].baz', "foo.'complex.key'.baz").

    Returns:
        list[str | int]: List of keys and indices.
    """
    logger.debug("Parsing key path: %s", key_path)
    tokens = []

    # Pattern to match:
    # - Single quoted keys: 'key'
    # - Double quoted keys: "key"
    # - Plain keys: key
    # - Array indices: [0][1][2]
    pattern = re.compile(
        r"""
        (?:
            '([^']*)'           # group 1: single-quoted key (allows empty)
            | "([^"]*)"         # group 2: double-quoted key (allows empty)
            | ([a-zA-Z0-9_\-]+) # group 3: plain key
        )
        ((?:\[\d+\])*)          # group 4: array indices
    """,
        re.VERBOSE,
    )

    pos = 0
    while pos < len(key_path):
        # Skip dots
        while pos < len(key_path) and key_path[pos] == ".":
            pos += 1

        if pos >= len(key_path):
            break

        # Find the next component
        match_ = pattern.match(key_path, pos)
        if not match_:
            logger.error("Invalid key_path at position %d: %s", pos, key_path[pos:])
            raise ValueError(f"Invalid key_path at position {pos}: {key_path[pos:]}")

        # Extract the key
        if match_.group(1) is not None:  # single-quoted
            tokens.append(match_.group(1))
        elif match_.group(2) is not None:  # double-quoted
            tokens.append(match_.group(2))
        elif match_.group(3) is not None:  # plain key
            tokens.append(match_.group(3))

        # Extract array indices
        indices_str = match_.group(4)
        if indices_str:
            indices = re.findall(r"\[(\d+)\]", indices_str)
            for idx in indices:
                tokens.append(int(idx))

        # Move to the end of this match
        pos = match_.end()

    logger.debug("Parsed tokens: %r", tokens)
    return tokens


def get_value_from_dict(dictionary: dict[str, Any], key_path: str) -> tuple[Any, bool]:
    """Gets a value from a nested dictionary using a key path.

    Args:
        dictionary (dict[str, Any]): The dictionary to search.
        key_path (str): The key path string.

    Returns:
        tuple[Any, bool]: (value, True) if found, (None, False) otherwise.
    """
    logger.debug("Getting value from dict for key_path: %s", key_path)
    tokens = parse_key_path(key_path)
    dict_iter: Any = dictionary
    for token in tokens:
        if isinstance(dict_iter, list):
            if not isinstance(token, int) or token >= len(dict_iter):
                logger.warning("Invalid index %s for %s", token, dict_iter)
                return None, False
        elif token not in dict_iter:
            logger.warning("Key %s not found in values.yaml", key_path)
            return None, False
        dict_iter = dict_iter[token]
    logger.info("Successfully got value for %s: %r", key_path, dict_iter)
    return dict_iter, True


def _get_or_create_next(container: Any, token: str | int, next_token: str | int) -> Any:
    if isinstance(next_token, int):
        if token in container:
            if not isinstance(container[token], list):
                logger.error("Expected list at %r, got %r", token, type(container[token]))
                raise ValueError(f"Expected list at {token}, got {type(container[token])}")
        else:
            container[token] = []
    elif isinstance(next_token, str):
        if token in container:
            if not isinstance(container[token], dict):
                logger.error("Expected dict at %r, got %r", token, type(container[token]))
                raise ValueError(f"Expected dict at {token}, got {type(container[token])}")
        else:
            container[token] = {}
    return container[token]


def _set_final_value(container: Any, token: str | int, value: Any) -> None:
    if isinstance(container, list):
        if not isinstance(token, int):
            logger.error("Expected integer index for list, got %r", token)
            raise ValueError(f"Expected integer index for list, got {token}")
        while token >= len(container):
            container.append(None)
        container[token] = value
    else:
        container[token] = value


def set_value_to_dict(dictionary: dict[str, Any], key_path: str, value: Any) -> None:
    """Sets a value in a nested dictionary using a key path.

    Args:
        dictionary (dict[str, Any]): The dictionary to modify.
        key_path (str): The key path string.
        value (Any): The value to set.
    """
    logger.debug("Setting value for key_path: %s to %r", key_path, value)
    tokens = parse_key_path(key_path)
    dict_iter: Any = dictionary
    for i, token in enumerate(tokens[:-1]):
        next_token = tokens[i + 1]
        if isinstance(dict_iter, list):
            if not isinstance(token, int):
                logger.error("Expected integer index for list, got %r", token)
                raise ValueError(f"Expected integer index for list, got {token}")
            while token >= len(dict_iter):
                dict_iter.append(None)
            if dict_iter[token] is None:
                dict_iter[token] = [] if isinstance(next_token, int) else {}
            dict_iter = dict_iter[token]
        else:
            dict_iter = _get_or_create_next(dict_iter, token, next_token)
    last_token = tokens[-1]
    _set_final_value(dict_iter, last_token, value)
    logger.info("Successfully set value for %s to %r", key_path, value)
