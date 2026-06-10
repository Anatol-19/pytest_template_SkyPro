import csv
import re
from pathlib import Path

from services.content_assets.models import ExpectedAsset


QUALITY_PATH_RE = re.compile(r"^([^:]+):\s*(.+)$")


def parse_quality_paths(value):
    for line in (value or "").splitlines():
        line = line.strip()
        if not line:
            continue
        match = QUALITY_PATH_RE.match(line)
        if match:
            yield match.group(1).strip(), match.group(2).strip()
        else:
            yield "", line


def normalize_expected_path(path):
    return (path or "").strip().lstrip("/")


def load_video_rows(csv_path, limit=None):
    path = Path(csv_path)
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if limit:
        rows = rows[: int(limit)]
    return rows


def expected_assets_from_rows(rows):
    assets = []
    for index, row in enumerate(rows, start=1):
        title = row.get("title", "").strip()
        slug = row.get("slug", "").strip()

        for quality, path in parse_quality_paths(row.get("full_video_paths", "")):
            assets.append(
                ExpectedAsset(index, title, slug, "full", quality, normalize_expected_path(path), "full_video_paths")
            )

        for quality, path in parse_quality_paths(row.get("trailer_paths", "")):
            assets.append(
                ExpectedAsset(index, title, slug, "trailer", quality, normalize_expected_path(path), "trailer_paths")
            )

        simple_columns = [
            ("short", "", "short_video_path"),
            ("tiles", "free", "thumb_tiles_free_path"),
            ("tiles", "paid", "thumb_tiles_paid_path"),
            ("tiles", "slider", "thumbnail_slider_path"),
            ("cover", "featured", "cover_featured_path"),
            ("cover", "preview", "cover_preview_path"),
            ("mask", "", "mask_path"),
            ("script", "", "script_path"),
        ]
        for asset_type, quality, column in simple_columns:
            for path in (row.get(column, "") or "").splitlines():
                path = normalize_expected_path(path)
                if path:
                    assets.append(ExpectedAsset(index, title, slug, asset_type, quality, path, column))
    return assets


def load_expected_assets(csv_path, limit=None):
    return expected_assets_from_rows(load_video_rows(csv_path, limit=limit))
