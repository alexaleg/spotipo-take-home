import requests

# UniFi Network API reference: https://developer.ui.com/network/v10.3.58/gettingstarted


class UniFiError(Exception):
    pass


class UniFiClient:
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        site: str = "default",
        verify_ssl: bool = False,
    ) -> None:
        self._host = host.rstrip("/")
        self._username = username
        self._password = password
        self._site = site
        self._session = requests.Session()
        self._session.verify = verify_ssl

    def login(self) -> None:
        response = self._session.post(
            f"{self._host}/api/login",
            json={"username": self._username, "password": self._password},
            timeout=10,
        )
        self._raise_for_unifi_error(response)

    def authorize_guest(
        self,
        mac: str,
        minutes: int = 480,
        ap_mac: str | None = None,
    ) -> None:
        payload: dict[str, object] = {
            "cmd": "authorize-guest",
            "mac": mac.lower(),
            "minutes": minutes,
        }
        if ap_mac is not None:
            payload["ap_mac"] = ap_mac.lower()

        response = self._session.post(
            f"{self._host}/api/s/{self._site}/cmd/stamgr",
            json=payload,
            timeout=10,
        )
        self._raise_for_unifi_error(response)

    def logout(self) -> None:
        self._session.post(f"{self._host}/api/logout", timeout=10)

    def _raise_for_unifi_error(self, response: requests.Response) -> None:
        if not response.ok:
            raise UniFiError(f"HTTP {response.status_code}: {response.text[:200]}")
        try:
            data = response.json()
        except ValueError as exc:
            raise UniFiError("Invalid JSON response from controller") from exc
        meta = data.get("meta", {})
        if meta.get("rc") != "ok":
            raise UniFiError(meta.get("msg", "Unknown controller error"))
