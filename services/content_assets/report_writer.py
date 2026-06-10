import csv
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path


DETAIL_FIELDNAMES = [
    "record_no",
    "title",
    "slug",
    "asset_type",
    "quality",
    "source_column",
    "expected_path",
    "api_field",
    "signed_url",
    "ttl",
    "token_present",
    "api_status",
    "cdn_status",
    "verification_status",
    "details",
]


SUMMARY_FIELDNAMES = [
    "record_no",
    "title",
    "slug",
    "total_assets",
    "ok_assets",
    "problem_assets",
    "verification_status",
    "details",
]


def write_detail_report(results, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=DETAIL_FIELDNAMES)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def write_summary_report(results, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    grouped = defaultdict(list)
    for result in results:
        grouped[(result.record_no, result.title, result.slug)].append(result)

    rows = []
    for (record_no, title, slug), items in grouped.items():
        statuses = Counter(item.verification_status for item in items)
        problem_items = [item for item in items if item.verification_status != "ok"]
        details = "; ".join(
            f"{item.asset_type}:{item.quality or '-'}:{item.verification_status}" for item in problem_items[:10]
        )
        if len(problem_items) > 10:
            details += f"; +{len(problem_items) - 10} more"
        rows.append(
            {
                "record_no": record_no,
                "title": title,
                "slug": slug,
                "total_assets": len(items),
                "ok_assets": statuses.get("ok", 0),
                "problem_assets": len(problem_items),
                "verification_status": "ok" if not problem_items else "failed",
                "details": details,
            }
        )

    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=SUMMARY_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
