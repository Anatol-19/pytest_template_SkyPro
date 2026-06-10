# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests
pytest

# Run by marker
pytest -m performance          # Lighthouse speed tests
pytest -m functional           # GUI/Selenium tests

# Run single test file
pytest test/speed_test.py -v

# Content assets verification (CSV-driven)
pytest test/test_content_assets.py \
  --environment=VRP_PROD \
  --assets-csv="/path/to/Result.csv" \
  --asset-limit=5 \
  --check-http

# Payment flow tests (per contour)
pytest -m payment --environment=VRP_STAGE -v
python run_payment_contours.py --contours VRP_DEV,VRP_TEST,VRP_STAGE

# Allure report (on by default → Reports/allure; disable with --no-allure)
bash tools/allure_report.sh          # generate with history/trend + open
bash tools/allure_report.sh --serve  # quick view, no history

# Run Lighthouse service directly
python services/lighthouse/pagespeed_service.py

# MCP server (stdio)
python services/lighthouse/mcp_server.py
```

Pytest flags: `--browser=chrome|firefox`, `--headless`, `--local`, `--docker`, `--contour=development|staging|production`, `--screen-resolution=1920x1080`, `--environment=<section from base_urls.ini>`.

Content assets flags: `--assets-csv`, `--asset-report`, `--asset-summary`, `--asset-limit`, `--check-http`.

## Architecture

QA automation framework for **VRPorn / VRSmash** platforms. Three independent test tracks + shared services.

### 1. Functional / GUI tests (`test/simple_test.py`)

Selenium + POM pattern. `helper/StartSession.py` manages WebDriver lifecycle (Chrome/Firefox via webdriver-manager). `POM/AuthPage.py` + `POM/selectors.py` for login flow. `helper/GUIHelper.py` wraps element interactions.

### 2. Performance tests (`test/speed_test.py`)

Calls `SpeedtestService` from `services/lighthouse/pagespeed_service.py`. Three-layer architecture:

1. **Runners** — `cli_runner.py` (local Lighthouse CLI via subprocess), `api_runner.py` (Google PageSpeed Insights API, token-bucket rate-limiter ~20 req/100 s)
2. **Processor** — `processor_lighthouse.py` parses JSON, aggregates min/max/avg/p90 for metrics P, LCP, FCP, TBT, CLS, SI, TTI, TTFB, INP
3. **Orchestrator** — `SpeedtestService` coordinates runners + processor + Google Sheets write

CrUX data available only for `*_PROD` environments.

MCP server (`mcp_server.py`, FastMCP) exposes async job queue: `enqueue_lighthouse`, `enqueue_crux`, `list_jobs`, `job_status`, plus sync `run_lighthouse`, `run_crux`, `list_environments`, `list_routes`, `get_status`. Each `SpeedtestService` receives `environment` directly — does not mutate `base_urls.ini`, safe for parallel runs.

### 3. Content Assets tests (`test/test_content_assets.py`)

API-level verification of signed CDN URLs against a CSV export of expected asset paths.

Flow: `AuthClient.login()` → `/proxy-user/api/wp/auth/login` → bearer token → `ContentClient.get_post(slug)` → `/proxy/api/content/v1/post/{slug}` → `ContentAssetVerifier` cross-checks actual signed URLs against expected paths, validates `ttl`/`token`, optionally HEAD-checks CDN. Output: `_asset_report.csv` (per-asset) + `_verified.csv` (per-video summary). Credentials via `.env`: `VRP_MEMBER_EMAIL`, `VRP_MEMBER_PASSWORD`.

### 4. Payment tests (`test/test_payment.py`)

API-level payment flow tests for VRPorn (Join / Upgrade / Cancel / Refund / Rebill), Layers 01–03. All Epoch operations go through the backend proxy `/api/payment/sync-handler/epoch` — **never** directly to `bs.epoch.com`. Transactions sent with `isTest=true`.

`services/payment/`: `PaymentClient(BaseApiClient)` (HTTP + response parsers), `epoch_payloads.py` (FlexPost JSON / DataPlus+Cancel+FlexGrade form bodies), `payment_flow.py` (`PaymentFlow` orchestrator accumulating `PaymentSession`), `fakes.py` (synthetic member/tx/session ids, `inc_tx`), `config_payment.py` (Epoch sandbox constants).

Contour-agnostic: select via `--environment=VRP_DEV|VRP_TEST|VRP_STAGE|VRP_PROD` (default `VRP_STAGE`). `self_host` resolved dynamically from `base_url` (no hardcoded host). Multi-contour runner: `run_payment_contours.py`. Layer 03 + re-join need `VRP_PAY_EMAIL`/`VRP_PAY_PASSWORD` in `.env`. **Run only on non-PROD by default.** Marker `@pytest.mark.payment`. Reference: `ai/POSTMAN_ANALYSIS.md`, `ai/VRP_PAYMENT_TESTING.md`.

> Payment auth endpoint is `/api/wp/secure/auth/login` (route `auth_payment`) — distinct from content tests' `/proxy-user/api/wp/auth/login` (route `auth_login`).

### REST layer (`REST/`)

`BaseApiClient` — `requests.Session` wrapper that reads `base_urls.ini` + `routes.ini` at init. `build_url(route_name)` / `route(name, **params)` resolve named routes. `set_bearer_token()` / `set_origin_headers()` configure auth headers. `AuthClient` extends it for member login.

### Configuration

- `URLs/base_urls.ini` — environment URLs. `[environments] current` selects active env. Sections: `VRS_DEV/TEST/STAGE/PROD`, `VRP_DEV/TEST/STAGE/PROD`. ConfigParser lowercases all keys → use `base_url` (not `BASE_URL`) when reading.
- `URLs/routes.ini` — named route paths (`[routes]` section)
- `services/lighthouse/configs/config_lighthouse.py` — paths, caching, helper functions
- `services/lighthouse/configs/config_lighthouse.env` — API keys, Google Sheets IDs, worksheet names
- `config.py` — global test config vars (browser, headless, etc.), set to `None` at module level, populated by `initialize_config` fixture in conftest

**Environment switching (Lighthouse)**: pass `environment=` to `SpeedtestService(...)` constructor — do not write to `base_urls.ini`.  
**Environment switching (REST/content tests)**: pass `--environment=VRP_PROD` CLI flag or `environment=` to `BaseApiClient(...)`.

### Google Sheets (`services/google/google_sheets_client.py`)

Service account auth → batch row buffer → `flush()` writes all rows. Template sheets (`_CLI_Template`, `_API_Template`, `_ChU_Template`) cloned for new worksheets.

### Auxiliary services

- `services/ZOHO/` — Zoho Projects API client (`Zoho_api_client.py`) + models (User, TaskStatus, DefectStatus, portal_data). Config in `config_zoho.env`. Tests in `test_zoho.py` are **ignored** by `pytest.ini`.
- `services/Release_Test_Plan/TestPlanGenerator.py` — generates QA release test plans from Zoho sprint data.
- `services/lighthouse/Google Sheet/*.gs` — Google Apps Script for Sheets dashboard; mirrored under `tools/clasp/` as `.js` for clasp deployment.

## Key Conventions

- **Language**: Russian in all comments, docstrings, and log/print output
- **Markers**: `@pytest.mark.performance`, `@pytest.mark.functional`
- Lighthouse device types: `"desktop"` or `"mobile"` (match config JSON filenames in `configs/`)
- Reports written to `Reports/reports_lighthouse/`; temp Lighthouse JSON to `Reports/reports_lighthouse/temp_lighthouse/`
- `.env` files (`.env`, `config_lighthouse.env`, `config_zoho.env`) are gitignored — keep credentials out of code