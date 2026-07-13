import requests
from datetime import datetime, timedelta

class QualtricsClient:
    def __init__(self, api_url, token):
        self.api_url = api_url
        self.api_token = token

        # Initialize headers with the current token (if any)
        self.headers = self.get_headers()

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "X-API-TOKEN": self.api_token
        }

