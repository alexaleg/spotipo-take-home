import re
from datetime import UTC, datetime

from flask import Blueprint, current_app, make_response, render_template, request

from app import db
from app.models import GuestSession
from app.unifi import UniFiClient, UniFiError

main_bp = Blueprint("main", __name__)

_MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@main_bp.get("/")
def index() -> str:
    return render_template(
        "login.html",
        mac=request.args.get("mac", ""),
        ap=request.args.get("ap", ""),
        site_id=request.args.get("id", ""),
        ssid=request.args.get("ssid", ""),
        redirect_url=request.args.get("url", ""),
    )


@main_bp.post("/authenticate")
def authenticate():  # type: ignore[return]
    email = (request.form.get("email") or "").strip()
    mac = (request.form.get("mac") or "").strip()
    ap = (request.form.get("ap") or "").strip()
    site_id = (request.form.get("site_id") or "").strip()
    ssid = (request.form.get("ssid") or "").strip()

    if not _EMAIL_RE.match(email):
        return render_template(
            "partials/error.html", message="Please enter a valid email address."
        ), 422

    if not _MAC_RE.match(mac):
        return render_template(
            "partials/error.html", message="Invalid request: missing device identifier."
        ), 422

    session = GuestSession(
        email=email,
        mac_address=mac.lower(),
        ap_mac=ap.lower() if ap else None,
        site_id=site_id or None,
        ssid=ssid or None,
        client_ip=request.remote_addr,
        status="pending",
        minutes_authorized=current_app.config["PORTAL_AUTHORIZED_MINUTES"],
    )
    db.session.add(session)
    db.session.commit()

    if not current_app.config.get("UNIFI_MOCK"):
        client = UniFiClient(
            host=current_app.config["UNIFI_HOST"],
            username=current_app.config["UNIFI_USERNAME"],
            password=current_app.config["UNIFI_PASSWORD"],
            site=current_app.config["UNIFI_SITE"],
            verify_ssl=current_app.config["UNIFI_VERIFY_SSL"],
        )
        try:
            client.login()
            client.authorize_guest(
                mac=mac,
                minutes=current_app.config["PORTAL_AUTHORIZED_MINUTES"],
                ap_mac=ap or None,
            )
            client.logout()
        except UniFiError as exc:
            session.status = "failed"
            session.error_message = str(exc)
            db.session.commit()
            return render_template(
                "partials/error.html",
                message="Authorization failed. Please try again or contact staff.",
            ), 502

    session.status = "authorized"
    session.authorized_at = datetime.now(UTC).replace(tzinfo=None)
    db.session.commit()

    response = make_response("", 200)
    response.headers["HX-Redirect"] = "/success"
    return response


@main_bp.get("/success")
def success() -> str:
    return render_template("success.html")


@main_bp.get("/admin")
def admin() -> str:
    sessions = GuestSession.query.order_by(GuestSession.created_at.desc()).all()
    return render_template("admin.html", sessions=sessions)
