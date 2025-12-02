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
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from thc_devops_toolkit.documentation.dataframe import DataFrameRow, upsert_row
from thc_devops_toolkit.documentation.markdown import MarkdownDocumentManager

md_example_dir = Path(__file__).resolve().parent
md_file = md_example_dir / "my_file.md"
dataframe_id = "my_projects"


@dataclass
class MyProjectRow(DataFrameRow):
    """Data frame row representing a project."""

    project: str
    owner: str
    timestamp: str
    primary_key = "project"
    _highlightable_fields = frozenset({"timestamp"})


def main() -> None:
    doc_manager = MarkdownDocumentManager(md_file)

    if not md_file.is_file():
        # Initialize markdown file
        doc_manager.lines.append("# My Projects")
        doc_manager.lines.append("")
        doc_manager.lines.append("## Notes")
        doc_manager.lines.append("Here are some useful projects.<br>")
        doc_manager.lines.append("Welcome to pull and contribute.")
        doc_manager.lines.append("")

    # Update dataframe
    dataframe = doc_manager.get_dataframe(dataframe_id=dataframe_id)
    if dataframe is None:
        dataframe = pd.DataFrame(columns=MyProjectRow.header())
        doc_manager.insert_dataframe(dataframe_id=dataframe_id, line_idx=len(doc_manager.lines), dataframe=dataframe)

    this_project = MyProjectRow(
        project="THC-DEVOPS-TOOLKIT",
        owner="Tsung-Han Chang",
        timestamp=datetime.today().strftime("%Y-%m-%d, %H:%M:%S"),
    )
    this_project.highlight()
    upsert_row(dataframe=dataframe, data=this_project)

    devpod = MyProjectRow(
        project="DEVPOD",
        owner="Pesci Chang",
        timestamp=datetime.today().strftime("%Y-%m-%d, %H:%M:%S"),
    )
    devpod.highlight()
    upsert_row(dataframe=dataframe, data=devpod)

    # Save the document
    doc_manager.save()


if __name__ == "__main__":
    main()
