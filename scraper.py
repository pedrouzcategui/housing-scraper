import asyncio
import re
from scraper_utils import get_element_by_id, get_elements_by_classname, scroll_to_load_all
from playwright.async_api import async_playwright, Page
from config import *


# This function scrapes detailed information from a listing page
async def get_listing_information(page: Page):
    title = await page.locator(f".{LISTING_TITLE_HTML_CLASSNAME}").text_content()
    type_ = await page.locator(f".{APARTMENT_OR_HOUSE_HTML_CLASSNAME}").text_content()  # It needs to be "type_" to avoid conflict with Python keyword
    price = await page.locator(f'meta[itemprop="{PRICE_META_PROPERTY}"]').get_attribute("content")
    listing_type = await page.locator(f".{LISTING_TYPE_HTML_CLASSNAME}").text_content()
    desc_el = await page.query_selector(f".{LISTING_DESCRIPTION_HTML_CLASSNAME}")
    description = await desc_el.text_content() if desc_el else None
    
    # Scrape specs: area, rooms, bathrooms
    specs_texts = await page.locator(f".{SPECS_CONTAINER_CLASSNAME} .ui-pdp-label span").all_text_contents()
    area = rooms = bathrooms = None
    for text in specs_texts:
        if "m²" in text:
            m = re.search(r"(\d+)", text)
            area = m.group(1) if m else None
        elif "cuarto" in text:
            rooms = text.split()[0]
        elif "baños" in text:
            bathrooms = text.split()[0]
    
    return {
        "title": title,
        "type": type_,
        "price": price,
        "listing_type": listing_type,
        "description": description,
        "area": area,
        "rooms": rooms,
        "bathrooms": bathrooms
    }

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        page = await browser.new_page()
        await page.goto(MERCADOLIBRE_URL)
        searchbox = get_element_by_id(page, SEARCHBOX_HTML_ID)
        await searchbox.fill("San Antonio de Los Altos")
        await searchbox.press("Enter")
        # Wait for results to appear, then scroll to load lazy items
        await page.wait_for_selector(f".{LISTING_ITEM_HTML_CLASSNAME}")
        await scroll_to_load_all(page, pause=1.0, max_scrolls=40)
        listings = get_elements_by_classname(page, LISTING_ITEM_HTML_CLASSNAME)
        hrefs = []
        print("Total listings found:", await listings.count())
        # await asyncio.sleep(20)  # Just to ensure all items are fully loaded
        for listing in await listings.all():
            href = await listing.locator("a").get_attribute("href")
            if href:
                hrefs.append(href)

        # Process all listings from current page
        for href in hrefs:
            await page.goto(href)
            info = await get_listing_information(page)
            print(f"Scraped: {info}")
            await asyncio.sleep(2)
            # Just for demonstration purposes, go back to listing page
            await page.go_back()
        await browser.close()