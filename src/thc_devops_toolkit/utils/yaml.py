import logging
from typing import Any
import re

def parse_key_path(key_path: str) -> list[str | int]:
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
        m = pattern.fullmatch(part)
        if not m:
            raise ValueError(f"Invalid key_path part: {part}")
        # quoted key
        if m.group(1) is not None:
            tokens.append(m.group(1))
        elif m.group(2) is not None:
            tokens.append(m.group(2))
        # plain key
        elif m.group(3) is not None:
            tokens.append(m.group(3))
        # array indices
        indices = re.findall(r"\[(\d+)\]", m.group(4))
        for idx in indices:
            tokens.append(int(idx))
    return tokens

def get_value_from_dict(dictionary: dict, key_path: str) -> tuple[Any, bool]:
    tokens = parse_key_path(key_path)
    for token in tokens:
        if not dictionary.__contains__(token):
            print(f"Key {key_path} not found in values.yaml")
            return None, False
        dictionary = dictionary[token]
    return dictionary, True

def set_value_to_dict(dictionary: dict, key_path: str, value: Any) -> None:
    keys = key_path.split('.')
    d = dictionary
    for key in keys[:-1]:
        d = d[key]
    d[keys[-1]] = value
    logging.info(f"Successfully set value for {key_path} to {value}")
