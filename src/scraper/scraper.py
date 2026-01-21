import asyncio
import random
import re

from playwright.async_api import Page, async_playwright
from playwright_stealth import Stealth

from src.scraper.config import (
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
    MAP_IMAGE,
)
from utils.logging import log_failure, setup_logger
from utils.console import console
from db.models import Property
from utils.scraper import (
    get_element_by_id,
    get_elements_by_classname,
    scroll_like_human,
    extract_coordinates_from_staticmap,
)
from src.utils.network_usage import NetworkUsage

def extract_listing_id_from_url(url: str) -> str:
    match = re.search(r'/MLV-(\d+)', url)
    return match.group(1) if match else ""

# This function scrapes detailed information from a listing page
async def get_listing_information(page: Page):
    try:
        mercadolibre_id = extract_listing_id_from_url(page.url)
        
        # before scrolling
        console.print("[italic]Scrolling listings on page...[/]")
        
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

        # Extract optional coordinates from the static map image
        lat, lon = await extract_coordinates_from_staticmap(page, MAP_IMAGE)

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
            latitude=lat,
            longitude=lon,
        )

        property_obj.save()
        console.print(f"[green]Saved listing[/] [bold]{mercadolibre_id}[/]")
        console.print(f"[green]Finished scraping listing[/] [bold]{mercadolibre_id}[/]")
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
    console.print(f"[cyan]{len(hrefs)} listings found on current page[/]")
    console.print(f"[cyan]Collected {len(hrefs)} listing hrefs[/]")

    for href in hrefs:
        await asyncio.sleep(random.uniform(3.0, 10.0))
        navigated = False
        try:
            await page.goto(href)
            navigated = True
            console.print(f"[magenta]Visiting[/] {href}")
            info = await get_listing_information(page)
            if info:
                console.print(f"[green]Finished scraping listing[/] {info.mercadolibre_listing_id} ({href})")
                console.print(f"[green]Scraped listing[/] {info.mercadolibre_listing_id}")
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
    console.print(f"[bold]Starting search for city[/]: {city}")
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
                console.print(f"[yellow]No more pages for city[/] '{city}'")
                break
            await next_button.click()
            console.print(f"[blue]Navigated to next page for city[/]: '{city}'")
            await page.wait_for_load_state("networkidle")  # Keep for pagination, or replace with selector if needed
    except Exception as exc:
        print(f"Error in get_all_listings_by_city for city '{city}': {exc}")
        if DEBUG_MODE:
            raise

async def get_all_listings_by_state(page: Page, state: str):
    pass

async def main(city: str):
    setup_logger(LOG_DIR, LOG_LEVEL)
    async with Stealth().use_async(async_playwright()) as playwright_instance:
        console.print(f"[bold]Launching browser for city[/] '{city}'")
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
        # Attach network usage tracker
        net = NetworkUsage()
        net.attach(page)

        try:
            await page.goto(MERCADOLIBRE_URL)
            console.print(f"[blue]Opened search page[/]: {MERCADOLIBRE_URL}")
            await get_all_listings_by_city(page, city)
        except Exception as exc:
            console.print(f"[red]Error in main for city[/] '{city}': {exc}")
            if DEBUG_MODE:
                raise
        finally:
            await browser.close()
            console.print(f"[blue]Browser closed for city[/] '{city}'")
            snap = net.snapshot()
            console.print(
                f"[cyan]Estimated proxy data[/] "
                f"inbound={snap['inbound_mb']} MB, "
                f"outbound={snap['outbound_mb']} MB, "
                f"total≈{snap['total_gb']} GB"
            )
            # Logging handlers flush removed; using prints now