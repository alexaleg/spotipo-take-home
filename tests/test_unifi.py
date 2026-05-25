"""
Tests for the UniFi API client.
API reference: https://developer.ui.com/network/v10.3.58/gettingstarted
"""

from unittest.mock import MagicMock, patch

import pytest

from app.unifi import UniFiClient, UniFiError


def _make_client() -> UniFiClient:
    return UniFiClient(
        host="https://192.168.1.1:8443",
        username="admin",
        password="password",
        site="default",
        verify_ssl=False,
    )


def _ok_response(data: dict | None = None) -> MagicMock:
    response = MagicMock()
    response.ok = True
    response.json.return_value = {"meta": {"rc": "ok"}, "data": data or []}
    return response


def _error_response(status_code: int = 400, msg: str = "bad request") -> MagicMock:
    response = MagicMock()
    response.ok = False
    response.status_code = status_code
    response.text = msg
    return response


def _unifi_error_response(msg: str = "controller error") -> MagicMock:
    response = MagicMock()
    response.ok = True
    response.json.return_value = {"meta": {"rc": "error", "msg": msg}}
    return response


class TestLogin:
    def test_login_success(self):
        client = _make_client()
        with patch.object(client._session, "post", return_value=_ok_response()):
            client.login()

    def test_login_http_error_raises(self):
        client = _make_client()
        with patch.object(client._session, "post", return_value=_error_response(401)):
            with pytest.raises(UniFiError, match="HTTP 401"):
                client.login()

    def test_login_controller_error_raises(self):
        client = _make_client()
        with patch.object(
            client._session,
            "post",
            return_value=_unifi_error_response("Invalid credentials"),
        ):
            with pytest.raises(UniFiError, match="Invalid credentials"):
                client.login()


class TestAuthorizeGuest:
    def test_authorize_guest_sends_correct_payload(self):
        client = _make_client()
        mock_post = MagicMock(return_value=_ok_response())
        with patch.object(client._session, "post", mock_post):
            client.authorize_guest(mac="AA:BB:CC:DD:EE:FF", minutes=240)

        call_kwargs = mock_post.call_args
        assert call_kwargs[0][0].endswith("/api/s/default/cmd/stamgr")
        payload = call_kwargs[1]["json"]
        assert payload["cmd"] == "authorize-guest"
        assert payload["mac"] == "aa:bb:cc:dd:ee:ff"
        assert payload["minutes"] == 240

    def test_authorize_guest_includes_ap_mac_when_provided(self):
        client = _make_client()
        mock_post = MagicMock(return_value=_ok_response())
        with patch.object(client._session, "post", mock_post):
            client.authorize_guest(mac="AA:BB:CC:DD:EE:FF", ap_mac="11:22:33:44:55:66")

        payload = mock_post.call_args[1]["json"]
        assert payload["ap_mac"] == "11:22:33:44:55:66"

    def test_authorize_guest_omits_ap_mac_when_none(self):
        client = _make_client()
        mock_post = MagicMock(return_value=_ok_response())
        with patch.object(client._session, "post", mock_post):
            client.authorize_guest(mac="AA:BB:CC:DD:EE:FF")

        payload = mock_post.call_args[1]["json"]
        assert "ap_mac" not in payload

    def test_authorize_guest_raises_on_controller_error(self):
        client = _make_client()
        with patch.object(
            client._session, "post", return_value=_unifi_error_response("mac not found")
        ):
            with pytest.raises(UniFiError, match="mac not found"):
                client.authorize_guest(mac="AA:BB:CC:DD:EE:FF")

    def test_authorize_guest_raises_on_http_error(self):
        client = _make_client()
        with patch.object(client._session, "post", return_value=_error_response(500)):
            with pytest.raises(UniFiError, match="HTTP 500"):
                client.authorize_guest(mac="AA:BB:CC:DD:EE:FF")
