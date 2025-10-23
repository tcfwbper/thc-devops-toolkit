import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thc_devops_toolkit.utils.cython_builder import CythonBuilder


class TestCythonBuilder(unittest.TestCase):
    """Test cases for CythonBuilder class."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_src = Path(self.temp_dir) / "test_src"
        self.test_src.mkdir()
        
        # Create some test Python files
        (self.test_src / "__init__.py").write_text("# init file\n")
        (self.test_src / "module1.py").write_text("def hello():\n    return 'world'\n")
        
        # Create a subdirectory with files
        subdir = self.test_src / "subpackage"
        subdir.mkdir()
        (subdir / "__init__.py").write_text("# subpackage init\n")
        (subdir / "module2.py").write_text("def foo():\n    return 'bar'\n")

    def tearDown(self) -> None:
        """Clean up test fixtures after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_with_valid_directory(self) -> None:
        """Test CythonBuilder initialization with a valid directory."""
        builder = CythonBuilder(self.test_src)
        self.assertEqual(builder._src, self.test_src)
        self.assertEqual(builder._dst, Path("build"))

    def test_init_with_string_path(self) -> None:
        """Test CythonBuilder initialization with a string path."""
        builder = CythonBuilder(str(self.test_src))
        self.assertEqual(builder._src, self.test_src)

    def test_init_with_nonexistent_directory(self) -> None:
        """Test CythonBuilder initialization with a non-existent directory."""
        nonexistent = Path(self.temp_dir) / "nonexistent"
        with self.assertRaises(ValueError) as cm:
            CythonBuilder(nonexistent)
        self.assertIn("is not a directory", str(cm.exception))

    def test_init_with_file_instead_of_directory(self) -> None:
        """Test CythonBuilder initialization with a file instead of directory."""
        test_file = Path(self.temp_dir) / "test_file.py"
        test_file.write_text("# test file")
        
        with self.assertRaises(ValueError) as cm:
            CythonBuilder(test_file)
        self.assertIn("is not a directory", str(cm.exception))

    def test_remove_pycache(self) -> None:
        """Test removal of __pycache__ directories."""
        # Create __pycache__ directories
        pycache1 = self.test_src / "__pycache__"
        pycache1.mkdir()
        pycache2 = self.test_src / "subpackage" / "__pycache__"
        pycache2.mkdir()
        
        builder = CythonBuilder(self.test_src)
        builder._remove_pycache()
        
        # Verify __pycache__ directories are removed
        self.assertFalse(pycache1.exists())
        self.assertFalse(pycache2.exists())

    def test_remove_dst(self) -> None:
        """Test removal of destination build directory."""
        builder = CythonBuilder(self.test_src)
        
        # Create a previous build directory
        previous_build = builder._dst / self.test_src.name
        previous_build.mkdir(parents=True)
        
        builder._remove_dst()
        
        # Verify build directory is removed
        self.assertFalse(previous_build.exists())

    def test_setup_temp_dir(self) -> None:
        """Test setting up temporary directory with file copying and .py to .pyx transformation."""
        builder = CythonBuilder(self.test_src)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_src = Path(temp_dir) / "temp_src"
            builder._setup_temp_dir(temp_src)
            
            # Verify files are copied and transformed
            self.assertTrue((temp_src / "__init__.pyx").exists())
            self.assertTrue((temp_src / "module1.pyx").exists())
            self.assertTrue((temp_src / "subpackage" / "__init__.pyx").exists())
            self.assertTrue((temp_src / "subpackage" / "module2.pyx").exists())
            
            # Verify content is preserved
            content = (temp_src / "module1.pyx").read_text()
            self.assertEqual(content, "def hello():\n    return 'world'\n")

    def test_ensure_initializer(self) -> None:
        """Test ensuring __init__.pyx files exist in all directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_src = Path(temp_dir) / "temp_src"
            temp_src.mkdir()
            
            # Create a subdirectory without __init__.pyx
            subdir = temp_src / "subdir"
            subdir.mkdir()
            
            CythonBuilder._ensure_initializer(temp_src)
            
            # Verify __init__.pyx files are created
            self.assertTrue((temp_src / "__init__.pyx").exists())
            self.assertTrue((subdir / "__init__.pyx").exists())

    def test_setup_temp_dir_with_non_python_files(self) -> None:
        """Test setup_temp_dir handles non-Python files correctly."""
        # Create a non-Python file
        (self.test_src / "config.txt").write_text("configuration data")
        
        builder = CythonBuilder(self.test_src)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_src = Path(temp_dir) / "temp_src"
            builder._setup_temp_dir(temp_src)
            
            # Verify non-Python file is copied without transformation
            self.assertTrue((temp_src / "config.txt").exists())
            content = (temp_src / "config.txt").read_text()
            self.assertEqual(content, "configuration data")

    @patch('thc_devops_toolkit.utils.cython_builder.setup')
    @patch('thc_devops_toolkit.utils.cython_builder.cythonize')
    def test_build_success(self, mock_cythonize: MagicMock, mock_setup: MagicMock) -> None:
        """Test successful build process."""
        mock_cythonize.return_value = []
        
        builder = CythonBuilder(self.test_src)
        builder.build()
        
        # Verify cythonize was called
        mock_cythonize.assert_called_once()
        args, kwargs = mock_cythonize.call_args
        
        # Verify .pyx files were passed to cythonize
        pyx_files = args[0]
        self.assertTrue(any(file.endswith("__init__.pyx") for file in pyx_files))
        self.assertTrue(any(file.endswith("module1.pyx") for file in pyx_files))
        
        # Verify compiler directives
        self.assertEqual(kwargs["compiler_directives"]["annotation_typing"], False)
        
        # Verify setup was called
        mock_setup.assert_called_once()

    @patch('thc_devops_toolkit.utils.cython_builder.setup')
    @patch('thc_devops_toolkit.utils.cython_builder.cythonize')
    def test_build_with_custom_compiler_directives(self, mock_cythonize: MagicMock, mock_setup: MagicMock) -> None:
        """Test build with custom compiler directives."""
        mock_cythonize.return_value = []
        custom_directives = {"boundscheck": False, "wraparound": False}
        
        builder = CythonBuilder(self.test_src)
        builder.build(compiler_directives=custom_directives)
        
        # Verify custom directives are merged with defaults
        args, kwargs = mock_cythonize.call_args
        expected_directives = {"annotation_typing": False, "boundscheck": False, "wraparound": False}
        self.assertEqual(kwargs["compiler_directives"], expected_directives)

    @patch('thc_devops_toolkit.utils.cython_builder.setup')
    @patch('thc_devops_toolkit.utils.cython_builder.cythonize')
    @patch('thc_devops_toolkit.utils.cython_builder.sys')
    def test_build_preserves_sys_argv(self, mock_sys: MagicMock, mock_cythonize: MagicMock, mock_setup: MagicMock) -> None:
        """Test that build process preserves original sys.argv."""
        original_argv = ["original", "args"]
        mock_sys.argv = original_argv.copy()
        mock_cythonize.return_value = []
        
        builder = CythonBuilder(self.test_src)
        builder.build()
        
        # Verify sys.argv is restored
        self.assertEqual(mock_sys.argv, original_argv)

    @patch('thc_devops_toolkit.utils.cython_builder.setup')
    @patch('thc_devops_toolkit.utils.cython_builder.cythonize')
    @patch('thc_devops_toolkit.utils.cython_builder.sys')
    def test_build_exception_handling(self, mock_sys: MagicMock, mock_cythonize: MagicMock, mock_setup: MagicMock) -> None:
        """Test that sys.argv is restored even if setup raises an exception."""
        original_argv = ["original", "args"]
        mock_sys.argv = original_argv.copy()
        mock_cythonize.return_value = []
        mock_setup.side_effect = Exception("Build failed")
        
        builder = CythonBuilder(self.test_src)
        
        with self.assertRaises(Exception):
            builder.build()
        
        # Verify sys.argv is restored even after exception
        self.assertEqual(mock_sys.argv, original_argv)


if __name__ == "__main__":
    unittest.main()