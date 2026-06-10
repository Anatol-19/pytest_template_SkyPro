import configparser
from pathlib import Path
from urllib.parse import urljoin

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_URLS_PATH = PROJECT_ROOT / "URLs" / "base_urls.ini"
ROUTES_PATH = PROJECT_ROOT / "URLs" / "routes.ini"


class ApiClientError(Exception):
    """Raised when the API client cannot prepare or complete a request."""


class BaseApiClient:
    def __init__(
        self,
        environment=None,
        base_key="base_url",
        session=None,
        base_urls_path=BASE_URLS_PATH,
        routes_path=ROUTES_PATH,
        timeout=30,
    ):
        self.environment = environment or self._read_current_environment(base_urls_path)
        self.base_key = base_key
        self.timeout = timeout
        self.session = session or requests.Session()
        self.base_urls = self._read_ini(base_urls_path)
        self.routes = self._read_ini(routes_path)
        self.base_url = self._get_base_url()
        self.session.headers.update(self._default_headers())

    @staticmethod
    def _read_ini(path):
        parser = configparser.ConfigParser()
        parser.read(path, encoding="utf-8")
        return parser

    @classmethod
    def _read_current_environment(cls, base_urls_path):
        parser = cls._read_ini(base_urls_path)
        return parser.get("environments", "current", fallback="VRP_PROD")

    def _get_base_url(self):
        if not self.base_urls.has_section(self.environment):
            raise ApiClientError(f"Environment '{self.environment}' is not found in {BASE_URLS_PATH}")
        return self.base_urls.get(self.environment, self.base_key)

    def _default_headers(self):
        return {
            "accept": "application/json",
            "accept-language": "ru",
            "content-type": "application/json",
            "cf-ipcountry": "US",
            "x-country-code": "US",
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
            ),
        }

    def route(self, route_name, **params):
        if not self.routes.has_option("routes", route_name):
            raise ApiClientError(f"Route '{route_name}' is not found in {ROUTES_PATH}")
        route = self.routes.get("routes", route_name)
        if params:
            route = route.format(**params)
        return route

    def build_url(self, route_name=None, path=None, **params):
        route_or_path = path if path is not None else self.route(route_name, **params)
        return urljoin(self.base_url.rstrip("/") + "/", route_or_path.lstrip("/"))

    def set_bearer_token(self, token):
        self.session.headers.update({"authorization": f"Bearer {token}"})

    def set_origin_headers(self, referer_path="/"):
        self.session.headers.update(
            {
                "origin": self.base_url.rstrip("/"),
                "referer": self.build_url(path=referer_path),
            }
        )

    def request(self, method, route_name=None, path=None, **kwargs):
        url = self.build_url(route_name=route_name, path=path)
        timeout = kwargs.pop("timeout", self.timeout)
        response = self.session.request(method, url, timeout=timeout, **kwargs)
        return response

    def get_json(self, route_name=None, path=None, **kwargs):
        response = self.request("GET", route_name=route_name, path=path, **kwargs)
        response.raise_for_status()
        return response.json()

    def post_json(self, route_name=None, path=None, json=None, **kwargs):
        response = self.request("POST", route_name=route_name, path=path, json=json, **kwargs)
        response.raise_for_status()
        return response.json()

    def head(self, url, **kwargs):
        timeout = kwargs.pop("timeout", self.timeout)
        return self.session.head(url, timeout=timeout, allow_redirects=True, **kwargs)
