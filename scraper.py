import asyncio
import random
import re

from playwright.async_api import Page, async_playwright
from playwright_stealth import Stealth

from config import (
    APARTMENT_OR_HOUSE_HTML_CLASSNAME,
    DEBUG_MODE,
    LISTING_DESCRIPTION_HTML_CLASSNAME,
    LISTING_ITEM_HTML_CLASSNAME,
    LISTING_TITLE_HTML_CLASSNAME,
    LISTING_TYPE_HTML_CLASSNAME,
    LOG_DIR,
    LOG_LEVEL,
    MERCADOLIBRE_URL,
    NEXT_BUTTON_HTML_CLASSNAME,
    PRICE_META_PROPERTY,
    SEARCHBOX_HTML_ID,
    SPECS_CONTAINER_CLASSNAME,
)
from logging_utils import log_failure, logger, setup_logger
from models import Property
import json
import os
from datetime import datetime, timezone
from scraper_utils import (
    get_element_by_id,
    get_elements_by_classname,
    scroll_like_human,
    get_current_page_number,
)

def extract_listing_id_from_url(url: str) -> str:
    match = re.search(r'/MLV-(\d+)', url)
    return match.group(1) if match else ""

# This function scrapes detailed information from a listing page
async def get_listing_information(page: Page):
    try:
        mercadolibre_id = extract_listing_id_from_url(page.url)
        
        # before scrolling
        logger.info("Scrolling listings on page...")
        
        await scroll_like_human(page, delay=random.uniform(1.0, 6.0), max_scrolls=4)
        title = await page.locator(f".{LISTING_TITLE_HTML_CLASSNAME}").text_content()
        type_ = await page.locator(f".{APARTMENT_OR_HOUSE_HTML_CLASSNAME}").text_content()
        price = await page.locator(
            f'meta[itemprop="{PRICE_META_PROPERTY}"]'
        ).get_attribute("content")
        listing_type = await page.locator(f".{LISTING_TYPE_HTML_CLASSNAME}").text_content()
        desc_el = await page.query_selector(f".{LISTING_DESCRIPTION_HTML_CLASSNAME}")
        description = await desc_el.text_content() if desc_el else None

        specs_texts = await page.locator(
            f".{SPECS_CONTAINER_CLASSNAME} .ui-pdp-label span"
        ).all_text_contents()
        area = rooms = bathrooms = None
        for text in specs_texts:
            if "m²" in text:
                match = re.search(r"(\d+)", text)
                area = match.group(1) if match else None
            elif "cuarto" in text:
                rooms = text.split()[0]
            elif "baños" in text:
                bathrooms = text.split()[0]

        property_obj = Property(
            mercadolibre_listing_id=mercadolibre_id,
            title=title,
            p_type=type_,
            price=float(price) if price else None,
            listing_type=listing_type,
            description=description,
            area=float(area) if area else None,
            rooms=int(rooms) if rooms else None,
            bathrooms=int(bathrooms) if bathrooms else None,
        )

        property_obj.save()
        logger.info("Saved listing %s", mercadolibre_id)
        logger.info("Finished scraping listing %s", mercadolibre_id)
        return property_obj
    except Exception as exc:
        await log_failure(
            page,
            page.url if page else None,
            exc,
            {"step": "get_listing_information", "listing_url": page.url if page else None},
        )
        if DEBUG_MODE:
            raise
        return None

async def get_all_listings_information(page: Page):
    await scroll_like_human(page, delay=random.uniform(1.0, 10.0), max_scrolls=40)
    await page.wait_for_selector(f".{LISTING_ITEM_HTML_CLASSNAME}")
    listings = get_elements_by_classname(page, LISTING_ITEM_HTML_CLASSNAME)
    hrefs = []
    for listing in await listings.all():
        href = await listing.locator("a").first.get_attribute("href")
        if href:
            hrefs.append(href)

    # Pretty-print to console
    print(len(hrefs), "listings found on current page:")

    logger.info("Collected %s listing hrefs", len(hrefs))

    for href in hrefs:
        await asyncio.sleep(random.uniform(3.0, 10.0))
        navigated = False
        try:
            await page.goto(href)
            navigated = True
            logger.info("Visiting %s", href)
            info = await get_listing_information(page)
            if info:
                logger.info("Finished scraping listing %s (%s)", info.mercadolibre_listing_id, href)
                logger.debug("Scraped listing %s", info.mercadolibre_listing_id)
        except Exception as exc:
            await log_failure(page, href, exc, {"step": "get_all_listings_information"})
            if DEBUG_MODE:
                raise
        finally:
            delay = random.uniform(15.0, 20.0)
            await asyncio.sleep(delay)
            if navigated:
                try:
                    await page.go_back()
                except Exception as back_exc:
                    await log_failure(
                        page,
                        href,
                        back_exc,
                        {"step": "return_to_list", "listing_href": href},
                    )
                    if DEBUG_MODE:
                        raise

async def get_all_listings_by_city(page: Page, city: str):
    logger.info("Starting search for city '%s'", city)
    try:
        searchbox = get_element_by_id(page, SEARCHBOX_HTML_ID)
        await searchbox.click()
        await page.keyboard.type(city, delay=random.randint(100, 200))
        await asyncio.sleep(random.uniform(3.0, 6.0))
        await searchbox.press("Enter")
        await page.wait_for_selector(f".{LISTING_ITEM_HTML_CLASSNAME}")  # Wait for listings to load

        while True:
            await get_all_listings_information(page)
            next_button = get_elements_by_classname(page, NEXT_BUTTON_HTML_CLASSNAME)
            if not await next_button.is_visible():
                logger.info("No more pages for city '%s'", city)
                break
            await next_button.click()
            logger.debug("Navigated to next page for city '%s'", city)
            await page.wait_for_load_state("networkidle")  # Keep for pagination, or replace with selector if needed
    except Exception as exc:
        await log_failure(page, page.url if page else None, exc, {"city": city, "step": "get_all_listings_by_city"})
        if DEBUG_MODE:
            raise

async def get_all_listings_by_state(page: Page, state: str):
    pass

async def main(city: str):
    setup_logger(LOG_DIR, LOG_LEVEL)
    async with Stealth().use_async(async_playwright()) as playwright_instance:
        logger.info("Launching browser for city '%s'", city)
        browser = await playwright_instance.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context()
        await context.add_init_script(
            """
                Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
                })
            """
        )

        page = await context.new_page()
        try:
            await page.goto(MERCADOLIBRE_URL)
            logger.info("Opened search page: %s", MERCADOLIBRE_URL)
            await get_all_listings_by_city(page, city)
        except Exception as exc:
            await log_failure(page, page.url if page else None, exc, {"city": city, "step": "main"})
            if DEBUG_MODE:
                raise
        finally:
            await browser.close()
            logger.info("Browser closed for city '%s'", city)
            
            # Explicitly flush handlers
            for handler in logger.handlers:
                try:
                    handler.flush()
                    handler.close()
                except Exception:
                    pass