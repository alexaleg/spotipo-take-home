"""
Tests for the UniFi API client.
External Hotspot API: https://help.ui.com/hc/en-us/articles/31228198640023
Execute client action: https://developer.ui.com/network/v1/executeconnectedclientaction
Authentication (X-API-KEY): https://developer.ui.com/site-manager/v1.0.0/gettingstarted
"""

from unittest.mock import MagicMock, patch

import pytest

from app.unifi import UniFiClient, UniFiError


def _make_client() -> UniFiClient:
    return UniFiClient(
        host="https://192.168.1.1",
        api_key="test-api-key",
        site_id="abc123",
        verify_ssl=False,
    )


def _ok_response(data=None) -> MagicMock:
    response = MagicMock()
    response.ok = True
    response.json.return_value = data if data is not None else {}
    return response


def _clients_response(client_id: str, mac: str = "AA:BB:CC:DD:EE:FF") -> MagicMock:
    return _ok_response([{"id": client_id, "macAddress": mac, "type": "WIRELESS"}])


def _error_response(status_code: int = 400, msg: str = "bad request") -> MagicMock:
    response = MagicMock()
    response.ok = False
    response.status_code = status_code
    response.text = msg
    return response


class TestInit:
    def test_api_key_set_in_session_headers(self):
        client = _make_client()
        assert client._session.headers["X-API-KEY"] == "test-api-key"


class TestGetClientId:
    def test_returns_client_id_from_response(self):
        client = _make_client()
        mock_response = _clients_response("clientXYZ")
        with patch.object(client._session, "get", return_value=mock_response):
            result = client.get_client_id("AA:BB:CC:DD:EE:FF")
        assert result == "clientXYZ"

    def test_sends_mac_filter_param(self):
        client = _make_client()
        mock_get = MagicMock(return_value=_clients_response("clientXYZ"))
        with patch.object(client._session, "get", mock_get):
            client.get_client_id("aa:bb:cc:dd:ee:ff")
        params = mock_get.call_args[1]["params"]
        assert "macAddress.eq" in params["filter"]

    def test_uppercases_mac_in_filter(self):
        client = _make_client()
        mock_get = MagicMock(return_value=_clients_response("clientXYZ"))
        with patch.object(client._session, "get", mock_get):
            client.get_client_id("aa:bb:cc:dd:ee:ff")
        params = mock_get.call_args[1]["params"]
        assert "AA:BB:CC:DD:EE:FF" in params["filter"]

    def test_raises_when_client_list_is_empty(self):
        client = _make_client()
        with patch.object(client._session, "get", return_value=_ok_response([])):
            with pytest.raises(UniFiError, match="not found"):
                client.get_client_id("AA:BB:CC:DD:EE:FF")

    def test_raises_on_http_error(self):
        client = _make_client()
        with patch.object(client._session, "get", return_value=_error_response(401)):
            with pytest.raises(UniFiError, match="HTTP 401"):
                client.get_client_id("AA:BB:CC:DD:EE:FF")


class TestAuthorizeGuest:
    def test_sends_correct_action_and_time_limit(self):
        client = _make_client()
        mock_get = MagicMock(return_value=_clients_response("clientXYZ"))
        mock_post = MagicMock(return_value=_ok_response())
        with (
            patch.object(client._session, "get", mock_get),
            patch.object(client._session, "post", mock_post),
        ):
            client.authorize_guest(mac="AA:BB:CC:DD:EE:FF", minutes=240)

        payload = mock_post.call_args[1]["json"]
        assert payload["action"] == "AUTHORIZE_GUEST_ACCESS"
        assert payload["timeLimitMinutes"] == 240

    def test_uses_client_id_in_action_url(self):
        client = _make_client()
        mock_get = MagicMock(return_value=_clients_response("clientXYZ"))
        mock_post = MagicMock(return_value=_ok_response())
        with (
            patch.object(client._session, "get", mock_get),
            patch.object(client._session, "post", mock_post),
        ):
            client.authorize_guest(mac="AA:BB:CC:DD:EE:FF")

        url = mock_post.call_args[0][0]
        assert "clientXYZ" in url

    def test_uses_site_id_in_action_url(self):
        client = _make_client()
        mock_get = MagicMock(return_value=_clients_response("clientXYZ"))
        mock_post = MagicMock(return_value=_ok_response())
        with (
            patch.object(client._session, "get", mock_get),
            patch.object(client._session, "post", mock_post),
        ):
            client.authorize_guest(mac="AA:BB:CC:DD:EE:FF")

        url = mock_post.call_args[0][0]
        assert "abc123" in url

    def test_raises_when_client_lookup_fails(self):
        client = _make_client()
        with patch.object(client._session, "get", return_value=_ok_response([])):
            with pytest.raises(UniFiError, match="not found"):
                client.authorize_guest(mac="AA:BB:CC:DD:EE:FF")

    def test_raises_on_post_http_error(self):
        client = _make_client()
        mock_get = MagicMock(return_value=_clients_response("clientXYZ"))
        mock_post = MagicMock(return_value=_error_response(500))
        with (
            patch.object(client._session, "get", mock_get),
            patch.object(client._session, "post", mock_post),
        ):
            with pytest.raises(UniFiError, match="HTTP 500"):
                client.authorize_guest(mac="AA:BB:CC:DD:EE:FF")
