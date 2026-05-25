from datetime import datetime

from app import db
from app.models import GuestSession


def test_guest_session_create(app):
    with app.app_context():
        session = GuestSession(
            email="user@example.com",
            mac_address="aa:bb:cc:dd:ee:ff",
            status="pending",
            minutes_authorized=480,
        )
        db.session.add(session)
        db.session.commit()

        fetched = db.session.get(GuestSession, session.id)
        assert fetched is not None
        assert fetched.email == "user@example.com"
        assert fetched.mac_address == "aa:bb:cc:dd:ee:ff"
        assert fetched.status == "pending"


def test_guest_session_nullable_fields(app):
    with app.app_context():
        session = GuestSession(
            email="user@example.com",
            mac_address="aa:bb:cc:dd:ee:ff",
            status="pending",
            minutes_authorized=480,
        )
        db.session.add(session)
        db.session.commit()

        assert session.authorized_at is None
        assert session.error_message is None
        assert session.ap_mac is None


def test_guest_session_created_at_set(app):
    with app.app_context():
        session = GuestSession(
            email="user@example.com",
            mac_address="aa:bb:cc:dd:ee:ff",
            status="pending",
            minutes_authorized=480,
        )
        db.session.add(session)
        db.session.commit()

        assert isinstance(session.created_at, datetime)


def test_guest_session_status_transition(app):
    with app.app_context():
        session = GuestSession(
            email="user@example.com",
            mac_address="aa:bb:cc:dd:ee:ff",
            status="pending",
            minutes_authorized=480,
        )
        db.session.add(session)
        db.session.commit()

        session.status = "authorized"
        session.authorized_at = datetime(2024, 1, 1, 12, 0, 0)
        db.session.commit()

        fetched = db.session.get(GuestSession, session.id)
        assert fetched is not None
        assert fetched.status == "authorized"
        assert fetched.authorized_at == datetime(2024, 1, 1, 12, 0, 0)
