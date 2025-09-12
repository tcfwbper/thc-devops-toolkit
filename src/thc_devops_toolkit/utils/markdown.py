from dataclasses import dataclass
import logging
from pathlib import Path
import re
from typing import Any, Hashable
import uuid

import pandas as pd

_markdown_comment_head: str = "<!--"
_markdown_comment_tail: str = "-->"
_markdown_table_marker: str = "MarkdownDocumentManager:Table"
_markdown_table_id_argument: str = "table_id="

def get_empty_table(header: list[Hashable]) -> pd.DataFrame:
    return pd.DataFrame(columns=header)

def match_mask(dataframe: pd.DataFrame, column: Hashable, match_value: Any) -> pd.Series[bool]:
    condition = pd.Series([True] * len(dataframe))
    condition &= (dataframe[column] == match_value)
    return condition

@dataclass
class MarkdownTable:
    # please ensure table_id is unique in a markdown document
    table_id: str = ""
    dataframe: pd.DataFrame | None = None

    def upsert_row(
        self,
        data: dict[Hashable, Any],
        primary_key: str,
        insert_ahead: bool = False
    ) -> None:
        # check primary key
        condition = match_mask(
            dataframe=self.dataframe,
            column=primary_key,
            match_value=data[primary_key]
        )
        if condition.any():
            # hit
            row_idx = self.dataframe[condition].index[0]
            for key, value in data.items():
                # skip?
                if value is not None:
                    self.dataframe.at[row_idx, key] = value
        else:
            # new data
            if insert_ahead:
                new_df = pd.DataFrame([data])
                self.dataframe = pd.concat([new_df, self.dataframe], ignore_index=True)
            else:
                self.dataframe.loc[len(self.dataframe)] = data

class MarkdownDocumentManager:
    def __init__(self, file_path: str | Path):
        self.file_path: Path = Path(file_path)
        self.lines: list[str | MarkdownTable] = []
        self.tables: dict[str, MarkdownTable] = {}
        self._load_document()
    
    def _load_document(self) -> None:
        if self.file_path.exists():
            with self.file_path.open("r", encoding="utf-8") as f:
                self.lines = [line.rstrip() for line in f.readlines()]
        self.parse_lines()
    
    def parse_lines(self) -> None:
        # housekeeping
        self.tables.clear()

        # parse document
        i: int = 0
        table_id: str | None = None

        while i < len(self.lines):
            line = self.lines[i].strip()
            
            # is table marker?
            table_marker_pattern = rf"^{_markdown_comment_head}{_markdown_table_marker}\s+{_markdown_table_id_argument}(.*?){_markdown_comment_tail}$"
            match_ = re.match(table_marker_pattern, line)
            if match_:
                table_id = match_.group(1).strip()
                i += 1
                continue
            
            # is table?
            # This match table like "| something | else |"
            if re.match(r'^\s*\|.*\|\s*$', line):
                markdown_table = self._parse_table(i)
                if markdown_table:
                    # if table_id is not defined, we don't care about this table
                    # just assign a temporary and random one
                    if not table_id:
                        table_id = "default-" + str(uuid.uuid4())
                    markdown_table.table_id = table_id
                    self.tables[table_id] = markdown_table
                    table_id = None
                    i += 1
                    continue
            
            table_id = None # table_id only works when table is immediately after marker
            i += 1
    
    def _parse_table(self, start_line: int) -> MarkdownTable | None:
        if start_line >= len(self.lines):
            return None
        
        table_lines: list[str] = []
        i = start_line
        
        while i < len(self.lines) and re.match(r'^\s*\|.*\|\s*$', self.lines[i]):
            table_lines.append(self.lines[i].strip())
            i += 1

        # at least 2 lines for a table (header + separator)
        if len(table_lines) < 2:
            return None
        
        header = [col.strip() for col in table_lines[0].split("|")[1:-1]]
        
        data = []
        for row in table_lines[2:]: # skip header and separator
            cols = [col.strip() for col in row.split("|")[1:-1]]
            if len(cols) == len(header):
                data_item = {header[j]: cols[j] for j in range(len(header))}
                data.append(data_item)
        
        df = pd.DataFrame(data, columns=header)
        
        markdown_table = MarkdownTable(
            table_id="",
            dataframe=df
        )

        # replace lines with table object
        del self.lines[start_line:i]
        self.lines.insert(start_line, markdown_table)
        
        return markdown_table
    
    def list_tables(self) -> list[str]:
        return list(self.tables.keys())
    
    def save_document(self) -> None:
        # Create a new list to hold the final content
        final_lines: list[str] = []
        i = 0

        while i < len(self.lines):
            
            # is table?
            if isinstance(self.lines[i], MarkdownTable):
                markdown_table = self.lines[i]
                if markdown_table.dataframe is not None:
                    table_lines = markdown_table.dataframe.to_markdown(index=False).split('\n')
                    # Remove empty lines at the end
                    while table_lines and not table_lines[-1].strip():
                        table_lines.pop()
                    final_lines.extend(table_lines)
            else:
                # Keep original line
                final_lines.append(self.lines[i])
            
            i += 1

        # Write to file
        with self.file_path.open("w", encoding="utf-8") as f:
            for line in final_lines:
                f.write(line + '\n')

    def generate_table_marker(self, table_id: str) -> str:
        return f"{_markdown_comment_head}{_markdown_table_marker} {_markdown_table_id_argument}{table_id}{_markdown_comment_tail}"
