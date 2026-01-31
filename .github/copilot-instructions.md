# Copilot instructions (housing-scraper)

## Project overview

- This repo is an async Playwright scraper for MercadoLibre Venezuela listings.
- Core flow: [src/main.py](../src/main.py) -> `scraper.scraper.main()` ([src/scraper/scraper.py](../src/scraper/scraper.py)) -> scrape listing pages -> persist a subset of fields to PostgreSQL (recommended) via `Listing.save()` ([src/db/models/property.py](../src/db/models/property.py)) using SQLModel/SQLAlchemy sessions.
- Logging is first-class: rotating log file + console via `setup_logger()`, and HTML snapshots on failures via `log_failure()` ([logging_utils.py](../logging_utils.py)).

## Developer workflow (Windows / PowerShell)

- Use `uv` for everything:
  - Run: `uv run src/main.py`
  - Add deps: `uv add <package>`
  - Install Playwright browsers: `uv run playwright install`
- Required environment variables come from `.env` loaded by [config.py](../config.py):
  - `MERCADOLIBRE_APARTAMENTOS_URL` (start/search page URL)
  - `DATABASE_URL` (SQLAlchemy URL; recommended Postgres)
  - Optional: `LOG_DIR` (default `logs`), `LOG_LEVEL` (default `INFO`)

## Runtime behavior you must know

- `DEBUG_MODE` is controlled via env vars in [config.py](../config.py) (`DEBUG_MODE` or `PWDEBUG`). When enabled:
  - [src/main.py](../src/main.py) calls `Database.initialize_fresh()` on every run (drops/recreates tables).
  - Errors inside scrape steps are re-raised after logging (`if DEBUG_MODE: raise`).
- PowerShell example: `$env:PWDEBUG=1; uv run src/main.py`.

## Scraper patterns (Playwright)

- Uses `playwright.async_api` + `playwright-stealth`:
  - Browser bootstrapping is in `scraper.main()` ([scraper.py](../scraper.py)); it launches Chromium with `headless=False` and `slow_mo=100`.
  - Also applies an init script to mask `navigator.webdriver`.
- DOM access style:
  - Helpers in [scraper_utils.py](../scraper_utils.py) return Playwright `Locator`s; locators are not awaited until you perform an action (`click`, `text_content`, `get_attribute`, etc.).
  - Human-ish behavior is important: `scroll_like_human()` is called before extracting listing content.
- Failure handling convention:
  - Wrap scrape steps in `try/except`, call `await log_failure(page, href_or_url, exc, {"step": "..."})`, then re-raise only when `DEBUG_MODE` is enabled.

## Database/model conventions (SQLite)

SQLite is supported as a fallback for local dev/tests, but the primary database is PostgreSQL via `DATABASE_URL`.

## Existing testing situation

- There is a small pytest suite under `tests/`.
- There is an exploratory Playwright stealth check script at [test-playwright-stealth.py](../test-playwright-stealth.py) (uses https://bot.sannysoft.com/).
