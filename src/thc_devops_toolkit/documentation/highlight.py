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
"""Functions for highlighting text in markdown documents."""

_highlight_head: str = '<span style="color:red">**'
_highlight_tail: str = "**</span>"


def highlight(text: str) -> str:
    """Highlights the given text using HTML span tags.

    Args:
        text (str): The text to be highlighted.

    Returns:
        str: The highlighted text.
    """
    if text.startswith(_highlight_head) and text.endswith(_highlight_tail):
        return text

    return f"{_highlight_head}{text}{_highlight_tail}"


def unhighlight(text: str) -> str:
    """Removes highlighting from the given text.

    Args:
        text (str): The text from which to remove highlighting.

    Returns:
        str: The unhighlighted text.
    """
    text = text.replace(_highlight_head, "")
    text = text.replace(_highlight_tail, "")
    return text
