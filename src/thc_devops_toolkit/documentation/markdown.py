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
"""This module provides utility functions and classes for manipulating Markdown documents and tables.

Includes MarkdownDocumentManager for managing tables in markdown files, and MarkdownTable for table operations.
"""

import re
import uuid
from collections.abc import Hashable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from thc_devops_toolkit.observability import THCLoggerHighlightLevel, thc_logger

_markdown_comment_head: str = "<!--"
_markdown_comment_tail: str = "-->"
_markdown_table_marker: str = "MarkdownDocumentManager:Table"
_markdown_table_id_argument: str = "table_id="


def get_empty_dataframe(header: list[Hashable]) -> pd.DataFrame:
    """Creates an empty DataFrame with the specified header.

    Args:
        header (list[Hashable]): List of column names.

    Returns:
        pd.DataFrame: An empty DataFrame with the given columns.
    """
    thc_logger.highlight(
        THCLoggerHighlightLevel.DEBUG,
        f"Creating empty table with header: {header}",
    )
    return pd.DataFrame(columns=header)


def match_mask(dataframe: pd.DataFrame, column: Hashable, match_value: Any) -> pd.Series:
    """Returns a boolean mask for rows where column matches match_value.

    Args:
        dataframe (pd.DataFrame): The DataFrame to search.
        column (Hashable): The column to match.
        match_value (Any): The value to match.

    Returns:
        pd.Series[bool]: Boolean mask for matching rows.
    """
    thc_logger.highlight(
        THCLoggerHighlightLevel.DEBUG,
        f"Matching mask for column '{column}' with value '{match_value}'",
    )
    condition = pd.Series([True] * len(dataframe))
    condition &= dataframe[column] == match_value
    return condition


@dataclass
class MarkdownTable:
    """Represents a markdown table with a unique table_id and DataFrame.

    Attributes:
        table_id (str): Unique identifier for the table.
        dataframe (pd.DataFrame | None): The table data.
    """

    # please ensure table_id is unique in a markdown document
    table_id: str = ""
    dataframe: pd.DataFrame | None = None

    def upsert_row(self, data: dict[Hashable, Any], primary_key: str, insert_ahead: bool = False) -> None:
        """Upserts a row into the table by primary key.

        Args:
            data (dict[Hashable, Any]): Row data to insert or update.
            primary_key (str): The primary key column.
            insert_ahead (bool, optional): Insert at the top if True. Defaults to False.
        """
        thc_logger.highlight(
            THCLoggerHighlightLevel.DEBUG,
            f"Upserting row with primary_key '{primary_key}': {data}",
        )
        # Ensure dataframe is initialized
        if self.dataframe is None:
            self.dataframe = get_empty_dataframe(list(data.keys()))
        # check primary key
        condition = match_mask(dataframe=self.dataframe, column=primary_key, match_value=data[primary_key])
        if condition.any():
            # hit
            thc_logger.highlight(
                THCLoggerHighlightLevel.DEBUG,
                f"Updating existing row with primary_key '{primary_key}': {data}",
            )
            row_idx = self.dataframe[condition].index[0]
            for key, value in data.items():
                # skip?
                if value is not None:
                    thc_logger.highlight(
                        THCLoggerHighlightLevel.DEBUG,
                        f"Updating column '{key}' to '{value}' at row {row_idx}",
                    )
                    self.dataframe.at[row_idx, key] = value
        else:
            # new data
            thc_logger.highlight(
                THCLoggerHighlightLevel.DEBUG,
                f"No row found for primary_key '{data[primary_key]}', inserting new row.",
            )
            if insert_ahead:
                new_df = pd.DataFrame([data])
                self.dataframe = pd.concat([new_df, self.dataframe], ignore_index=True)
            else:
                self.dataframe.loc[len(self.dataframe)] = data


class MarkdownDocumentManager:
    """Manages a markdown document, supporting table parsing, insertion, and saving.

    Attributes:
        file_path (Path): Path to the markdown file.
        lines (list[str | MarkdownTable]): Document lines and tables.
        tables (dict[str, MarkdownTable]): Table id to MarkdownTable mapping.
    """

    def __init__(self, file_path: str | Path):
        """Initializes the manager and loads the document.

        Args:
            file_path (str | Path): Path to the markdown file.
        """
        thc_logger.highlight(
            THCLoggerHighlightLevel.INFO,
            f"Initializing MarkdownDocumentManager for file: {file_path}",
        )
        self.file_path: Path = Path(file_path)
        self.lines: list[str | MarkdownTable] = []
        self.tables: dict[str, MarkdownTable] = {}
        self._load_document()

    def _load_document(self) -> None:
        """Loads the markdown document from file and parses tables."""
        thc_logger.highlight(
            THCLoggerHighlightLevel.INFO,
            f"Loading markdown document from: {self.file_path}",
        )
        if self.file_path.exists():
            with self.file_path.open("r", encoding="utf-8") as file:
                self.lines = [line.rstrip() for line in file.readlines()]
        else:
            thc_logger.highlight(
                THCLoggerHighlightLevel.WARNING,
                f"File does not exist: {self.file_path}",
            )
        self._parse_lines()

    def _parse_lines(self) -> None:
        """Parses document lines and identifies tables and markers."""
        thc_logger.highlight(
            THCLoggerHighlightLevel.INFO,
            "Parsing lines in markdown document.",
        )
        # housekeeping
        self.tables.clear()

        # parse document
        i: int = 0
        table_id: str | None = None

        while i < len(self.lines):
            line_obj = self.lines[i]
            if isinstance(line_obj, str):
                line = line_obj.strip()
            else:
                # If it's a MarkdownTable, skip marker/table logic
                table_id = None
                i += 1
                continue

            # is table marker?
            table_marker_pattern = (
                rf"^{_markdown_comment_head}{_markdown_table_marker}\s+{_markdown_table_id_argument}(.*?){_markdown_comment_tail}$"
            )
            match_ = re.match(table_marker_pattern, line)
            if match_:
                table_id = match_.group(1).strip()
                i += 1
                continue

            # is table?
            # This match table like "| something | else |"
            if re.match(r"^\s*\|.*\|\s*$", line):
                thc_logger.highlight(
                    THCLoggerHighlightLevel.DEBUG,
                    f"Found markdown table at line {i}",
                )
                markdown_table = self._parse_table(i)
                if markdown_table:
                    # if table_id is not defined, we don't care about this table
                    # just assign a temporary and random one
                    if not table_id:
                        table_id = self._get_tmp_table_id()
                        thc_logger.highlight(
                            THCLoggerHighlightLevel.WARNING,
                            f"Table without marker found, assigning temporary table_id: {table_id}",
                        )
                    markdown_table.table_id = table_id
                    self.tables[table_id] = markdown_table
                    table_id = None
                    i += 1
                    continue

            table_id = None  # table_id only works when table is immediately after marker
            i += 1

    def _parse_table(self, start_line: int) -> MarkdownTable | None:
        """Parses a markdown table starting at a given line.

        Args:
            start_line (int): The line index to start parsing.

        Returns:
            MarkdownTable | None: Parsed table or None if not found.
        """
        thc_logger.highlight(
            THCLoggerHighlightLevel.DEBUG,
            f"Parsing table starting at line {start_line}",
        )
        if start_line >= len(self.lines):
            thc_logger.highlight(
                THCLoggerHighlightLevel.WARNING,
                f"Start line {start_line} out of range for table parsing.",
            )
            return None

        table_lines: list[str] = []
        i = start_line

        while i < len(self.lines):
            line_obj = self.lines[i]
            if isinstance(line_obj, str) and re.match(r"^\s*\|.*\|\s*$", line_obj):
                table_lines.append(line_obj.strip())
                i += 1
            else:
                break

        # at least 2 lines for a table (header + separator)
        if len(table_lines) < 2:
            thc_logger.highlight(
                THCLoggerHighlightLevel.WARNING,
                f"Table at line {start_line} has less than 2 lines, skipping.",
            )
            return None

        header = [col.strip() for col in table_lines[0].split("|")[1:-1]]

        data = []
        for row in table_lines[2:]:  # skip header and separator
            cols = [col.strip() for col in row.split("|")[1:-1]]
            if len(cols) == len(header):
                data_item = {header[j]: cols[j] for j in range(len(header))}
                data.append(data_item)
            else:
                thc_logger.highlight(
                    THCLoggerHighlightLevel.WARNING,
                    f"Row in table at line {start_line} has mismatched columns, skipping row: {row}",
                )

        dataframe = pd.DataFrame(data, columns=header)

        markdown_table = MarkdownTable(table_id="", dataframe=dataframe)

        # replace lines with table object
        del self.lines[start_line:i]
        self.lines.insert(start_line, markdown_table)
        thc_logger.highlight(
            THCLoggerHighlightLevel.DEBUG,
            f"Inserted MarkdownTable object at line {start_line}.",
        )
        return markdown_table

    @staticmethod
    def _get_tmp_table_id() -> str:
        """Generates a temporary unique table id.

        Returns:
            str: Temporary table id.
        """
        tmp_id = "default-" + str(uuid.uuid4())
        thc_logger.highlight(
            THCLoggerHighlightLevel.DEBUG,
            f"Generated temporary table_id: {tmp_id}",
        )
        return tmp_id

    def insert_table(self, table: MarkdownTable, line_idx: int) -> None:
        """Inserts a table at the specified line index.

        Args:
            table (MarkdownTable): The table to insert.
            line_idx (int): The line index to insert at.

        Raises:
            ValueError: If table id already exists.
        """
        thc_logger.highlight(
            THCLoggerHighlightLevel.INFO,
            f"Inserting table with id '{table.table_id}' at line {line_idx}",
        )
        if table.table_id:
            table_marker = self.generate_table_marker(table.table_id)
        else:
            thc_logger.highlight(
                THCLoggerHighlightLevel.WARNING,
                "Table ID is not defined. Generating a temporary ID.",
            )
            table.table_id = self._get_tmp_table_id()
            table_marker = None

        if table.table_id in self.tables:
            thc_logger.highlight(
                THCLoggerHighlightLevel.ERROR,
                f"Table with id '{table.table_id}' already exists. Insertion aborted.",
            )
            raise ValueError(f"Table with id {table.table_id} already exists")

        if table_marker:
            self.lines.insert(line_idx, table_marker)
            line_idx += 1
        self.lines.insert(line_idx, table)
        self.tables[table.table_id] = table
        thc_logger.highlight(
            THCLoggerHighlightLevel.DEBUG,
            f"Inserted table with id '{table.table_id}' at line {line_idx}.",
        )

    def list_tables(self) -> list[str]:
        """Lists all table ids in the document.

        Returns:
            list[str]: List of table ids.
        """
        thc_logger.highlight(
            THCLoggerHighlightLevel.INFO,
            "Listing all table ids in document.",
        )
        return list(self.tables.keys())

    def save_document(self) -> None:
        """Saves the current document (including tables) to file."""
        thc_logger.highlight(
            THCLoggerHighlightLevel.INFO,
            f"Saving document to: {self.file_path}",
        )
        # Create a new list to hold the final content
        final_lines: list[str] = []
        i = 0

        while i < len(self.lines):
            # is table?
            line_obj = self.lines[i]
            if isinstance(line_obj, MarkdownTable):
                markdown_table = line_obj
                if markdown_table.dataframe is not None:
                    thc_logger.highlight(
                        THCLoggerHighlightLevel.DEBUG,
                        f"Writing table with id '{markdown_table.table_id}' to file.",
                    )
                    table_lines = markdown_table.dataframe.to_markdown(index=False).split("\n")
                    # Remove empty lines at the end
                    while table_lines and not table_lines[-1].strip():
                        table_lines.pop()
                    final_lines.extend(table_lines)
            elif isinstance(line_obj, str):
                # Keep original line
                final_lines.append(line_obj)
            i += 1
        # Write to file
        with self.file_path.open("w", encoding="utf-8") as file:
            for line in final_lines:
                file.write(line + "\n")
        thc_logger.highlight(
            THCLoggerHighlightLevel.INFO,
            f"Document saved successfully to: {self.file_path}",
        )

    @staticmethod
    def generate_table_marker(table_id: str) -> str:
        """Generates a table marker comment for a given table id.

        Args:
            table_id (str): The table id.

        Returns:
            str: The table marker comment.
        """
        thc_logger.highlight(
            THCLoggerHighlightLevel.DEBUG,
            f"Generating table marker for table_id: {table_id}",
        )
        return f"{_markdown_comment_head}{_markdown_table_marker} {_markdown_table_id_argument}{table_id}{_markdown_comment_tail}"
