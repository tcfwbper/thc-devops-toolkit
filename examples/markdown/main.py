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
from pathlib import Path

import pandas as pd

from thc_devops_toolkit.documentation.markdown import MarkdownDocumentManager, MarkdownTable

md_example_dir = Path(__file__).resolve().parent
md_file = md_example_dir / "my_file.md"


def main() -> None:
    if md_file.exists():
        md_file.unlink()

    # Read empty document
    doc_manager = MarkdownDocumentManager(md_file)

    # Create MarkdownTable
    sample_data = [
        {"Project": "THC-DEVOPS-TOOLKIT", "Owner": "Tsung-Han Chang"},
        {"Project": "DEVPOD", "Owner": "Pesci Chang"},
    ]
    dataframe = pd.DataFrame(sample_data)
    table = MarkdownTable(table_id="my_projects", dataframe=dataframe)

    # Update markdown file
    doc_manager.lines.append("# My Projects")
    doc_manager.lines.append("")
    doc_manager.insert_table(table, len(doc_manager.lines))
    doc_manager.lines.append("")
    doc_manager.lines.append("## Notes")
    doc_manager.lines.append("- There are some useful projects.")
    doc_manager.lines.append("- Welcome to pull and contribute.")

    # Update an existing project or insert a new project
    table.upsert_row(data={"Project": "DEVPOD", "Owner": "Tsung-Han Chang"}, primary_key="Project")

    # Save the document
    doc_manager.save_document()


if __name__ == "__main__":
    main()
