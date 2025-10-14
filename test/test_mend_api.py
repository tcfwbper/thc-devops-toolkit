import pytest
from unittest.mock import patch, MagicMock

import thc_devops_toolkit.security.mend_api_helper as mend

def test_get_refresh_token_success():
    with patch("thc_devops_toolkit.security.mend_api_helper.requests.post") as post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": {"refreshToken": "REFRESH"}}
        post.return_value = mock_resp
        token = mend.get_refresh_token("user@example.com", "userkey")
        assert token == "REFRESH"
        post.assert_called_once()
        args, kwargs = post.call_args
        assert "login" in args[0]
        assert kwargs["headers"]["Content-Type"] == "application/json"

def test_get_jwt_token_success():
    with patch("thc_devops_toolkit.security.mend_api_helper.requests.post") as post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": {"jwtToken": "JWT"}}
        post.return_value = mock_resp
        token = mend.get_jwt_token("REFRESH")
        assert token == "JWT"
        post.assert_called_once()
        args, kwargs = post.call_args
        assert "accessToken" in args[0]
        assert kwargs["headers"]["wss-refresh-token"] == "REFRESH"

def test_get_alerts_by_library_success():
    with patch("thc_devops_toolkit.security.mend_api_helper.requests.get") as get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"retVal": [{"lib1": []}, {"lib2": []}]}
        get.return_value = mock_resp
        data = mend.get_alerts_by_library("projtoken", "jwt")
        assert isinstance(data, list)
        assert len(data) == 2
        get.assert_called_once()
        args, kwargs = get.call_args
        assert "groupBy/component" in args[0]
        assert kwargs["headers"]["Authorization"].startswith("Bearer ")

def test_get_alerts_by_library_type_error():
    with patch("thc_devops_toolkit.security.mend_api_helper.requests.get") as get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"retVal": "not a list"}
        get.return_value = mock_resp
        with pytest.raises(ValueError):
            mend.get_alerts_by_library("projtoken", "jwt")

def test_get_vulnerabilities_by_project_success():
    with patch("thc_devops_toolkit.security.mend_api_helper.requests.get") as get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"retVal": [{"vuln1": {}}, {"vuln2": {}}]}
        get.return_value = mock_resp
        data = mend.get_vulnerabilities_by_project("projtoken", "jwt")
        assert isinstance(data, list)
        assert len(data) == 2
        get.assert_called_once()
        args, kwargs = get.call_args
        assert "alerts/security" in args[0]
        assert kwargs["headers"]["Authorization"].startswith("Bearer ")

def test_get_vulnerabilities_by_project_type_error():
    with patch("thc_devops_toolkit.security.mend_api_helper.requests.get") as get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"retVal": "not a list"}
        get.return_value = mock_resp
        with pytest.raises(ValueError):
            mend.get_vulnerabilities_by_project("projtoken", "jwt")
