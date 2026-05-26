import requests

# External Hotspot API: https://help.ui.com/hc/en-us/articles/31228198640023
# Execute client action: https://developer.ui.com/network/v1/executeconnectedclientaction
# Authentication: https://developer.ui.com/site-manager/v1.0.0/gettingstarted


class UniFiError(Exception):
    pass


class UniFiClient:
    def __init__(
        self,
        host: str,
        api_key: str,
        site_id: str,
        verify_ssl: bool = False,
    ) -> None:
        self._host = host.rstrip("/")
        self._site_id = site_id
        self._session = requests.Session()
        self._session.verify = verify_ssl
        self._session.headers.update(
            {
                "X-API-KEY": api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def get_client_id(self, mac: str) -> str:
        """Look up the UniFi clientId for a device by MAC address."""
        response = self._session.get(
            f"{self._host}/v1/sites/{self._site_id}/clients",
            params={"filter": f"macAddress.eq('{mac.upper()}')"},
            timeout=10,
        )
        self._raise_for_status(response)
        clients = response.json()
        if not clients:
            raise UniFiError(f"Client not found for MAC {mac}")
        return clients[0]["id"]

    def authorize_guest(
        self,
        mac: str,
        minutes: int = 480,
    ) -> None:
        client_id = self.get_client_id(mac)
        payload: dict[str, object] = {
            "action": "AUTHORIZE_GUEST_ACCESS",
            "timeLimitMinutes": minutes,
        }
        response = self._session.post(
            f"{self._host}/v1/sites/{self._site_id}/clients/{client_id}/actions",
            json=payload,
            timeout=10,
        )
        self._raise_for_status(response)

    def _raise_for_status(self, response: requests.Response) -> None:
        if not response.ok:
            raise UniFiError(f"HTTP {response.status_code}: {response.text[:200]}")
