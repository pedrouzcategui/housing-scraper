import os
from dotenv import load_dotenv

load_dotenv()


def _parse_bool_env(value: str) -> bool:
	v = (value or "").strip().lower()
	if v in {"1", "true", "yes", "on"}:
		return True
	if v in {"0", "false", "no", "off"}:
		return False
	raise ValueError(f"Unrecognized boolean value: {value!r}")


def _get_bool_env(*names: str, default: bool = False) -> bool:
	for name in names:
		raw = os.getenv(name)
		if raw is None:
			continue
		try:
			return _parse_bool_env(raw)
		except ValueError:
			# Keep behavior predictable: if user set something weird, fall back.
			return default
	return default

MERCADOLIBRE_URL = os.getenv("MERCADOLIBRE_APARTAMENTOS_URL")
DEBUG_MODE = _get_bool_env("DEBUG_MODE", "PWDEBUG", default=False)

LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

SEARCHBOX_HTML_ID = "cb1-edit"

# Listing related constants
LISTING_ITEM_HTML_CLASSNAME = "ui-search-layout__item"
LISTING_TITLE_HTML_CLASSNAME = "ui-pdp-title"
LISTING_TYPE_HTML_CLASSNAME = "ui-pdp-subtitle" # Whether is "house" or "apartment"
APARTMENT_OR_HOUSE_HTML_CLASSNAME = "ui-pdp-subtitle"
LISTING_DESCRIPTION_HTML_CLASSNAME = "ui-pdp-description__content"
SPECS_CONTAINER_CLASSNAME = "ui-pdp-highlighted-specs-res"
PRICE_META_PROPERTY = "price"
NEXT_BUTTON_HTML_CLASSNAME = "andes-pagination__button--next"
MAP_IMAGE = "ui-pdp-image"