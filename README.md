# UniFi Captive Portal

An external captive portal for UniFi-managed Wi-Fi networks. When a user connects to the network, UniFi redirects their browser here. They enter their email, it is stored in the database, and the UniFi Network API is called to authorize internet access for their device.

## Stack

- **Backend:** Flask 3 + SQLAlchemy 2
- **Database:** MySQL 8
- **Frontend:** Tailwind CSS + Alpine.js + HTMX (all via CDN)
- **Deployment:** Docker Compose
- **Package manager:** [uv](https://docs.astral.sh/uv/)
- **Linting / formatting:** [ruff](https://docs.astral.sh/ruff/)
- **Type checking:** [ty](https://github.com/astral-sh/ty)
- **Testing:** pytest

API references:
- [External Hotspot API for Authorization Clients](https://help.ui.com/hc/en-us/articles/31228198640023)
- [Execute Connected Client Action](https://developer.ui.com/network/v1/executeconnectedclientaction)
- [Authentication (X-API-KEY)](https://developer.ui.com/site-manager/v1.0.0/gettingstarted)

---

## How the captive portal flow works

```
User connects to Wi-Fi
  → UniFi detects guest (unauthorized) device
  → UniFi redirects browser to: http://<portal>:5000/?id=<client-mac>&ap=<ap-mac>&t=<timestamp>&ssid=<name>&url=<original-url>
  → User sees login page, enters email
  → POST /authenticate: email stored in DB
      → GET /v1/sites/{siteId}/clients?filter=macAddress.eq(...)  — look up clientId
      → POST /v1/sites/{siteId}/clients/{clientId}/actions        — authorize access
  → User sees success page and has internet access
```

The `id` parameter in the redirect URL is the **client device's MAC address**, injected by the UniFi controller. It is used to look up the `clientId` needed to call the authorization API.

---

## Quickstart (Docker)

```bash
cp .env.example .env
# Edit .env with your UniFi API key and site ID
docker compose up --build
```

The portal is available at `http://localhost:5000`.

To simulate a UniFi redirect, open this URL in your browser after the containers are up:

```
http://localhost:5000/?id=aa:bb:cc:dd:ee:ff&ap=11:22:33:44:55:66&t=1742398732&ssid=MyNetwork&url=http://example.com
```

---

## Testing without a UniFi controller

Set `UNIFI_MOCK=true` in your `.env` file. In mock mode the UniFi API call is skipped entirely — the portal records the session as `authorized` and redirects to the success page, so you can test the complete end-to-end flow without a controller.

```bash
cp .env.example .env
# Set UNIFI_MOCK=true in .env
docker compose up --build
```

Then open the simulated redirect URL above, submit an email, and verify the session appears in the admin panel at `http://localhost:5000/admin`.

When `UNIFI_MOCK=false` (the default) and no controller is reachable, the app catches the error gracefully and shows the user a friendly "Authorization failed" message — it will not crash.

---

## UniFi Controller configuration

This portal targets the **UniFi Network Application 9.1.105+** using the official REST API with API key authentication.

### Generate an API key

1. Open the Network Application
2. Go to **Network → Control Plane → Integrations**
3. Generate an API key and copy it to `UNIFI_API_KEY` in your `.env`

### Configure the guest portal

1. Go to **Settings → Guest Control** (or **Hotspot**)
2. Enable **Guest Portal**
3. Set **Portal customization** to **External portal server**
4. Set the **External portal URL** to `http://<your-server-ip>:5000`

The controller will then redirect all guest clients to this portal, appending `id`, `ap`, `t`, `ssid`, and `url` as query parameters.

---

## Local development

```bash
# Install all dependencies
uv sync --extra dev

# Run tests
uv run pytest --cov=app --cov-report=term-missing

# Type check
uv run ty check app/ config.py wsgi.py

# Lint + format
uv run ruff check .
uv run ruff format .

# Start dev server (no MySQL needed locally — SQLite in dev is possible by overriding DATABASE_URL)
DATABASE_URL=sqlite:///dev.db uv run flask --app wsgi:app run --debug
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | Flask secret key (required in production) |
| `DATABASE_URL` | `mysql+pymysql://root:password@db:3306/captive_portal` | SQLAlchemy connection string |
| `MYSQL_ROOT_PASSWORD` | `password` | MySQL root password (docker-compose only) |
| `UNIFI_HOST` | `https://192.168.1.1` | UniFi Network Application base URL |
| `UNIFI_API_KEY` | — | API key from Network → Control Plane → Integrations |
| `UNIFI_SITE_ID` | `default` | UniFi site ID (from `GET /v1/sites`) |
| `UNIFI_VERIFY_SSL` | `false` | Verify controller TLS certificate |
| `PORTAL_AUTHORIZED_MINUTES` | `480` | Duration of guest authorization (minutes) |
| `UNIFI_MOCK` | `false` | Skip UniFi API call and always authorize (for testing) |

---

## Admin panel

View all guest sessions at `http://localhost:5000/admin`.

Each session shows the email address, client MAC, SSID, authorization status, and timestamps. The record is created when the user submits the form and updated with the result of the UniFi API call.

---

## Security considerations

**MAC address tampering:** The client MAC address is passed by UniFi in the `id` query parameter of the redirect URL and is not cryptographically signed by default. A user on the same network could theoretically submit a different device's MAC address to authorize it. The practical risk is low (they would authorize someone else's device, not gain access themselves), but for production deployments consider enabling a **UAM shared secret** in the UniFi controller guest portal settings so the portal can verify the redirect parameters have not been tampered with.

**SSL:** `UNIFI_VERIFY_SSL=false` by default because most on-premise controllers use self-signed certificates. Set to `true` in production if your controller has a valid certificate.

---

## Project structure

```
app/
  __init__.py       Flask app factory
  models.py         GuestSession SQLAlchemy model
  routes.py         Route handlers (/, /authenticate, /success, /admin)
  unifi.py          UniFi API client
  templates/        Jinja2 templates
    base.html
    login.html
    success.html
    admin.html
    partials/
      error.html
tests/
  conftest.py       pytest fixtures
  test_models.py
  test_routes.py
  test_unifi.py
config.py           Config and TestConfig
wsgi.py             Gunicorn entry point
```
