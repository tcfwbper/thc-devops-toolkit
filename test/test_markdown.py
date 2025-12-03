import shutil
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from thc_devops_toolkit.documentation import markdown as md_mod


@pytest.fixture(scope="function")
def tmp_md_file():
    tmpdir = tempfile.mkdtemp()
    md_path = Path(tmpdir) / "test.md"
    yield md_path
    if md_path.exists():
        md_path.unlink()
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_dataframe_upsert_operations():
    # Test basic DataFrame operations
    df = pd.DataFrame([{"id": "1", "name": "Alice"}])
    assert df.shape[0] == 1

    # Update using pandas concat
    df_update = pd.DataFrame([{"id": "1", "name": "Bob"}])
    df = pd.concat([df[df["id"] != "1"], df_update], ignore_index=True)
    assert df.iloc[0]["name"] == "Bob"

    # Insert ahead
    df_new = pd.DataFrame([{"id": "2", "name": "Carol"}])
    df = pd.concat([df_new, df], ignore_index=True)
    assert df.iloc[0]["id"] == "2"


def test_generate_dataframe_marker():
    marker = md_mod.MarkdownDocumentManager.generate_dataframe_marker("dataframe-xyz")
    assert "dataframe_id=dataframe-xyz" in marker


def test_document_manager_parse_and_list_dataframes(tmp_md_file):
    content = [
        md_mod._comment_head + md_mod._dataframe_marker + " " + md_mod._dataframe_id_argument + "t1" + md_mod._comment_tail,
        "| id | name |",
        "|----|------|",
        "| 1  | Alice |",
        "| 2  | Bob   |",
        "",
        "Some text.",
    ]
    tmp_md_file.write_text("\n".join(content))
    mgr = md_mod.MarkdownDocumentManager(tmp_md_file)
    assert "t1" in mgr.dataframe_ids
    dataframe = mgr.get_dataframe("t1")
    assert isinstance(dataframe, pd.DataFrame)
    assert dataframe.shape[0] == 2
    assert dataframe.iloc[0]["name"] == "Alice"


def test_insert_dataframe_and_save(tmp_md_file):
    mgr = md_mod.MarkdownDocumentManager(tmp_md_file)
    df = pd.DataFrame([{"id": "1", "name": "A"}, {"id": "2", "name": "B"}])
    mgr.insert_dataframe(dataframe_id="t2", line_idx=0, dataframe=df)
    assert "t2" in mgr.dataframe_ids
    mgr.save()
    saved = tmp_md_file.read_text()
    assert "id" in saved and "name" in saved
    assert "A" in saved and "B" in saved


def test_dataframe_without_marker(tmp_md_file):
    # Without a marker, the document manager won't parse standalone tables
    content = [
        "| id | name |",
        "|----|------|",
        "| 1  | Alice |",
    ]
    tmp_md_file.write_text("\n".join(content))
    mgr = md_mod.MarkdownDocumentManager(tmp_md_file)
    # No dataframes should be detected without markers
    assert len(mgr.dataframe_ids) == 0


def test_insert_duplicate_dataframe_id(tmp_md_file):
    mgr = md_mod.MarkdownDocumentManager(tmp_md_file)
    df = pd.DataFrame([{"id": "1", "name": "A"}])
    mgr.insert_dataframe(dataframe_id="dup", line_idx=0, dataframe=df)
    df2 = pd.DataFrame([{"id": "2", "name": "B"}])
    with pytest.raises(ValueError):
        mgr.insert_dataframe(dataframe_id="dup", line_idx=1, dataframe=df2)
