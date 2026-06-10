from collections import defaultdict

from REST.auth_client import AuthClient
from REST.base_client import BaseApiClient
from services.content_assets.asset_mapper import map_actual_assets
from services.content_assets.content_client import ContentClient
from services.content_assets.csv_loader import load_expected_assets
from services.content_assets.models import VerificationResult
from services.content_assets.report_writer import write_detail_report, write_summary_report
from services.content_assets.signed_url_validator import (
    check_cdn_url,
    signed_url_metadata,
    url_matches_expected_path,
)


class ContentAssetVerifier:
    def __init__(self, environment=None, check_http=False):
        self.api_client = BaseApiClient(environment=environment)
        self.auth_client = AuthClient(self.api_client)
        self.content_client = ContentClient(self.api_client)
        self.check_http = check_http

    def login(self):
        return self.auth_client.login()

    def verify_csv(self, csv_path, limit=None, detail_report_path=None, summary_report_path=None):
        self.login()
        expected_assets = load_expected_assets(csv_path, limit=limit)
        results = self.verify_expected_assets(expected_assets)

        if detail_report_path:
            write_detail_report(results, detail_report_path)
        if summary_report_path:
            write_summary_report(results, summary_report_path)

        return results

    def verify_expected_assets(self, expected_assets):
        by_slug = defaultdict(list)
        for asset in expected_assets:
            by_slug[asset.slug].append(asset)

        results = []
        for slug, slug_assets in by_slug.items():
            try:
                item = self.content_client.get_post(slug)
                actual_assets = map_actual_assets(item)
                api_status = "ok"
                api_error = ""
            except Exception as exc:
                actual_assets = []
                api_status = "api_error"
                api_error = str(exc)

            for expected in slug_assets:
                results.append(self._verify_one(expected, actual_assets, api_status, api_error))
        return results

    def _verify_one(self, expected, actual_assets, api_status, api_error):
        result = VerificationResult(
            record_no=expected.record_no,
            title=expected.title,
            slug=expected.slug,
            asset_type=expected.asset_type,
            quality=expected.quality,
            source_column=expected.source_column,
            expected_path=expected.expected_path,
            api_status=api_status,
        )

        if api_status != "ok":
            result.verification_status = api_status
            result.details = api_error
            return result

        actual = self._find_actual_asset(expected, actual_assets)
        if not actual:
            result.verification_status = "signed_url_not_found"
            result.details = "Expected asset path was not found in content API response"
            return result

        result.api_field = actual.api_field
        result.signed_url = actual.signed_url
        result.ttl, result.token_present, metadata_status = signed_url_metadata(actual.signed_url)
        if metadata_status != "ok":
            result.verification_status = metadata_status
            result.details = "Signed URL is missing valid ttl/token"
            return result

        if self.check_http:
            result.cdn_status, cdn_error = check_cdn_url(self.api_client, actual.signed_url)
            if cdn_error:
                result.verification_status = "cdn_error"
                result.details = cdn_error
                return result

        result.verification_status = "ok"
        return result

    @staticmethod
    def _find_actual_asset(expected, actual_assets):
        candidates = [
            asset
            for asset in actual_assets
            if asset.asset_type == expected.asset_type and asset.quality == expected.quality
        ]
        for candidate in candidates:
            if url_matches_expected_path(candidate.signed_url, expected.expected_path):
                return candidate
        return None
