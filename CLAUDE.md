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

# Run Lighthouse service directly
py -m services.lighthouse.pagespeed_service

# MCP server (stdio)
python services/lighthouse/mcp_server.py
```

Pytest flags: `--browser=chrome|firefox`, `--headless`, `--local`, `--docker`, `--contour=development|staging|production`, `--screen-resolution=1920x1080`.

## Architecture

**Testing framework** (Pytest + Selenium) with a **Lighthouse performance service** and **Google Sheets** for results storage.

### Lighthouse Service (`services/lighthouse/`)

Three-layer architecture:

1. **Runners** — `cli_runner.py` (local Lighthouse CLI via subprocess), `api_runner.py` (Google PageSpeed API)
2. **Processor** — `processor_lighthouse.py` parses JSON, aggregates metrics (min/max/avg/p90), builds Sheets rows
3. **Orchestrator** — `pagespeed_service.py` (`SpeedtestService`) coordinates runners + processor + Google Sheets client

`mcp_server.py` — MCP server (FastMCP) wrapping SpeedtestService for Claude integration. 5 tools: `run_lighthouse`, `run_crux`, `list_environments`, `list_routes`, `get_status`.

### Configuration

- `URLs/base_urls.ini` — environment URLs. `[environments] current` selects active env. Sections: `VRS_DEV/TEST/STAGE/PROD`, `VRP_DEV/TEST/STAGE/PROD`
- `URLs/routes.ini` — route paths (`[routes]` section, key=path pairs)
- `services/lighthouse/configs/config_lighthouse.py` — paths, caching (`BASE_URL` global), helper functions
- `services/lighthouse/configs/config_lighthouse.env` — API keys, Google Sheets IDs, worksheet names
- `config.py` — global test config vars (browser, headless, etc.), initialized by conftest fixtures

**Environment switching**: write to `base_urls.ini` `[environments] current`, then reset `cfg.BASE_URL = None`.

### Google Sheets (`services/google/google_sheets_client.py`)

Service account auth → batch row buffer → `flush()` writes all rows. Template sheets (`_CLI_Template`, `_API_Template`, `_ChU_Template`) cloned for new worksheets.

### Test Structure (`test/`)

- `conftest.py` — fixtures (`browser`, `gui_service`, `service`), pytest CLI options, browser version auto-detection
- `simple_test.py` — GUI login tests (Selenium)
- `speed_test.py` — Lighthouse performance tests
- `test_zoho.py` — ignored via pytest.ini

### Page Objects (`POM/`)

Selenium Page Object Model. `AuthPage.py` for login, `selectors.py` for locators. `helper/StartSession.py` manages WebDriver lifecycle, `helper/GUIHelper.py` provides element interaction utilities.

## Key Conventions

- Language: Russian in comments, docstrings, and output messages
- Config keys in `base_urls.ini` are lowercase after ConfigParser processing (use `base_url` not `BASE_URL` when reading)
- Lighthouse metrics: P(erformance), LCP, FCP, TBT, CLS, SI, TTI, TTFB, INP
- CrUX data only available for `*_PROD` environments
- Device types: `"desktop"` or `"mobile"` (matching config JSON files)