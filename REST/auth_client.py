import os

from REST.base_client import BaseApiClient, PROJECT_ROOT

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


class AuthError(Exception):
    """Raised when member authorization fails."""


class AuthClient:
    def __init__(self, api_client=None):
        if load_dotenv:
            load_dotenv(PROJECT_ROOT / ".env")
        self.api_client = api_client or BaseApiClient()

    def login(self, email=None, password=None):
        email = email or os.getenv("VRP_MEMBER_EMAIL")
        password = password or os.getenv("VRP_MEMBER_PASSWORD")
        if not email or not password:
            raise AuthError("Set VRP_MEMBER_EMAIL and VRP_MEMBER_PASSWORD in .env or environment variables")

        self.api_client.set_origin_headers(referer_path="/login/?backTo=/")
        payload = {"email": email, "password": password}
        data = self.api_client.post_json("auth_login", json=payload)

        status = data.get("status", {})
        if status.get("code") != 1:
            raise AuthError(f"Login failed: {status.get('message', data)}")

        token_data = data.get("data", {}).get("token", {})
        atoken = token_data.get("atoken")
        rtoken = token_data.get("rtoken")
        if not atoken:
            raise AuthError("Login response does not contain data.token.atoken")

        self.api_client.set_bearer_token(atoken)
        self.api_client.session.cookies.set("atoken", atoken)
        if rtoken:
            self.api_client.session.cookies.set("rtoken", rtoken)
        return token_data
