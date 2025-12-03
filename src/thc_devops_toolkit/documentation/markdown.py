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
"""This module provides utility functions and classes for manipulating Markdown documents and dataframes."""

import re
from pathlib import Path

import pandas as pd

from thc_devops_toolkit.observability import LogLevel, logger

_comment_head: str = "<!--"
_comment_tail: str = "-->"
_dataframe_marker: str = "MarkdownDocumentManager:DataFrame"
_dataframe_id_argument: str = "dataframe_id="
_dataframe_marker_pattern = rf"^{_comment_head}{_dataframe_marker}\s+{_dataframe_id_argument}(.*?){_comment_tail}$"


class MarkdownDocumentManager:
    """Manages a markdown document, supporting dataframe parsing, insertion, and saving.

    Attributes:
        file_path (Path): Path to the markdown file.
        lines (list[str | pd.DataFrame]): Document lines and dataframes.
        _dataframes (dict[str, pd.DataFrame]): DataFrame id to pd.DataFrame mapping.
    """

    def __init__(self, file_path: str | Path):
        """Initializes the manager and loads the document.

        Args:
            file_path (str | Path): Path to the markdown file.
        """
        logger.info("Initializing MarkdownDocumentManager for file: %s", file_path)
        self.file_path: Path = Path(file_path)
        self.lines: list[str | pd.DataFrame] = []
        self._dataframes: dict[str, pd.DataFrame] = {}
        self.reload()

    def reload(self) -> None:
        """Loads the markdown document from file and parses dataframes."""
        logger.info("Loading markdown document from: %s", self.file_path)
        # housekeeping
        self.lines.clear()
        self._dataframes.clear()
        # read file
        if self.file_path.exists():
            with self.file_path.open("r", encoding="utf-8") as file:
                self.lines = [line.rstrip() for line in file.readlines()]
        else:
            logger.highlight(LogLevel.WARNING, f"File does not exist: {self.file_path}")

        self._parse_lines()

    def _parse_lines(self) -> None:
        """Parses document lines and identifies dataframes and markers."""
        logger.info("Parsing lines in markdown document.")

        # parse document
        line_idx: int = 0

        while line_idx < len(self.lines):
            # skip parsed dataframes
            if isinstance(self.lines[line_idx], pd.DataFrame):
                line_idx += 1
                continue

            cur_line = self.lines[line_idx].strip()

            # is managed dataframe?
            match_ = re.match(_dataframe_marker_pattern, cur_line)
            if match_:
                self._parse_dataframe(start_line=line_idx)

            line_idx += 1

    def _parse_dataframe(self, start_line: int) -> None:
        """Parses a markdown dataframe starting at a given line, removes parsed lines, and inserts a DataFrame object.

        Args:
            start_line (int): The line index to start parsing. This should point to the dataframe marker line.
        """
        logger.info("Parsing dataframe starting at line: %d", start_line)

        if start_line >= len(self.lines):
            logger.highlight(LogLevel.ERROR, f"Start line {start_line} out of range for dataframe parsing.")
            return

        # extract dataframe id
        match_ = re.match(_dataframe_marker_pattern, self.lines[start_line])
        if not match_:
            logger.highlight(LogLevel.ERROR, f"Line {start_line} is not a valid dataframe marker.")
            return
        dataframe_id = str(match_.group(1).strip())

        # parse dataframe lines
        line_idx = start_line + 1
        dataframe_lines: list[str] = []
        while line_idx < len(self.lines):
            cur_line = self.lines[line_idx]
            if isinstance(cur_line, str) and re.match(r"^\s*\|.*\|\s*$", cur_line):
                dataframe_lines.append(cur_line.strip())
                line_idx += 1
            else:
                break

        # at least 2 lines for a dataframe (header + separator)
        if len(dataframe_lines) < 2:
            logger.highlight(LogLevel.WARNING, f"Dataframe at line {start_line} has less than 2 lines, skipping.")
            return

        header = [col.strip() for col in dataframe_lines[0].split("|")[1:-1]]

        data = []
        for row in dataframe_lines[2:]:  # skip header and separator
            cols = [col.strip() for col in row.split("|")[1:-1]]
            if len(cols) == len(header):
                data_item = {header[col_idx]: cols[col_idx] for col_idx in range(len(header))}
                data.append(data_item)
            else:
                logger.highlight(
                    LogLevel.WARNING,
                    f"Row in dataframe at line {start_line} has mismatched columns, skipping row: {row}",
                )

        dataframe = pd.DataFrame(data, columns=header)

        # replace lines with DataFrame object
        del self.lines[start_line:line_idx]
        self.insert_dataframe(dataframe_id=dataframe_id, line_idx=start_line, dataframe=dataframe)

        logger.info("Inserted DataFrame object at line: %d", start_line)

    @property
    def dataframe_ids(self) -> list[str]:
        """Lists all dataframe ids in the document.

        Returns:
            list[str]: List of dataframe ids.
        """
        return list(self._dataframes.keys())

    def get_dataframe(self, dataframe_id: str) -> pd.DataFrame | None:
        """Retrieves a dataframe by its id.

        Args:
            dataframe_id (str): The id of the dataframe to retrieve.

        Returns:
            pd.DataFrame | None: The requested DataFrame, or None if not found.
        """
        return self._dataframes.get(dataframe_id, None)

    def insert_dataframe(self, dataframe_id: str, line_idx: int, dataframe: pd.DataFrame) -> None:
        """Inserts a dataframe marker at the specified line index followed by the dataframe.

        Args:
            dataframe_id (str): The ID of the dataframe to insert.
            line_idx (int): The line index to insert at.
            dataframe (pd.DataFrame): The DataFrame to insert.

        Raises:
            ValueError: If dataframe id already exists.
        """
        if dataframe_id in self._dataframes:
            logger.highlight(LogLevel.ERROR, f"Dataframe with id '{dataframe_id}' already exists. Insertion aborted.")
            raise ValueError(f"Dataframe with id {dataframe_id} already exists")

        dataframe_marker = self.generate_dataframe_marker(dataframe_id)
        self.lines.insert(line_idx, dataframe_marker)
        line_idx += 1

        self.lines.insert(line_idx, dataframe)
        self._dataframes[dataframe_id] = dataframe
        logger.info("DataFrame with id '%s' inserted at line %d", dataframe_id, line_idx)

    @staticmethod
    def generate_dataframe_marker(dataframe_id: str) -> str:
        """Generates a dataframe marker comment for a given dataframe id.

        Args:
            dataframe_id (str): The dataframe id.

        Returns:
            str: The dataframe marker comment.
        """
        logger.debug("Generating dataframe marker for dataframe_id: %s", dataframe_id)
        return f"{_comment_head}{_dataframe_marker} {_dataframe_id_argument}{dataframe_id}{_comment_tail}"

    def save(self) -> None:
        """Saves the current document (including dataframes) to file."""
        logger.info("Saving document to: %s", self.file_path)
        # Create a new list to hold the final content
        final_lines: list[str] = []
        line_idx = 0

        while line_idx < len(self.lines):
            cur_line = self.lines[line_idx]

            # is dataframe?
            if isinstance(cur_line, pd.DataFrame):
                dataframe_lines = cur_line.sort_index().to_markdown(index=False).split("\n")

                # Remove empty lines at the end
                while dataframe_lines and not dataframe_lines[-1].strip():
                    dataframe_lines.pop()

                final_lines.extend(dataframe_lines)

            # is string?
            elif isinstance(cur_line, str):
                # Keep original line
                final_lines.append(cur_line)

            line_idx += 1

        # Write to file
        with self.file_path.open("w", encoding="utf-8") as file:
            for line in final_lines:
                file.write(line + "\n")
        logger.info("Document saved to: %s", self.file_path)
