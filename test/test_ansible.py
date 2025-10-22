import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Any

from thc_devops_toolkit.infrastructure.ansible import Playbook


class TestPlaybook:
    """Test implementation of the Playbook abstract class for testing."""
    
    class ConcretePlaybook(Playbook):
        """Concrete implementation for testing purposes."""
        
        def __init__(self, playbook_file: str | Path, inventory_file: str | Path, 
                     limit: str, extravars: dict[str, Any],
                     vars_overrides: dict[str, Any] = None,
                     mandatory_vars: set[str] = None):
            super().__init__(playbook_file, inventory_file, limit, extravars)
            self._vars_overrides = vars_overrides or {}
            self._mandatory_vars = mandatory_vars or set()
        
        @property
        def vars_overrides(self) -> dict[str, Any]:
            return self._vars_overrides
        
        @property
        def mandatory_vars(self) -> set[str]:
            return self._mandatory_vars

    def test_init(self):
        """Test Playbook initialization."""
        playbook = self.ConcretePlaybook(
            playbook_file="/path/to/playbook.yml",
            inventory_file="/path/to/inventory",
            limit="all",
            extravars={"var1": "value1"}
        )
        
        assert playbook.playbook_file == "/path/to/playbook.yml"
        assert playbook.inventory_file == "/path/to/inventory"
        assert playbook.limit == "all"
        assert playbook.extravars == {"var1": "value1"}

    def test_init_with_path_objects(self):
        """Test Playbook initialization with Path objects."""
        playbook = self.ConcretePlaybook(
            playbook_file=Path("/path/to/playbook.yml"),
            inventory_file=Path("/path/to/inventory"),
            limit="webservers",
            extravars={"env": "prod"}
        )
        
        assert playbook.playbook_file == "/path/to/playbook.yml"
        assert playbook.inventory_file == "/path/to/inventory"

    def test_verify_extravars_success(self):
        """Test successful extravar verification."""
        playbook = self.ConcretePlaybook(
            playbook_file="test.yml",
            inventory_file="inventory",
            limit="all",
            extravars={"required_var": "value", "optional_var": "value2"},
            mandatory_vars={"required_var"}
        )
        
        # Should not raise any exception
        playbook.verify_extravars()

    def test_verify_extravars_missing_vars(self):
        """Test extravar verification with missing mandatory variables."""
        playbook = self.ConcretePlaybook(
            playbook_file="test.yml",
            inventory_file="inventory",
            limit="all",
            extravars={"optional_var": "value"},
            mandatory_vars={"required_var", "another_required_var"}
        )
        
        with pytest.raises(ValueError, match="Missing mandatory extravars: required_var, another_required_var"):
            playbook.verify_extravars()

    def test_override_vars(self):
        """Test variable override functionality."""
        playbook = self.ConcretePlaybook(
            playbook_file="test.yml",
            inventory_file="inventory",
            limit="all",
            extravars={"var1": "original", "var2": "keep"},
            vars_overrides={"var1": "overridden", "var3": "new"}
        )
        
        playbook.override_vars()
        
        expected_extravars = {
            "var1": "overridden",
            "var2": "keep", 
            "var3": "new"
        }
        assert playbook.extravars == expected_extravars

    @patch('thc_devops_toolkit.infrastructure.ansible.ansible_runner.run')
    @patch('thc_devops_toolkit.infrastructure.ansible.logger')
    def test_run_success(self, mock_logger, mock_ansible_run):
        """Test successful playbook execution."""
        # Setup mock
        mock_runner = Mock()
        mock_runner.rc = 0
        mock_runner.events = [
            {"stdout": "Task 1 output"},
            {"event": "playbook_on_start"},
            {"stdout": "Task 2 output"},
        ]
        mock_ansible_run.return_value = mock_runner
        
        playbook = self.ConcretePlaybook(
            playbook_file="test.yml",
            inventory_file="inventory",
            limit="all",
            extravars={"var1": "value1"},
            vars_overrides={"override_var": "override_value"},
            mandatory_vars={"var1"}
        )
        
        result = playbook.run()
        
        # Verify ansible_runner.run was called with correct parameters
        mock_ansible_run.assert_called_once_with(
            playbook="test.yml",
            inventory="inventory",
            extravars={"var1": "value1", "override_var": "override_value"},
            limit="all"
        )
        
        # Verify return value
        assert result == "Task 1 output\nTask 2 output"
        
        # Verify logging
        mock_logger.info.assert_called()

    @patch('thc_devops_toolkit.infrastructure.ansible.ansible_runner.run')
    @patch('thc_devops_toolkit.infrastructure.ansible.logger')
    def test_run_failure(self, mock_logger, mock_ansible_run):
        """Test playbook execution failure."""
        # Setup mock
        mock_runner = Mock()
        mock_runner.rc = 1
        mock_runner.events = [
            {"stdout": "Error output"},
        ]
        mock_ansible_run.return_value = mock_runner
        
        playbook = self.ConcretePlaybook(
            playbook_file="test.yml",
            inventory_file="inventory",
            limit="all",
            extravars={"var1": "value1"},
            mandatory_vars={"var1"}
        )
        
        with pytest.raises(RuntimeError, match="Playbook execution failed: Error output"):
            playbook.run()
        
        # Verify error logging
        mock_logger.highlight.assert_called()

    @patch('thc_devops_toolkit.infrastructure.ansible.ansible_runner.run')
    def test_run_with_missing_mandatory_vars(self, mock_ansible_run):
        """Test that run fails when mandatory variables are missing."""
        playbook = self.ConcretePlaybook(
            playbook_file="test.yml",
            inventory_file="inventory",
            limit="all",
            extravars={"optional_var": "value"},
            mandatory_vars={"required_var"}
        )
        
        with pytest.raises(ValueError, match="Missing mandatory extravars: required_var"):
            playbook.run()
        
        # Verify ansible_runner.run was not called
        mock_ansible_run.assert_not_called()

    @patch('thc_devops_toolkit.infrastructure.ansible.ansible_runner.run')
    def test_run_no_stdout_events(self, mock_ansible_run):
        """Test playbook execution with no stdout events."""
        mock_runner = Mock()
        mock_runner.rc = 0
        mock_runner.events = [
            {"event": "playbook_on_start"},
            {"event": "playbook_on_task_start"},
        ]
        mock_ansible_run.return_value = mock_runner
        
        playbook = self.ConcretePlaybook(
            playbook_file="test.yml",
            inventory_file="inventory",
            limit="all",
            extravars={}
        )
        
        result = playbook.run()
        assert result == ""

    def test_abstract_methods_not_implemented(self):
        """Test that abstract methods raise NotImplementedError when not implemented."""
        with pytest.raises(TypeError):
            # This should fail because Playbook is abstract
            Playbook("test.yml", "inventory", "all", {})
