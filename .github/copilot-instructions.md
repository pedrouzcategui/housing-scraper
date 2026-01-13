# Copilot instructions (housing-scraper)

## Project overview

- This repo is an async Playwright scraper for MercadoLibre Venezuela listings.
- Core flow: [main.py](../main.py) -> `scraper.main()` ([scraper.py](../scraper.py)) -> scrape listing pages -> persist a subset of fields to SQLite via `Property.save()` ([models.py](../models.py)) using `Database.execute_query()` ([db.py](../db.py)).
- Logging is first-class: rotating log file + console via `setup_logger()`, and HTML snapshots on failures via `log_failure()` ([logging_utils.py](../logging_utils.py)).

## Developer workflow (Windows / PowerShell)

- Use `uv` for everything:
  - Run: `uv run main.py`
  - Add deps: `uv add <package>`
  - Install Playwright browsers: `uv run playwright install`
- Required environment variables come from `.env` loaded by [config.py](../config.py):
  - `MERCADOLIBRE_APARTAMENTOS_URL` (start/search page URL)
  - `DATABASE_NAME` (SQLite path; common value: `properties.db`)
  - Optional: `LOG_DIR` (default `logs`), `LOG_LEVEL` (default `INFO`)

## Runtime behavior you must know

- `DEBUG_MODE` is controlled via env vars in [config.py](../config.py) (`DEBUG_MODE` or `PWDEBUG`). When enabled:
  - [main.py](../main.py) calls `Database.initialize_fresh()` on every run (drops/recreates the `properties` table).
  - Errors inside scrape steps are re-raised after logging (`if DEBUG_MODE: raise`).
- PowerShell example: `$env:PWDEBUG=1; uv run main.py`.

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

- SQLite schema is defined in `Database.initialize_database()` ([db.py](../db.py)).
- The `Property` model is a thin wrapper; keep schema + inserts + reads in sync:
  - Insert mapping is in `Property.save()` ([models.py](../models.py)).
  - Read mapping assumes `SELECT * FROM properties` column order and reconstructs objects as `Property(*row[1:], id=row[0])`.
  - If you add/remove a column, update: `CREATE TABLE` SQL, `INSERT` SQL/params, and the `Property.__init__` signature.

## Existing testing situation

- The `tests/` folder is currently empty.
- There is an exploratory Playwright stealth check script at [test-playwright-stealth.py](../test-playwright-stealth.py) (uses https://bot.sannysoft.com/).
