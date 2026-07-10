import requests
from datetime import datetime, timedelta

class LdotClient:
    def __init__(self, token_url, api_url, client_id, client_secret):
        self.token_url = token_url
        self.api_url = api_url
        self.client_id = client_id
        self.client_secret = client_secret

        # Start with no token and no expiry
        self.token = None
        self.token_expiry = None

        # Initialize headers with the current token (if any)
        self.headers = self.get_headers()

    def get_headers(self):
        token = self.get_token()

        return {
            "accept": "application/json",
            "Authorization": f"Bearer {token}"
        }


    def get_token(self):
        if self.token_is_valid():
            return self.token

        response = requests.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            },
            headers={"accept": "application/json"},
        )

        response.raise_for_status()
        payload = response.json()

        self.token = payload["access_token"]
        self.token_expiry = datetime.now() + timedelta(
            seconds=payload["expires_in"]
        )

        return self.token

    def token_is_valid(self):
        return self.token and self.token_expiry and datetime.now() < self.token_expiry