from __future__ import annotations

import uuid
from typing import Dict, Any, List

import requests
from tenacity import retry, wait_exponential, stop_after_attempt

from config import load_config


config = load_config()


class NylasClient:
    def __init__(self):
        self.client_id = config.nylas_client_id
        self.client_secret = config.nylas_client_secret
        self.api_uri = config.nylas_api_uri.rstrip("/")

    def get_auth_url(self, state: str) -> str:
        # Hosted OAuth URL
        # Docs: https://developer.nylas.com/docs/v3/auth/hosted-auth/
        params = {
            "client_id": self.client_id,
            "redirect_uri": f"{config.backend_base_url}/nylas/callback",
            "response_type": "code",
            "scope": "email.read_only",
            "state": state,
        }
        q = "&".join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
        return f"{self.api_uri}/v3/connect/auth?{q}"

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3)
    )
    def exchange_code(self, code: str) -> Dict[str, Any]:
        # Exchange authorization code for grant and access token
        token_url = f"{self.api_uri}/v3/connect/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": f"{config.backend_base_url}/nylas/callback",
        }
        resp = requests.post(token_url, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_grant_email(self, grant_id: str) -> str:
        """Fetch the email address associated with a grant"""
        headers = {
            "Authorization": f"Bearer {self.client_secret}",
            "Content-Type": "application/json",
        }
        url = f"{self.api_uri}/v3/grants/{grant_id}"
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("email") or data.get("email", "unknown@example.com")

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3)
    )
    def fetch_last_messages(
        self, grant_id: str, limit: int = 200
    ) -> List[Dict[str, Any]]:
        # Nylas v3 messages list
        # Docs: https://developer.nylas.com/docs/v3/email/
        headers = {
            "Authorization": f"Bearer {self.client_secret}",  # Use API key
            "Content-Type": "application/json",
        }
        params = {
            "limit": limit,
        }
        url = f"{self.api_uri}/v3/grants/{grant_id}/messages"
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # Expected format: { data: [ ... messages ... ], next_cursor?: str }
        return data.get("data", [])


def new_state() -> str:
    return uuid.uuid4().hex
