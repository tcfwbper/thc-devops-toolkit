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
import logging
from pathlib import Path

import pandas as pd

from thc_devops_toolkit.documentation.markdown import MarkdownDocumentManager, MarkdownTable

# Set up a default logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


md_example_dir = Path(__file__).resolve().parent
md_file = md_example_dir / "my_file.md"


def main() -> None:
    if md_file.exists():
        md_file.unlink()

    # Read empty document
    doc_manager = MarkdownDocumentManager(md_file)
    logger.info(f"Loaded document with {len(doc_manager.lines)} lines")

    # Create MarkdownTable
    sample_data = [
        {"Project": "THC-DEVOPS-TOOLKIT", "Owner": "Tsung-Han Chang"},
        {"Project": "DEVPOD", "Owner": "Pesci Chang"},
    ]
    dataframe = pd.DataFrame(sample_data)
    table = MarkdownTable(table_id="my_projects", dataframe=dataframe)
    logger.info(f"Created table with {len(dataframe)} rows and columns: {list(dataframe.columns)}")

    # Update markdown file
    doc_manager.lines.append("# My Projects")
    doc_manager.lines.append("")
    doc_manager.insert_table(table, len(doc_manager.lines))
    doc_manager.lines.append("")
    doc_manager.lines.append("## Notes")
    doc_manager.lines.append("- There are some useful projects.")
    doc_manager.lines.append("- Welcome to pull and contribute.")
    logger.info(f"Document now has {len(doc_manager.lines)} lines")

    # Update an existing project or insert a new project
    table.upsert_row(data={"Project": "DEVPOD", "Owner": "Tsung-Han Chang"}, primary_key="Project")

    # Save the document
    doc_manager.save_document()
    logger.info(f"Document saved to {md_file}")


if __name__ == "__main__":
    main()
