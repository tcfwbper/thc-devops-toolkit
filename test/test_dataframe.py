from dataclasses import dataclass
from typing import ClassVar
import pandas as pd
import pytest
from thc_devops_toolkit.documentation.dataframe import (
    DataFrameRow,
    row_matches,
    upsert_row,
)


@dataclass
class TestRow(DataFrameRow):
    id: str
    name: str
    description: str
    primary_key: ClassVar[str] = "id"
    _highlightable_fields: ClassVar[frozenset[str]] = frozenset({"name", "description"})


def test_dataframe_row_id_property():
    row = TestRow(id="1", name="Alice", description="Test user")
    assert row.id == "1"


def test_dataframe_row_header():
    header = TestRow.header()
    assert header == ["id", "name", "description"]


def test_dataframe_row_from_dict():
    data = {"id": "1", "name": "Alice", "description": "Test user"}
    row = TestRow.from_dict(data)
    assert row.id == "1"
    assert row.name == "Alice"
    assert row.description == "Test user"


def test_dataframe_row_from_dict_with_unhighlight():
    data = {
        "id": "1",
        "name": '<span style="color:red">**Alice**</span>',
        "description": '<span style="color:red">**Test**</span>',
    }
    row = TestRow.from_dict(data, unhighlight_=True)
    assert row.name == "Alice"
    assert row.description == "Test"


def test_dataframe_row_from_dict_extra_fields():
    data = {"id": "1", "name": "Alice", "description": "Test", "extra": "ignored"}
    row = TestRow.from_dict(data)
    assert not hasattr(row, "extra")


def test_dataframe_row_to_dict():
    row = TestRow(id="1", name="Alice", description="Test user")
    result = row.to_dict()
    assert result == {"id": "1", "name": "Alice", "description": "Test user"}


def test_dataframe_row_highlight():
    row = TestRow(id="1", name="Alice", description="Test user")
    row.highlight()
    assert '<span style="color:red">**' in row.name
    assert '<span style="color:red">**' in row.description
    # primary key should not be highlighted
    assert '<span style="color:red">**' not in row.id


def test_dataframe_row_highlight_no_highlightable_fields():
    row = TestRow(id="1", name="Alice", description="Test user")
    row.highlight()
    # should not raise error and should not modify fields
    assert row.id == row.pk_value


def test_row_matches_found():
    df = pd.DataFrame([
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob"},
    ])
    result = row_matches(df, "id", "1")
    assert result.iloc[0] == True
    assert result.iloc[1] == False


def test_row_matches_not_found():
    df = pd.DataFrame([
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob"},
    ])
    result = row_matches(df, "id", "3")
    assert not result.any()


def test_upsert_row_insert():
    df = pd.DataFrame(columns=["id", "name", "description"])
    row = TestRow(id="1", name="Alice", description="Test")
    upsert_row(df, row)
    assert len(df) == 1
    assert df.iloc[0]["id"] == "1"
    assert df.iloc[0]["name"] == "Alice"


def test_upsert_row_update():
    df = pd.DataFrame([{"id": "1", "name": "Alice", "description": "Old"}])
    row = TestRow(id="1", name="Alice Updated", description="New")
    upsert_row(df, row)
    assert len(df) == 1
    assert df.iloc[0]["name"] == "Alice Updated"
    assert df.iloc[0]["description"] == "New"


def test_upsert_row_write_ahead():
    df = pd.DataFrame([{"id": "1", "name": "Alice", "description": "First"}])
    row = TestRow(id="2", name="Bob", description="Second")
    upsert_row(df, row, write_ahead=True)
    assert len(df) == 2
    df_index = df.index.to_list()
    assert df_index[0] == 1
    assert df_index[1] == 0


def test_upsert_row_append():
    df = pd.DataFrame([{"id": "1", "name": "Alice", "description": "First"}])
    row = TestRow(id="2", name="Bob", description="Second")
    upsert_row(df, row, write_ahead=False)
    assert len(df) == 2
    assert df.iloc[0]["id"] == "1"
    assert df.iloc[1]["id"] == "2"
