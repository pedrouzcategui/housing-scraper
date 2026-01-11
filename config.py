import os
from dotenv import load_dotenv

load_dotenv()

MERCADOLIBRE_URL = os.getenv("MERCADOLIBRE_APARTAMENTOS_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DEBUG_MODE = True

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