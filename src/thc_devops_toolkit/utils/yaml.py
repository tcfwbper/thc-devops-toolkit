"""This module provides utility functions for parsing and manipulating YAML data."""

import logging
import re
from typing import Any

# Set up a default logger for this module
logger = logging.getLogger(__name__)


def parse_key_path(key_path: str) -> list[str | int]:
    """Parses a key path string into a list of keys and indices.

    Args:
        key_path (str): The key path string (e.g., 'foo.bar[0].baz').

    Returns:
        list[str | int]: List of keys and indices.
    """
    logger.debug("Parsing key path: %s", key_path)
    tokens = []
    pattern = re.compile(
        r"""
        (?:
            '([^']+)'           # group 1: single-quoted key
            | "([^"]+)"         # group 2: double-quoted key
            | ([a-zA-Z0-9_\-]+) # group 3: plain key
        )
        ((?:\[\d+\])*)          # group 4: array indices
    """,
        re.VERBOSE,
    )

    for part in key_path.split("."):
        match_ = pattern.fullmatch(part)
        if not match_:
            logger.error("Invalid key_path part: %s", part)
            raise ValueError(f"Invalid key_path part: {part}")
        # quoted key
        if match_.group(1) is not None:
            tokens.append(match_.group(1))
        elif match_.group(2) is not None:
            tokens.append(match_.group(2))
        # plain key
        elif match_.group(3) is not None:
            tokens.append(match_.group(3))
        # array indices
        indices = re.findall(r"\[(\d+)\]", match_.group(4))
        for idx in indices:
            tokens.append(int(idx))
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
        if not dict_iter.__contains__(token):
            logger.warning("Key %s not found in values.yaml", key_path)
            return None, False
        dict_iter = dict_iter[token]
    logger.info("Successfully got value for %s: %r", key_path, dict_iter)
    return dict_iter, True


def set_value_to_dict(dictionary: dict[str, Any], key_path: str, value: Any) -> None:
    """Sets a value in a nested dictionary using a key path.

    Args:
        dictionary (dict[str, Any]): The dictionary to modify.
        key_path (str): The key path string.
        value (Any): The value to set.
    """
    logger.debug("Setting value for key_path: %s to %r", key_path, value)
    keys = key_path.split(".")
    dict_iter = dictionary
    for key in keys[:-1]:
        dict_iter = dict_iter[key]
    dict_iter[keys[-1]] = value
    logger.info("Successfully set value for %s to %r", key_path, value)
