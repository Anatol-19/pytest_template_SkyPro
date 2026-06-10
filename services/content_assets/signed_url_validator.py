import time
from urllib.parse import parse_qs, unquote, urlparse


def url_object_path(url):
    return unquote(urlparse(url).path).lstrip("/")


def url_matches_expected_path(signed_url, expected_path):
    actual_path = url_object_path(signed_url)
    expected_path = expected_path.lstrip("/")
    return actual_path == expected_path or actual_path.endswith(expected_path)


def signed_url_metadata(url):
    params = parse_qs(urlparse(url).query)
    ttl = params.get("ttl", [""])[0]
    token = params.get("token", [""])[0]
    token_present = bool(token)

    if not ttl:
        return ttl, token_present, "missing_ttl"
    if not token_present:
        return ttl, token_present, "missing_token"
    try:
        if int(ttl) <= int(time.time()):
            return ttl, token_present, "ttl_expired"
    except ValueError:
        return ttl, token_present, "bad_ttl"
    return ttl, token_present, "ok"


def check_cdn_url(api_client, signed_url):
    try:
        response = api_client.head(signed_url)
        if response.status_code == 405:
            response = api_client.session.get(
                signed_url,
                headers={"Range": "bytes=0-0"},
                timeout=api_client.timeout,
                stream=True,
            )
        status_code = response.status_code
    except Exception as exc:
        return "request_error", str(exc)

    if 200 <= status_code < 400:
        return str(status_code), ""
    return str(status_code), f"CDN URL returned HTTP {status_code}"
