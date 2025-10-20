import logging
import tempfile
import shutil
from io import StringIO
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from thc_devops_toolkit.observability.logger import (
    ANSIEscapeCode,
    THCLogger,
    LogLevel,
    ansi_format,
    get_file_handler,
    get_timed_rotating_file_handler,
    logger,
)


@pytest.fixture(scope="function")
def tmp_log_file():
    """Create a temporary log file for testing."""
    tmpdir = tempfile.mkdtemp()
    log_path = Path(tmpdir) / "test.log"
    yield log_path
    if log_path.exists():
        log_path.unlink()
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture(scope="function")
def string_handler():
    """Create a StringIO handler for capturing log output."""
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.stream = stream
    return handler


class TestANSIEscapeCode:
    """Test cases for ANSIEscapeCode enum."""

    def test_ansi_escape_code_values(self):
        """Test that ANSI escape codes have correct values."""
        assert str(ANSIEscapeCode.RED) == "\033[31m"
        assert str(ANSIEscapeCode.GREEN) == "\033[32m"
        assert str(ANSIEscapeCode.BLUE) == "\033[34m"
        assert str(ANSIEscapeCode.BRIGHT_RED) == "\033[91m"
        assert str(ANSIEscapeCode._END) == "\033[0m"
        assert str(ANSIEscapeCode._BOLD) == "\033[1m"
        assert str(ANSIEscapeCode._UNDERLINE) == "\033[4m"

    def test_ansi_escape_code_str_method(self):
        """Test the __str__ method of ANSIEscapeCode."""
        code = ANSIEscapeCode.YELLOW
        assert str(code) == "\033[33m"

    def test_ansi_escape_code_addition(self):
        """Test addition operations with ANSIEscapeCode."""
        # Test adding string to ANSIEscapeCode
        result = ANSIEscapeCode.RED + "hello"
        assert result == "\033[31mhello"

        # Test adding ANSIEscapeCode to ANSIEscapeCode
        result = ANSIEscapeCode.RED + ANSIEscapeCode.BLUE
        assert result == "\033[31m\033[34m"

    def test_ansi_escape_code_reverse_addition(self):
        """Test reverse addition operations with ANSIEscapeCode."""
        # Test adding ANSIEscapeCode to string
        result = "hello" + ANSIEscapeCode.RED
        assert result == "hello\033[31m"

        # Test reverse addition of ANSIEscapeCode to ANSIEscapeCode
        result = ANSIEscapeCode.BLUE + ANSIEscapeCode.RED
        assert result == "\033[34m\033[31m"


class TestAnsiFormat:
    """Test cases for ansi_format function."""

    def test_ansi_format_default_parameters(self):
        """Test ansi_format with default parameters."""
        result = ansi_format("test")
        expected = "\033[34m\033[1mtest\033[0m"  # Blue + Bold + text + End
        assert result == expected

    def test_ansi_format_custom_color(self):
        """Test ansi_format with custom color."""
        result = ansi_format("test", color=ANSIEscapeCode.RED)
        expected = "\033[31m\033[1mtest\033[0m"  # Red + Bold + text + End
        assert result == expected

    def test_ansi_format_no_bold(self):
        """Test ansi_format without bold formatting."""
        result = ansi_format("test", bold=False)
        expected = "\033[34mtest\033[0m"  # Blue + text + End
        assert result == expected

    def test_ansi_format_with_underline(self):
        """Test ansi_format with underline formatting."""
        result = ansi_format("test", underline=True)
        expected = "\033[34m\033[1m\033[4mtest\033[0m"  # Blue + Bold + Underline + text + End
        assert result == expected

    def test_ansi_format_all_options(self):
        """Test ansi_format with all formatting options."""
        result = ansi_format("test", color=ANSIEscapeCode.GREEN, bold=True, underline=True)
        expected = "\033[32m\033[1m\033[4mtest\033[0m"  # Green + Bold + Underline + text + End
        assert result == expected

    def test_ansi_format_empty_text(self):
        """Test ansi_format with empty text."""
        result = ansi_format("")
        expected = "\033[34m\033[1m\033[0m"  # Blue + Bold + End
        assert result == expected


class TestFileHandlers:
    """Test cases for file handler functions."""

    def test_get_file_handler(self, tmp_log_file):
        """Test get_file_handler function."""
        handler = get_file_handler(str(tmp_log_file))
        assert isinstance(handler, logging.FileHandler)
        assert handler.baseFilename == str(tmp_log_file)

    def test_get_timed_rotating_file_handler_default(self, tmp_log_file):
        """Test get_timed_rotating_file_handler with default parameters."""
        handler = get_timed_rotating_file_handler(str(tmp_log_file))
        assert isinstance(handler, TimedRotatingFileHandler)
        assert handler.when == "MIDNIGHT"
        assert handler.interval == 86400  # 1 day in seconds
        assert handler.backupCount == 14

    def test_get_timed_rotating_file_handler_custom(self, tmp_log_file):
        """Test get_timed_rotating_file_handler with custom parameters."""
        handler = get_timed_rotating_file_handler(
            str(tmp_log_file), when="H", interval=2, backupCount=10
        )
        assert isinstance(handler, TimedRotatingFileHandler)
        assert handler.when == "H"
        assert handler.interval == 7200  # 2 hours in seconds
        assert handler.backupCount == 10


class TestLogLevel:
    """Test cases for LogLevel enum."""

    def test_highlight_level_values(self):
        """Test that highlight levels have correct values."""
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.CRITICAL.value == "CRITICAL"


class TestTHCLogger:
    """Test cases for THCLogger class."""

    def test_logger_initialization_default(self):
        """Test THCLogger initialization with default parameters."""
        logger = THCLogger()
        assert logger.name == "thc_devops_toolkit_logger"
        assert logger.level == logging.DEBUG
        assert logger.formatter is not None
        assert len(logger.handlers) > 0

    def test_logger_initialization_custom(self, string_handler):
        """Test THCLogger initialization with custom parameters."""
        custom_formatter = logging.Formatter("%(message)s")
        custom_handlers = [string_handler]
        
        logger = THCLogger(
            name="test_logger",
            level=logging.INFO,
            formatter=custom_formatter,
            handlers=custom_handlers
        )
        
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        assert logger.formatter == custom_formatter

    def test_logger_highlight_error(self, string_handler):
        """Test highlight method with ERROR level."""
        logger = THCLogger(handlers=[string_handler])
        logger.highlight(LogLevel.ERROR, "error message")
        
        output = string_handler.stream.getvalue()
        assert "error message" in output
        assert "\033[31m" in output  # Red color code

    def test_logger_highlight_warning(self, string_handler):
        """Test highlight method with WARNING level."""
        logger = THCLogger(handlers=[string_handler])
        logger.highlight(LogLevel.WARNING, "warning message")
        
        output = string_handler.stream.getvalue()
        assert "warning message" in output
        assert "\033[33m" in output  # Yellow color code

    def test_logger_highlight_info(self, string_handler):
        """Test highlight method with INFO level."""
        logger = THCLogger(handlers=[string_handler])
        logger.highlight(LogLevel.INFO, "info message")
        
        output = string_handler.stream.getvalue()
        assert "info message" in output
        assert "\033[34m" in output  # Blue color code

    def test_logger_highlight_debug(self, string_handler):
        """Test highlight method with DEBUG level."""
        logger = THCLogger(handlers=[string_handler])
        logger.highlight(LogLevel.DEBUG, "debug message")
        
        output = string_handler.stream.getvalue()
        assert "debug message" in output
        assert "\033[32m" in output  # Green color code

    def test_logger_highlight_critical(self, string_handler):
        """Test highlight method with CRITICAL level."""
        logger = THCLogger(handlers=[string_handler])
        logger.highlight(LogLevel.CRITICAL, "critical message")
        
        output = string_handler.stream.getvalue()
        assert "critical message" in output
        assert "\033[35m" in output  # Magenta color code

    def test_logger_regular_logging_methods(self, string_handler):
        """Test that regular logging methods still work."""
        logger = THCLogger(handlers=[string_handler])
        
        logger.info("regular info")
        logger.error("regular error")
        logger.warning("regular warning")
        logger.debug("regular debug")
        logger.critical("regular critical")
        
        output = string_handler.stream.getvalue()
        assert "regular info" in output
        assert "regular error" in output
        assert "regular warning" in output
        assert "regular debug" in output
        assert "regular critical" in output


class TestGlobalLogger:
    """Test cases for the global logger instance."""

    def test_global_logger_exists(self):
        """Test that the global logger instance exists and is properly configured."""
        assert isinstance(logger, THCLogger)
        assert logger.name == "thc_devops_toolkit_logger"
        assert logger.level == logging.DEBUG

    def test_global_logger_functionality(self):
        """Test that the global logger can perform basic operations."""
        # Create a StringIO handler to capture output
        stream = StringIO()
        test_handler = logging.StreamHandler(stream)
        test_handler.setLevel(logging.DEBUG)
        test_handler.setFormatter(logging.Formatter('%(message)s'))
        
        # Temporarily replace handlers
        original_handlers = logger.handlers.copy()
        logger.handlers.clear()
        logger.addHandler(test_handler)
        
        try:
            logger.info("test message")
            output = stream.getvalue()
            assert "test message" in output
        finally:
            # Restore original handlers
            logger.handlers.clear()
            for handler in original_handlers:
                logger.addHandler(handler)

    def test_global_logger_highlight_functionality(self):
        """Test that the global logger highlight method works."""
        # Create a StringIO handler to capture output
        stream = StringIO()
        test_handler = logging.StreamHandler(stream)
        test_handler.setLevel(logging.DEBUG)
        test_handler.setFormatter(logging.Formatter('%(message)s'))
        
        # Temporarily replace handlers
        original_handlers = logger.handlers.copy()
        logger.handlers.clear()
        logger.addHandler(test_handler)
        
        try:
            logger.highlight(LogLevel.INFO, "highlighted test")
            output = stream.getvalue()
            assert "highlighted test" in output
            assert "\033[34m" in output  # Blue color code
        finally:
            # Restore original handlers
            logger.handlers.clear()
            for handler in original_handlers:
                logger.addHandler(handler)
