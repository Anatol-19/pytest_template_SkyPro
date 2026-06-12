#!/usr/bin/env python3
import argparse
import csv
import os
import re
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlparse

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = "/Users/aqa/Documents/VRP Content/new_videos_arp.csv"
PREMIUM_QUALITIES = ("8k", "6k", "4k", "2k")
DEFAULT_LOGIN = "qa_active@mailto.plus"
DEFAULT_PASSWORD = "EBTcYm6AxXEcz7n!"
ENV_BASE_URLS = {
    "prod": "https://vrporn.com",
    "stage": "https://sg.vrporn.com",
    "stg": "https://sg.vrporn.com",
    "test": "https://t.vrporn.com",
    "dev": "https://d.vrporn.com",
}


@dataclass
class ReportRow:
    row_no: int
    arp_name: str
    vrp_title: str
    vrp_slug: str
    playa_video_id: str
    asset_type: str
    quality: str
    expected_path: str
    actual_url: str
    ttl: str
    token_present: bool
    http_status: str
    status: str
    details: str


def normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).casefold()


def normalize_asset_path(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"}:
        path = parsed.path
    elif parsed.scheme == "s3":
        path = parsed.path
    else:
        path = value
    path = unquote(path).lstrip("/")
    if path.startswith("cdn/"):
        path = path[4:]
    return path


def url_asset_path(value: str) -> str:
    return normalize_asset_path(value)


def signed_url_info(url: str) -> tuple[str, bool, str, str]:
    if not url:
        return "", False, "missing_url", "URL is empty"
    params = parse_qs(urlparse(url).query)
    ttl = params.get("ttl", [""])[0]
    token = params.get("token", [""])[0]
    if not ttl:
        return ttl, bool(token), "missing_ttl", "Signed URL has no ttl parameter"
    if not token:
        return ttl, False, "missing_token", "Signed URL has no token parameter"
    try:
        if int(ttl) <= int(time.time()):
            return ttl, True, "ttl_expired", "Signed URL ttl is expired"
    except ValueError:
        return ttl, True, "bad_ttl", "Signed URL ttl is not an integer"
    return ttl, True, "ok", ""


def path_matches(expected: str, actual_url: str) -> bool:
    expected_path = normalize_asset_path(expected)
    actual_path = url_asset_path(actual_url)
    if not expected_path or not actual_path:
        return False
    return actual_path == expected_path or actual_path.endswith(expected_path)


class PlayaClient:
    def __init__(self, base_url: str, playa_v2: str, timeout: int = 30, verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.playa_v2 = "/" + playa_v2.strip("/")
        self.timeout = timeout
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers.update(
            {
                "accept": "application/json",
                "content-type": "application/json",
                "user-agent": "pytest-template-skypro/arp-playa-asset-checker",
            }
        )

    def url(self, path: str) -> str:
        return f"{self.base_url}{self.playa_v2}/{path.lstrip('/')}"

    def log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)

    def login(self, login: str, password: str) -> None:
        self.log(f"POST {self.url('auth/sign-in-password')} login={login}")
        response = self.session.post(
            self.url("auth/sign-in-password"),
            json={"login": login, "password": password},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status", {}).get("code") != 1:
            raise RuntimeError(f"PLAYa login failed: {payload.get('status', payload)}")
        access_token = payload.get("data", {}).get("access_token")
        if not access_token:
            raise RuntimeError("PLAYa login response does not contain data.access_token")
        self.session.headers.update({"authorization": f"Bearer {access_token}"})
        self.log("AUTH ok")

    def search_video(self, title: str) -> dict[str, Any]:
        self.log(f"GET  {self.url('videos')} title={title!r}")
        response = self.session.get(
            self.url("videos"),
            params={"page-size": 16, "title": title},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status", {}).get("code") != 1:
            raise RuntimeError(f"PLAYa search failed for {title}: {payload.get('status', payload)}")
        data = payload.get("data", {})
        self.log(f"     search results: item_total={data.get('item_total')} page_total={data.get('page_total')}")
        return data

    def get_video(self, video_id: str) -> dict[str, Any]:
        self.log(f"GET  {self.url(f'video/{quote(str(video_id))}')} video_id={video_id}")
        response = self.session.get(self.url(f"video/{quote(str(video_id))}"), timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        if payload.get("status", {}).get("code") != 1:
            raise RuntimeError(f"PLAYa video details failed for {video_id}: {payload.get('status', payload)}")
        data = payload.get("data", {})
        self.log(f"     details: title={data.get('title')!r} details_count={len(data.get('details') or [])}")
        return data

    def check_url(self, url: str) -> tuple[str, str]:
        self.log(f"HEAD {url}")
        try:
            response = self.session.head(url, allow_redirects=True, timeout=self.timeout)
            if response.status_code == 405:
                self.log("     HEAD 405, fallback GET range")
                response = self.session.get(
                    url,
                    headers={"Range": "bytes=0-0"},
                    stream=True,
                    timeout=self.timeout,
                )
            status_code = response.status_code
        except Exception as exc:
            return "", f"request_error: {exc}"
        if 200 <= status_code < 400:
            return str(status_code), ""
        return str(status_code), f"http_{status_code}"


def pick_video(search_data: dict[str, Any], title: str) -> tuple[str, str]:
    content = search_data.get("content") or []
    if not content:
        return "", "playa_video_not_found"
    if len(content) == 1:
        return str(content[0].get("id", "")), ""

    expected = normalize_title(title)
    exact = [item for item in content if normalize_title(item.get("title", "")) == expected]
    if len(exact) == 1:
        return str(exact[0].get("id", "")), ""
    if len(exact) > 1:
        ids = ", ".join(str(item.get("id", "")) for item in exact)
        return "", f"playa_video_ambiguous_exact: {ids}"
    ids = ", ".join(f"{item.get('id')}:{item.get('title')}" for item in content[:5])
    return "", f"playa_video_ambiguous: {ids}"


def detail_by_type(video_data: dict[str, Any], detail_type: str) -> dict[str, Any]:
    for detail in video_data.get("details") or []:
        if detail.get("type") == detail_type:
            return detail
    return {}


def link_by_quality(detail: dict[str, Any], quality: str) -> dict[str, Any]:
    for link in detail.get("links") or []:
        if str(link.get("quality_name", "")).casefold() == quality.casefold():
            return link
    return {}


def add_media_result(
    results: list[ReportRow],
    row_no: int,
    row: dict[str, str],
    video_id: str,
    asset_type: str,
    quality: str,
    expected_path: str,
    actual_url: str,
    unavailable_reason: str,
    client: PlayaClient,
    check_http: bool,
) -> None:
    ttl, token_present, status, details = signed_url_info(actual_url)
    http_status = ""
    if unavailable_reason == "__quality_not_found__" and not actual_url:
        status = "quality_not_found"
        details = "Quality is not present in PLAYa detail links"
    elif unavailable_reason and not actual_url:
        status = f"unavailable_{unavailable_reason}"
        details = f"PLAYa link unavailable_reason={unavailable_reason}"
    elif status == "ok" and check_http:
        http_status, http_error = client.check_url(actual_url)
        if http_error:
            status = http_error
            details = http_error
    if status == "ok" and expected_path and actual_url and not path_matches(expected_path, actual_url):
        status = "path_mismatch"
        details = f"Expected {normalize_asset_path(expected_path)}, got {url_asset_path(actual_url)}"

    results.append(
        ReportRow(
            row_no=row_no,
            arp_name=row.get("ARP Name", ""),
            vrp_title=row.get("VRP Title", ""),
            vrp_slug=row.get("VRP Slug", ""),
            playa_video_id=video_id,
            asset_type=asset_type,
            quality=quality,
            expected_path=expected_path,
            actual_url=actual_url or "",
            ttl=ttl,
            token_present=token_present,
            http_status=http_status,
            status=status,
            details=details,
        )
    )


def verify_mask(
    results: list[ReportRow],
    row_no: int,
    row: dict[str, str],
    video_id: str,
    video_data: dict[str, Any],
    client: PlayaClient,
    check_http: bool,
) -> None:
    expected_path = row.get("mask path", "").strip()
    full_detail = detail_by_type(video_data, "full")
    trailer_detail = detail_by_type(video_data, "trailer")
    transparency = video_data.get("transparency")

    mask_sources = [
        ("full", full_detail.get("alpha_mask") or ""),
        ("trailer", trailer_detail.get("alpha_mask") or ""),
    ]
    seen = set()
    if not any(url for _, url in mask_sources):
        mask_sources = [("full_or_trailer", "")]

    for mask_quality, actual_url in mask_sources:
        if actual_url in seen:
            continue
        seen.add(actual_url)

        ttl, token_present, status, details = signed_url_info(actual_url)
        if not actual_url:
            status = "mask_expected_but_not_found" if expected_path else "mask_not_expected"
            details = "No alpha_mask in PLAYa video details"
        elif not transparency:
            status = "mask_transparency_missing"
            details = "alpha_mask exists, but data.transparency is empty"

        http_status = ""
        if status == "ok" and check_http:
            http_status, http_error = client.check_url(actual_url)
            if http_error:
                status = http_error
                details = http_error
        if status == "ok" and expected_path and actual_url and not path_matches(expected_path, actual_url):
            status = "mask_path_mismatch"
            details = f"Expected {normalize_asset_path(expected_path)}, got {url_asset_path(actual_url)}"

        results.append(
            ReportRow(
                row_no=row_no,
                arp_name=row.get("ARP Name", ""),
                vrp_title=row.get("VRP Title", ""),
                vrp_slug=row.get("VRP Slug", ""),
                playa_video_id=video_id,
                asset_type="mask",
                quality=mask_quality,
                expected_path=expected_path,
                actual_url=actual_url,
                ttl=ttl,
                token_present=token_present,
                http_status=http_status,
                status=status,
                details=details,
            )
        )


def verify_script(results: list[ReportRow], row_no: int, row: dict[str, str], video_id: str, video_data: dict[str, Any]) -> None:
    expected_path = row.get("script path", "").strip()
    full_detail = detail_by_type(video_data, "full")
    trailer_detail = detail_by_type(video_data, "trailer")
    script_info = full_detail.get("script_info") or trailer_detail.get("script_info")
    has_scripts = bool(video_data.get("has_scripts") or full_detail.get("has_scripts") or trailer_detail.get("has_scripts") or script_info)
    status = "ok" if has_scripts else "script_expected_but_not_found"
    details = "" if has_scripts else "No script_info/has_scripts in PLAYa video details"
    results.append(
        ReportRow(
            row_no=row_no,
            arp_name=row.get("ARP Name", ""),
            vrp_title=row.get("VRP Title", ""),
            vrp_slug=row.get("VRP Slug", ""),
            playa_video_id=video_id,
            asset_type="script",
            quality="",
            expected_path=expected_path,
            actual_url=str(script_info or ""),
            ttl="",
            token_present=False,
            http_status="",
            status=status,
            details=details,
        )
    )


def verify_row(
    row_no: int,
    row: dict[str, str],
    client: PlayaClient,
    check_http: bool,
) -> list[ReportRow]:
    results: list[ReportRow] = []
    title = row.get("VRP Title", "").strip()
    if not title:
        return [
            ReportRow(
                row_no=row_no,
                arp_name=row.get("ARP Name", ""),
                vrp_title="",
                vrp_slug=row.get("VRP Slug", ""),
                playa_video_id="",
                asset_type="video",
                quality="",
                expected_path="",
                actual_url="",
                ttl="",
                token_present=False,
                http_status="",
                status="missing_vrp_title",
                details="CSV row has empty VRP Title",
            )
        ]

    try:
        search_data = client.search_video(title)
        video_id, pick_error = pick_video(search_data, title)
        if pick_error:
            raise RuntimeError(pick_error)
        video_data = client.get_video(video_id)
    except Exception as exc:
        results.append(
            ReportRow(
                row_no=row_no,
                arp_name=row.get("ARP Name", ""),
                vrp_title=title,
                vrp_slug=row.get("VRP Slug", ""),
                playa_video_id="",
                asset_type="video",
                quality="",
                expected_path="",
                actual_url="",
                ttl="",
                token_present=False,
                http_status="",
                status="playa_api_error",
                details=str(exc),
            )
        )
        return results

    full_detail = detail_by_type(video_data, "full")
    trailer_detail = detail_by_type(video_data, "trailer")

    for quality in PREMIUM_QUALITIES:
        expected_path = row.get(quality, "").strip()
        if not expected_path:
            continue
        link = link_by_quality(full_detail, quality)
        add_media_result(
            results,
            row_no,
            row,
            video_id,
            "premium",
            quality,
            expected_path,
            link.get("url") or "",
            link.get("unavailable_reason") or ("__quality_not_found__" if not link else ""),
            client,
            check_http,
        )

    trailer_expected = row.get("trailer", "").strip()
    trailer_links = trailer_detail.get("links") or []
    if trailer_expected or trailer_links:
        if trailer_links:
            for link in sorted(trailer_links, key=lambda item: item.get("quality_order") or 0, reverse=True):
                add_media_result(
                    results,
                    row_no,
                    row,
                    video_id,
                    "trial",
                    str(link.get("quality_name") or ""),
                    trailer_expected,
                    link.get("url") or "",
                    link.get("unavailable_reason") or "",
                    client,
                    check_http,
                )
        else:
            add_media_result(results, row_no, row, video_id, "trial", "", trailer_expected, "", "__quality_not_found__", client, check_http)

    verify_mask(results, row_no, row, video_id, video_data, client, check_http)
    verify_script(results, row_no, row, video_id, video_data)
    return results


def write_report(rows: list[ReportRow], output_path: str) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(asdict(rows[0]).keys()) if rows else list(ReportRow.__dataclass_fields__))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def read_csv(input_path: str, limit: int | None) -> list[dict[str, str]]:
    with open(input_path, newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    return rows[:limit] if limit else rows


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    parser = argparse.ArgumentParser(description="Verify ARPorn migration assets through PLAYa API.")
    parser.add_argument("--file", "--input", dest="input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default="")
    parser.add_argument("--env", choices=sorted(ENV_BASE_URLS), default=os.getenv("PLAYA_ENV", "prod"))
    parser.add_argument("--base-url", default=os.getenv("PLAYA_BASE_URL", "https://vrporn.com"))
    parser.add_argument("--playa-v2", default=os.getenv("PLAYA_V2", "/api/playa/v2"))
    parser.add_argument("--login", default=os.getenv("PLAYA_LOGIN") or os.getenv("VRP_MEMBER_EMAIL") or DEFAULT_LOGIN)
    parser.add_argument("--password", default=os.getenv("PLAYA_PASSWORD") or os.getenv("VRP_MEMBER_PASSWORD") or DEFAULT_PASSWORD)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--check-http", action="store_true")
    parser.add_argument("--fail-on-issues", action="store_true")
    parser.add_argument("--verbose", action="store_true", help="Print request/progress logs")
    args = parser.parse_args()

    if not args.login or not args.password:
        raise SystemExit("Set PLAYA_LOGIN/PLAYA_PASSWORD or VRP_MEMBER_EMAIL/VRP_MEMBER_PASSWORD in .env")

    base_url = args.base_url or ENV_BASE_URLS[args.env]
    if not os.getenv("PLAYA_BASE_URL") and args.base_url == "https://vrporn.com":
        base_url = ENV_BASE_URLS[args.env]

    output = args.output or str(Path(args.input).with_name(Path(args.input).stem + "_playa_report.csv"))
    client = PlayaClient(base_url, args.playa_v2, verbose=args.verbose)
    client.login(args.login, args.password)

    all_results: list[ReportRow] = []
    input_rows = read_csv(args.input, args.limit)
    for row_no, row in enumerate(input_rows, start=1):
        if args.verbose:
            print(f"[{row_no}/{len(input_rows)}] {row.get('VRP Title', '')}", flush=True)
        all_results.extend(verify_row(row_no, row, client, args.check_http))

    write_report(all_results, output)
    issue_count = sum(1 for row in all_results if row.status != "ok")
    status_counts = Counter(row.status for row in all_results)
    print(f"Report: {output}")
    print(f"Rows: {len(all_results)}; issues: {issue_count}")
    print("Statuses:")
    for status, count in status_counts.most_common():
        print(f"  {status}: {count}")
    return 1 if args.fail_on_issues and issue_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
