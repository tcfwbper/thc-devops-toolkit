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
"""Module for handling data frame rows in documentation."""

from abc import ABC
from collections.abc import Hashable
from dataclasses import dataclass, fields
from typing import Any, ClassVar, TypeVar

import pandas as pd

from .text import highlight, unhighlight

DataFrameRowLike = TypeVar("DataFrameRowLike", bound="DataFrameRow")


@dataclass
class DataFrameRow(ABC):
    """Abstract base class for data frame rows.

    Attributes:
        primary_key (ClassVar[str]): Primary key field name. It must be one of the dataclass fields.
        _highlightable_fields (ClassVar[frozenset[str]]): Set of field names that can be highlighted. \
            These fields must be string type.
    """

    primary_key: ClassVar[str]
    _highlightable_fields: ClassVar[frozenset[str]] = frozenset()

    @property
    def pk_value(self) -> Any:
        """Returns the value representation of the primary key field.

        Returns:
            Any: Primary key field value.
        """
        return getattr(self, self.primary_key)

    @classmethod
    def header(cls: type[DataFrameRowLike]) -> list[Hashable]:
        """Returns the header for the data frame.

        Returns:
            list[Hashable]: Data frame header.
        """
        return [field.name for field in fields(cls)]

    @classmethod
    def from_dict(cls: type[DataFrameRowLike], data: dict[Hashable, Any], unhighlight_: bool = False) -> DataFrameRowLike:
        """Creates an DataFrameRowLike instance from a dictionary.

        Args:
            data (dict[Hashable, Any]): Dictionary containing DataFrameRowLike fields.
            unhighlight_ (bool): Whether to unhighlight text fields.

        Returns:
            DataFrameRowLike: New DataFrameRowLike instance.
        """
        field_names = {field.name for field in fields(cls)}

        return cls(
            **{
                key: unhighlight(value) if unhighlight_ and isinstance(value, str) else value
                for key, value in data.items()
                if key in field_names
            }
        )

    def to_dict(self) -> dict[Hashable, Any]:
        """Converts DataFrameRow instance to a dictionary.

        Returns:
            dict[Hashable, Any]: Dictionary representation of DataFrameRow.
        """
        return {field.name: getattr(self, field.name) for field in fields(self)}

    def highlight(self) -> None:
        """Highlights the fields specified in _highlightable_fields."""
        if not self._highlightable_fields:
            return

        header = set(self.header())

        for field_name in self._highlightable_fields:
            # don't highlight primary key field to ensure the correctness of matching
            if all(
                (
                    isinstance(field_name, str),
                    field_name in header,
                    field_name != self.primary_key,
                )
            ):
                setattr(self, field_name, highlight(str(getattr(self, field_name))))


def row_matches(dataframe: pd.DataFrame, key: Hashable, value: Any) -> pd.Series:
    """Checks which rows in the DataFrame match the given key-value pair.

    Args:
        dataframe (pd.DataFrame): The DataFrame to search.
        key (Hashable): The column name to search.
        value (Any): The value to match.

    Returns:
        pd.Series[bool]: A boolean Series indicating matching rows.
    """
    condition = pd.Series([True] * len(dataframe))
    condition &= pd.Series(dataframe[key] == value)
    return condition


def upsert_row(dataframe: pd.DataFrame, data: DataFrameRowLike, write_ahead: bool = False) -> None:
    """In-place inserts or updates a row to the DataFrame based on the primary key.

    Args:
        dataframe (pd.DataFrame): The DataFrame to modify.
        data (DataFrameRowLike): The data item to insert or update.
        write_ahead (bool): If True, inserts new rows at the beginning. Defaults to False.
    """
    condition = row_matches(dataframe=dataframe, key=data.primary_key, value=data.pk_value)

    # hit
    if condition.any():
        row_idx = dataframe[condition].index[0]
        for key, value in data.to_dict().items():
            dataframe.at[row_idx, key] = value
    # new data
    else:
        # write ahead
        if write_ahead:
            dataframe.index = dataframe.index + 1
            dataframe.sort_index(inplace=True)
            # insert data
            dataframe.loc[0] = data.to_dict()
        # append
        else:
            dataframe.loc[len(dataframe)] = data.to_dict()
