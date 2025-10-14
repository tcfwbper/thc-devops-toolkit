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
"""THC DevOps Toolkit Logger Module.

This module provides enhanced logging capabilities with ANSI color formatting support, rotating file handlers, and highlighted logging
methods for better console output visibility.
"""

import logging
import sys
from enum import Enum
from logging.handlers import TimedRotatingFileHandler
from typing import Union


class ANSIEscapeCode(Enum):
    """ANSI escape codes for terminal color and formatting.

    This enum provides standard ANSI escape codes for coloring and formatting
    terminal output. Supports both regular and bright color variants, as well
    as formatting options like bold and underline.

    Reference: https://en.wikipedia.org/wiki/ANSI_escape_code
    """

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    _END = "\033[0m"
    _BOLD = "\033[1m"
    _UNDERLINE = "\033[4m"

    def __str__(self) -> str:
        """Return the string representation of the ANSI escape code.

        Returns:
            str: The ANSI escape code value.
        """
        return str(self.value)

    def __add__(self, other: Union[str, "ANSIEscapeCode"]) -> str:
        """Allow concatenation with strings and other ANSIEscapeCode instances.

        Args:
            other: String or ANSIEscapeCode to concatenate with.

        Returns:
            str: Concatenated string result.
        """
        if isinstance(other, ANSIEscapeCode):
            return str(self) + str(other)
        return str(self) + str(other)

    def __radd__(self, other: Union[str, "ANSIEscapeCode"]) -> str:
        """Allow reverse concatenation with strings and other ANSIEscapeCode instances.

        Args:
            other: String or ANSIEscapeCode to concatenate with.

        Returns:
            str: Concatenated string result.
        """
        if isinstance(other, ANSIEscapeCode):
            return str(other) + str(self)
        return str(other) + str(self)


def ansi_format(text: str = "", color: ANSIEscapeCode = ANSIEscapeCode.BLUE, bold: bool = True, underline: bool = False) -> str:
    """Generate a colored/formatted string with ANSI escape codes.

    Args:
        text (str): The text to be colored/formatted.
        color (ANSIEscapeCode): The color to apply.
        bold (bool): Whether to apply bold formatting.
        underline (bool): Whether to apply underline formatting.

    Returns:
        str: The colored/formatted string.
    """
    codes = str(color)

    if bold:
        codes = codes + str(ANSIEscapeCode._BOLD)  # pylint: disable=protected-access

    if underline:
        codes = codes + str(ANSIEscapeCode._UNDERLINE)  # pylint: disable=protected-access

    return codes + text + str(ANSIEscapeCode._END)  # pylint: disable=protected-access


def get_file_handler(filename: str) -> logging.FileHandler:
    """Create a basic file handler for logging to a file.

    Args:
        filename (str): Path to the log file.

    Returns:
        logging.FileHandler: Configured file handler.
    """
    return logging.FileHandler(filename=filename)


def get_timed_rotating_file_handler(
    filename: str, when: str = "midnight", interval: int = 1, backupCount: int = 14  # pylint: disable=invalid-name
) -> TimedRotatingFileHandler:
    """Create a timed rotating file handler for log rotation.

    Args:
        filename (str): Path to the log file.
        when (str): Time interval type for rotation (default: "midnight").
        interval (int): Interval value for rotation (default: 1).
        backupCount (int): Number of backup files to keep (default: 14).

    Returns:
        TimedRotatingFileHandler: Configured rotating file handler.
    """
    return TimedRotatingFileHandler(filename=filename, when=when, interval=interval, backupCount=backupCount)


class THCLoggerHighlightLevel(Enum):
    """Enumeration of log levels for highlighted logging.

    This enum defines the available log levels that can be used with the highlight method of THCLogger for colored console output.
    """

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    CRITICAL = "CRITICAL"


class THCLogger(logging.Logger):
    """Enhanced logger class with ANSI color highlighting support.

    This logger extends the standard Python Logger with additional functionality
    for colored console output and simplified handler configuration.

    Attributes:
        formatter (logging.Formatter): The log message formatter.
        handlers (list[logging.Handler]): List of configured log handlers.
    """

    def __init__(
        self,
        name: str = "thc_devops_toolkit_logger",
        level: int = logging.DEBUG,
        formatter: logging.Formatter | None = None,
        handlers: list[logging.Handler] | None = None,
    ) -> None:
        """Initialize the THCLogger instance.

        Args:
            name (str): Logger name (default: "thc_devops_toolkit_logger").
            level (int): Logging level (default: logging.DEBUG).
            formatter (logging.Formatter | None): Custom formatter, if None uses default.
            handlers (list[logging.Handler] | None): List of handlers, if None uses stderr.
        """
        super().__init__(name, level)
        self.formatter = formatter or logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        self.handlers = handlers or [logging.StreamHandler(stream=sys.stderr)]
        for handler in self.handlers:
            handler.setLevel(level)
            handler.setFormatter(self.formatter)
            self.addHandler(handler)

    def highlight(self, level: THCLoggerHighlightLevel, message: str) -> None:
        """Log a message with ANSI color highlighting based on the log level.

        This method provides colored console output for different log levels
        to improve readability and visual distinction of log messages.

        Args:
            level (THCLoggerHighlightLevel): The highlight level determining color.
            message (str): The message to log with highlighting.
        """
        if level == THCLoggerHighlightLevel.ERROR:
            self.error(ansi_format(text=message, color=ANSIEscapeCode.RED, bold=True, underline=False))
        elif level == THCLoggerHighlightLevel.WARNING:
            self.warning(ansi_format(text=message, color=ANSIEscapeCode.YELLOW, bold=True, underline=False))
        elif level == THCLoggerHighlightLevel.INFO:
            self.info(ansi_format(text=message, color=ANSIEscapeCode.BLUE, bold=True, underline=False))
        elif level == THCLoggerHighlightLevel.DEBUG:
            self.debug(ansi_format(text=message, color=ANSIEscapeCode.GREEN, bold=True, underline=False))

        elif level == THCLoggerHighlightLevel.CRITICAL:
            self.critical(ansi_format(text=message, color=ANSIEscapeCode.MAGENTA, bold=True, underline=False))


thc_logger = THCLogger()
