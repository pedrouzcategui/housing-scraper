import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from playwright.async_api import Page
else:
    Page = Any

_LOG_DIR = "logs"


def setup_logger(log_dir: str = "logs", level: str = "INFO"):
    """No-op initializer kept for compatibility; ensures log dir exists."""
    # Maintain signature; create the directory so snapshots can be saved.
    global _LOG_DIR
    _LOG_DIR = log_dir
    os.makedirs(log_dir, exist_ok=True)
    # Using prints instead of logger per request.


async def log_failure(
    page: Optional[Page],
    href: Optional[str],
    exc: Exception,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Capture context when scraping fails; print and save HTML + screenshot."""
    from utils.console import console
    context: Dict[str, Any] = {"href": href}

    page_url = None
    if page:
        try:
            page_url = page.url
        except Exception:
            page_url = None
    context["page_url"] = page_url

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    html_path = None
    screenshot_path = None
    if page:
        try:
            os.makedirs(_LOG_DIR, exist_ok=True)
            html_content = await page.content()
            html_path = os.path.join(_LOG_DIR, f"failure_{timestamp}.html")
            with open(html_path, "w", encoding="utf-8") as snapshot:
                snapshot.write(html_content)
        except Exception as html_exc:
            console.print(f"[yellow]Warning:[/] Unable to capture HTML snapshot: {html_exc}")
        try:
            screenshot_path = os.path.join(_LOG_DIR, f"failure_{timestamp}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
        except Exception as shot_exc:
            console.print(f"[yellow]Warning:[/] Unable to capture screenshot: {shot_exc}")
    context["html_snapshot"] = html_path
    context["screenshot"] = screenshot_path

    if extra:
        context.update(extra)

    console.print("[red]Scrape failure:[/]", context)
    console.print("[red]Error:[/]", exc)
