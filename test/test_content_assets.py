from collections import Counter
from pathlib import Path

import pytest

from services.content_assets.verifier import ContentAssetVerifier


@pytest.mark.functional
def test_content_assets_signed_urls(request):
    assets_csv = request.config.getoption("--assets-csv")
    if not assets_csv:
        pytest.skip("Pass --assets-csv=/path/to/export.csv to run content asset verification")

    csv_path = Path(assets_csv)
    if not csv_path.exists():
        pytest.fail(f"Assets CSV does not exist: {csv_path}")

    environment = request.config.getoption("--environment")
    limit = request.config.getoption("--asset-limit")
    check_http = request.config.getoption("--check-http")
    detail_report = request.config.getoption("--asset-report") or str(csv_path.with_name(f"{csv_path.stem}_asset_report.csv"))
    summary_report = request.config.getoption("--asset-summary") or str(csv_path.with_name(f"{csv_path.stem}_verified.csv"))

    verifier = ContentAssetVerifier(environment=environment, check_http=check_http)
    results = verifier.verify_csv(
        csv_path,
        limit=limit,
        detail_report_path=detail_report,
        summary_report_path=summary_report,
    )

    statuses = Counter(result.verification_status for result in results)
    failed = [result for result in results if result.verification_status != "ok"]
    assert not failed, (
        f"Content asset verification failed: {dict(statuses)}. "
        f"Detail report: {detail_report}. Summary report: {summary_report}"
    )
