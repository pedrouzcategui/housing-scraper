import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from playwright.async_api import Page
else:
    Page = Any

LOGGER_NAME = "housing_scraper"
_LOG_DIR = "logs"


def setup_logger(log_dir: str = "logs", level: str = "INFO") -> logging.Logger:
    """Configure a rotating file + console logger and return it."""
    global _LOG_DIR
    _LOG_DIR = log_dir
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level.upper())

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(module)s:%(lineno)d - %(message)s"
        )

        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "scraper.log"),
            maxBytes=5_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger


logger = logging.getLogger(LOGGER_NAME)
logger.addHandler(logging.NullHandler())


async def log_failure(
    page: Optional[Page],
    href: Optional[str],
    exc: Exception,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Capture context (URL, href, optional HTML) when scraping fails."""
    log = logging.getLogger(LOGGER_NAME)
    context = {"href": href}

    page_url = None
    if page:
        try:
            page_url = page.url
        except Exception:
            page_url = None
    context["page_url"] = page_url

    html_path = None
    if page:
        try:
            os.makedirs(_LOG_DIR, exist_ok=True)
            html_content = await page.content()
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
            html_path = os.path.join(_LOG_DIR, f"failure_{timestamp}.html")
            with open(html_path, "w", encoding="utf-8") as snapshot:
                snapshot.write(html_content)
        except Exception:
            log.warning("Unable to capture HTML snapshot", exc_info=True)
    context["html_snapshot"] = html_path

    if extra:
        context.update(extra)

    log.error("Scrape failure context: %s", context, exc_info=exc)
