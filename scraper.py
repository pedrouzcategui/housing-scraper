import asyncio
import re
from scraper_utils import get_element_by_id, get_elements_by_classname, scroll_like_human
from playwright.async_api import async_playwright, Page
from config import *
import random

def extract_listing_id_from_url(url: str) -> str:
    match = re.search(r'/MLV-(\d+)', url)
    return match.group(1) if match else ""

# This function scrapes detailed information from a listing page
async def get_listing_information(page: Page):
    id = extract_listing_id_from_url(page.url)
    await scroll_like_human(page, pause=random.uniform(1.5, 2.5), max_scrolls=4)
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
        "id": id,
        "title": title,
        "type": type_,
        "price": price,
        "listing_type": listing_type,
        "description": description,
        "area": area,
        "rooms": rooms,
        "bathrooms": bathrooms
    }

async def get_all_listings_information(page: Page):
    # Wait for results to appear
    await scroll_like_human(page, pause=1.5, max_scrolls=40)
    # We select all items
    await page.wait_for_selector(f".{LISTING_ITEM_HTML_CLASSNAME}")
    listings = get_elements_by_classname(page, LISTING_ITEM_HTML_CLASSNAME)
    hrefs = []
    # await page.pause()
    for listing in await listings.all():
        # href = await listing.locator("a").get_attribute("href")
        href = await listing.locator("a").first.get_attribute("href")
        if href:
            hrefs.append(href)

    # for listing in await listings.all():
    #     await listing.click(position={"x": random.uniform(20, 30), "y": random.uniform(20, 40)})
    #     info = await get_listing_information(page)
    #     print(f"Scraped: {info}")
    #     delay = random.uniform(5.0, 15.0)
    #     await asyncio.sleep(delay)
    #     # Just for demonstration purposes, go back to listing page
    #     await page.go_back()

    for href in hrefs:
        await page.goto(href)
        info = await get_listing_information(page)
        print(f"Scraped: {info}")
        delay = random.uniform(15.0, 20.0)
        await asyncio.sleep(delay)
        # Just for demonstration purposes, go back to listing page
        await page.go_back()

async def get_all_listings_by_city(page: Page, city: str):
    searchbox = get_element_by_id(page, SEARCHBOX_HTML_ID)
    await searchbox.click()
    # The `type` method simulates typing with a delay between keystrokes
    await page.keyboard.type(city, delay=random.randint(100, 200))
    await asyncio.sleep(2)  # Wait for suggestions to load
    await searchbox.press("Enter")
    # Here is where the loop begins, basically we have to keep repeating the process while there is a next button
    next_button = get_elements_by_classname(page, NEXT_BUTTON_HTML_CLASSNAME)
    while (await next_button.is_visible()):
        await page.wait_for_load_state("networkidle")
        await get_all_listings_information(page)
        next_button = get_elements_by_classname(page, NEXT_BUTTON_HTML_CLASSNAME)
        await next_button.click()
        await page.wait_for_load_state("networkidle")  # Wait for the next page to load

async def get_all_listings_by_state(page: Page, state: str):
    pass

async def main():
    async with async_playwright() as p:
        city = input("Enter the city name: ")
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        page = await browser.new_page()
        await page.goto(MERCADOLIBRE_URL)
        await get_all_listings_by_city(page, city)
        await browser.close()