#!/usr/bin/env python
"""Pull Google Sheet snapshots to local CSVs.

Uses GS_CREDS (path to service-account json) and GS_SHEET_ID env vars.
Falls back to loading services/lighthouse/configs/config_lighthouse.env if env is missing.
"""
import os
import sys
import csv
from pathlib import Path
from datetime import datetime

import gspread
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV = ROOT / "services" / "lighthouse" / "configs" / "config_lighthouse.env"
SNAP_ROOT = ROOT / "Reports" / "sheets_snapshots"


def ensure_env():
    if os.getenv("GS_CREDS") and os.getenv("GS_SHEET_ID"):
        return
    if DEFAULT_ENV.exists():
        load_dotenv(DEFAULT_ENV)
    if not os.getenv("GS_CREDS") or not os.getenv("GS_SHEET_ID"):
        raise SystemExit("GS_CREDS or GS_SHEET_ID not set; update config_lighthouse.env or env vars")


def open_client():
    creds_path = Path(os.getenv("GS_CREDS"))
    if not creds_path.is_absolute():
        creds_path = ROOT / creds_path
    if not creds_path.exists():
        raise SystemExit(f"Creds file not found: {creds_path}")
    gc = gspread.service_account(filename=creds_path)
    sh = gc.open_by_key(os.getenv("GS_SHEET_ID"))
    return sh


def dump_worksheet(ws, target_dir: Path):
    title = ws.title.replace("/", "-")
    values = ws.get_all_values()
    path = target_dir / f"{title}.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(values)
    return path, len(values)


def main():
    ensure_env()
    sh = open_client()
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = SNAP_ROOT / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    files = []
    for ws in sh.worksheets():
        path, rows = dump_worksheet(ws, out_dir)
        files.append((ws.title, path, rows))
        total_rows += rows

    print(f"Snapshot saved to {out_dir}")
    for title, path, rows in files:
        print(f" - {title}: {rows} rows -> {path}")
    print(f"Total rows: {total_rows}")


if __name__ == "__main__":
    main()
