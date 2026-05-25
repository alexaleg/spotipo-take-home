"""
Route integration tests.
UniFi API reference: https://developer.ui.com/network/v10.3.58/gettingstarted
"""

from unittest.mock import patch

from app import db
from app.models import GuestSession
from app.unifi import UniFiError

VALID_MAC = "aa:bb:cc:dd:ee:ff"
VALID_EMAIL = "user@example.com"


def _auth_form(email: str = VALID_EMAIL, mac: str = VALID_MAC, **kwargs):
    return {
        "email": email,
        "mac": mac,
        "ap": "",
        "site_id": "default",
        "ssid": "TestNet",
        **kwargs,
    }


class TestIndex:
    def test_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_renders_email_form(self, client):
        response = client.get("/")
        assert b'name="email"' in response.data

    def test_passes_mac_to_hidden_input(self, client):
        response = client.get(f"/?mac={VALID_MAC}&ap=11:22:33:44:55:66&id=default")
        assert VALID_MAC.encode() in response.data


class TestAuthenticate:
    def test_success_returns_hx_redirect(self, client, app):
        with patch("app.routes.UniFiClient") as mock_cls:
            mock_cls.return_value.login.return_value = None
            mock_cls.return_value.authorize_guest.return_value = None
            mock_cls.return_value.logout.return_value = None

            response = client.post("/authenticate", data=_auth_form())

        assert response.status_code == 200
        assert response.headers.get("HX-Redirect") == "/success"

    def test_success_creates_authorized_session(self, client, app):
        with patch("app.routes.UniFiClient") as mock_cls:
            mock_cls.return_value.login.return_value = None
            mock_cls.return_value.authorize_guest.return_value = None
            mock_cls.return_value.logout.return_value = None

            client.post("/authenticate", data=_auth_form())

        with app.app_context():
            session = GuestSession.query.filter_by(email=VALID_EMAIL).first()
            assert session is not None
            assert session.status == "authorized"
            assert session.authorized_at is not None

    def test_unifi_error_returns_502(self, client, app):
        with patch("app.routes.UniFiClient") as mock_cls:
            mock_cls.return_value.login.side_effect = UniFiError("controller down")

            response = client.post("/authenticate", data=_auth_form())

        assert response.status_code == 502

    def test_unifi_error_stores_failed_session(self, client, app):
        with patch("app.routes.UniFiClient") as mock_cls:
            mock_cls.return_value.login.side_effect = UniFiError("controller down")

            client.post("/authenticate", data=_auth_form())

        with app.app_context():
            session = GuestSession.query.filter_by(email=VALID_EMAIL).first()
            assert session is not None
            assert session.status == "failed"
            assert session.error_message == "controller down"

    def test_invalid_email_returns_422(self, client, app):
        response = client.post("/authenticate", data=_auth_form(email="not-an-email"))
        assert response.status_code == 422

    def test_invalid_email_does_not_create_session(self, client, app):
        client.post("/authenticate", data=_auth_form(email="not-an-email"))
        with app.app_context():
            assert GuestSession.query.count() == 0

    def test_invalid_mac_returns_422(self, client, app):
        response = client.post("/authenticate", data=_auth_form(mac="not-a-mac"))
        assert response.status_code == 422

    def test_missing_mac_returns_422(self, client, app):
        response = client.post("/authenticate", data=_auth_form(mac=""))
        assert response.status_code == 422


    def test_mock_mode_skips_unifi_and_authorizes(self, app):
        app.config["UNIFI_MOCK"] = True
        with app.test_client() as mock_client:
            with patch("app.routes.UniFiClient") as unifi_cls:
                response = mock_client.post("/authenticate", data=_auth_form())
                unifi_cls.assert_not_called()

        assert response.status_code == 200
        assert response.headers.get("HX-Redirect") == "/success"

        with app.app_context():
            session = GuestSession.query.filter_by(email=VALID_EMAIL).first()
            assert session is not None
            assert session.status == "authorized"

        app.config["UNIFI_MOCK"] = False


class TestSuccess:
    def test_returns_200(self, client):
        response = client.get("/success")
        assert response.status_code == 200


class TestAdmin:
    def test_returns_200_empty(self, client):
        response = client.get("/admin")
        assert response.status_code == 200

    def test_lists_sessions(self, client, app):
        with app.app_context():
            session = GuestSession(
                email="admin@example.com",
                mac_address=VALID_MAC,
                status="authorized",
                minutes_authorized=480,
            )
            db.session.add(session)
            db.session.commit()

        response = client.get("/admin")
        assert b"admin@example.com" in response.data
