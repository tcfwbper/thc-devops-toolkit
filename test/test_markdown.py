import tempfile
import shutil
from pathlib import Path
from thc_devops_toolkit.documentation import markdown as md_mod
import pandas as pd
import pytest

@pytest.fixture(scope="function")
def tmp_md_file():
    tmpdir = tempfile.mkdtemp()
    md_path = Path(tmpdir) / "test.md"
    yield md_path
    if md_path.exists():
        md_path.unlink()
    shutil.rmtree(tmpdir, ignore_errors=True)

def test_markdown_table_upsert_row():
    table = md_mod.MarkdownTable(table_id="t1")
    data1 = {"id": "1", "name": "Alice"}
    table.upsert_row(data1, primary_key="id")
    assert table.dataframe.shape[0] == 1
    # update
    data2 = {"id": "1", "name": "Bob"}
    table.upsert_row(data2, primary_key="id")
    assert table.dataframe.iloc[0]["name"] == "Bob"
    # insert ahead
    data3 = {"id": "2", "name": "Carol"}
    table.upsert_row(data3, primary_key="id", insert_ahead=True)
    assert table.dataframe.iloc[0]["id"] == "2"

def test_generate_table_marker():
    marker = md_mod.MarkdownDocumentManager.generate_table_marker("table-xyz")
    assert "table_id=table-xyz" in marker

def test_document_manager_parse_and_list_tables(tmp_md_file):
    content = [
        md_mod._markdown_comment_head + md_mod._markdown_table_marker + " " + md_mod._markdown_table_id_argument + "t1" + md_mod._markdown_comment_tail,
        "| id | name |",
        "|----|------|",
        "| 1  | Alice |",
        "| 2  | Bob   |",
        "",
        "Some text.",
    ]
    tmp_md_file.write_text("\n".join(content))
    mgr = md_mod.MarkdownDocumentManager(tmp_md_file)
    assert "t1" in mgr.list_tables()
    table = mgr.tables["t1"]
    assert isinstance(table, md_mod.MarkdownTable)
    assert table.dataframe.shape[0] == 2
    assert table.dataframe.iloc[0]["name"] == "Alice"

def test_insert_table_and_save(tmp_md_file):
    mgr = md_mod.MarkdownDocumentManager(tmp_md_file)
    df = pd.DataFrame([{"id": "1", "name": "A"}, {"id": "2", "name": "B"}])
    table = md_mod.MarkdownTable(table_id="t2", dataframe=df)
    mgr.insert_table(table, line_idx=0)
    assert "t2" in mgr.list_tables()
    mgr.save_document()
    saved = tmp_md_file.read_text()
    assert "id" in saved and "name" in saved
    assert "A" in saved and "B" in saved

def test_table_without_marker(tmp_md_file):
    content = [
        "| id | name |",
        "|----|------|",
        "| 1  | Alice |",
    ]
    tmp_md_file.write_text("\n".join(content))
    mgr = md_mod.MarkdownDocumentManager(tmp_md_file)
    assert len(mgr.tables) == 1
    tid = list(mgr.tables.keys())[0]
    assert tid.startswith("default-")

def test_insert_duplicate_table_id(tmp_md_file):
    mgr = md_mod.MarkdownDocumentManager(tmp_md_file)
    df = pd.DataFrame([{"id": "1", "name": "A"}])
    table1 = md_mod.MarkdownTable(table_id="dup", dataframe=df)
    mgr.insert_table(table1, line_idx=0)
    table2 = md_mod.MarkdownTable(table_id="dup", dataframe=df)
    with pytest.raises(ValueError):
        mgr.insert_table(table2, line_idx=1)
