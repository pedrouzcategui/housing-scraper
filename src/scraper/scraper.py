import asyncio
import random
import re
from datetime import date

from playwright.async_api import Page, async_playwright
from playwright_stealth import Stealth
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from scraper.config import (
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
from db.models import Listing, ListingPrice
from db.session import get_engine
from utils.scraper import (
    get_element_by_id,
    get_elements_by_classname,
    scroll_like_human,
    extract_coordinates_from_staticmap,
)
from utils.network_usage import NetworkUsage

def extract_listing_id_from_url(url: str) -> str:
    match = re.search(r'/MLV-(\d+)', url)
    return match.group(1) if match else ""


def _split_city_state(city_query: str) -> tuple[str, str | None]:
    parts = [p.strip() for p in (city_query or "").split(",") if p.strip()]
    if len(parts) >= 2:
        return parts[0], parts[1]
    if len(parts) == 1:
        return parts[0], None
    return "", None


async def extract_gallery_image_urls(page: Page) -> list[str]:
    """Extract full-size gallery image URLs from MercadoLibre listing pages.

    Prefers `data-zoom` when present (often the largest), falls back to `src`.
    """
    try:
        locator = page.locator(".ui-pdp-gallery__figure__image")
        if await locator.count() == 0:
            return []

        urls: list[str] = await locator.evaluate_all(
            """els => els
                .map(e => e.getAttribute('data-zoom') || e.getAttribute('src') || '')
                .filter(Boolean)
            """
        )

        cleaned: list[str] = []
        seen: set[str] = set()
        for u in urls:
            if not u or u.startswith("data:"):
                continue
            if u not in seen:
                seen.add(u)
                cleaned.append(u)
        return cleaned
    except Exception:
        return []


def _persist_listing_and_daily_price(*, listing: Listing | None, mercadolibre_id: str, price: float | None) -> None:
    """Persist Listing (only if new) and today's ListingPrice (only if missing).

    - If the listing already exists, it is NOT updated.
    - If today's price row already exists (by mercadolibre id + day), it is skipped.
    """

    if not mercadolibre_id:
        return

    with Session(get_engine()) as session:
        existing_listing = session.exec(
            select(Listing).where(Listing.mercadolibre_listing_id == mercadolibre_id)
        ).first()

        if existing_listing is None:
            if listing is None:
                # Can't create price history without a Listing record.
                return
            session.add(listing)
            session.commit()
            session.refresh(listing)
            existing_listing = listing
        else:
            # Do not update existing listing
            pass

        today = date.today()
        already_scanned = session.exec(
            select(ListingPrice).where(
                ListingPrice.mercadolibre_listing_id == mercadolibre_id,
                ListingPrice.day == today,
            )
        ).first()
        if already_scanned is not None:
            return

        price_row = ListingPrice(
            listing_id=existing_listing.id,
            mercadolibre_listing_id=mercadolibre_id,
            day=today,
            price=price,
        )
        try:
            session.add(price_row)
            session.commit()
        except IntegrityError:
            # Another worker/thread inserted concurrently.
            session.rollback()


def _listing_exists_by_mlvid(mercadolibre_id: str) -> bool:
    if not mercadolibre_id:
        return False
    with Session(get_engine()) as session:
        existing = session.exec(
            select(Listing.id).where(Listing.mercadolibre_listing_id == mercadolibre_id)
        ).first()
        return existing is not None


# This function scrapes detailed information from a listing page
async def get_listing_information(page: Page, *, city_query: str):
    try:
        mercadolibre_id = extract_listing_id_from_url(page.url)
        city, state = _split_city_state(city_query)
        
        # before scrolling
        console.print("[italic]Scrolling listings on page...[/]")
        
        await scroll_like_human(page, delay=random.uniform(1.0, 6.0), max_scrolls=4)

        # Price is needed even when we skip listing updates.
        price = await page.locator(
            f'meta[itemprop="{PRICE_META_PROPERTY}"]'
        ).get_attribute("content")
        price_value = float(price) if price else None

        # If listing already exists, do NOT update it; only persist today's price.
        if await asyncio.to_thread(_listing_exists_by_mlvid, mercadolibre_id):
            await asyncio.to_thread(
                _persist_listing_and_daily_price,
                listing=None,
                mercadolibre_id=mercadolibre_id,
                price=price_value,
            )
            console.print(f"[yellow]Listing exists; skipped update[/] [bold]{mercadolibre_id}[/]")
            return None

        title = await page.locator(f".{LISTING_TITLE_HTML_CLASSNAME}").text_content()
        type_ = await page.locator(f".{APARTMENT_OR_HOUSE_HTML_CLASSNAME}").text_content()
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

        images = await extract_gallery_image_urls(page)

        listing_obj = Listing(
            mercadolibre_listing_id=mercadolibre_id,
            title=title,
            state=state,
            city=city,
            p_type=type_,
            price=price_value,
            listing_type=listing_type,
            description=description,
            area=float(area) if area else None,
            rooms=int(rooms) if rooms else None,
            bathrooms=int(bathrooms) if bathrooms else None,
            latitude=lat,
            longitude=lon,
            images=images,
        )

        # Run DB I/O off the event loop (important once running multiple agents)
        await asyncio.to_thread(
            _persist_listing_and_daily_price,
            listing=listing_obj,
            mercadolibre_id=mercadolibre_id,
            price=price_value,
        )
        console.print(f"[green]Saved listing + today's price[/] [bold]{mercadolibre_id}[/]")
        console.print(f"[green]Finished scraping listing[/] [bold]{mercadolibre_id}[/]")
        return listing_obj
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

async def get_all_listings_information(page: Page, *, city_query: str):
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
            info = await get_listing_information(page, city_query=city_query)
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

async def get_all_listings_by_city(page: Page, city_query: str):
    console.print(f"[bold]Starting search for city[/]: {city_query}")
    try:
        searchbox = get_element_by_id(page, SEARCHBOX_HTML_ID)
        await searchbox.click()
        await page.keyboard.type(city_query, delay=random.randint(100, 200))
        await asyncio.sleep(random.uniform(3.0, 6.0))
        await searchbox.press("Enter")
        await page.wait_for_selector(f".{LISTING_ITEM_HTML_CLASSNAME}")  # Wait for listings to load

        while True:
            await get_all_listings_information(page, city_query=city_query)
            next_button = get_elements_by_classname(page, NEXT_BUTTON_HTML_CLASSNAME)
            if not await next_button.is_visible():
                console.print(f"[yellow]No more pages for city[/] '{city_query}'")
                break
            await next_button.click()
            console.print(f"[blue]Navigated to next page for city[/]: '{city_query}'")
            await page.wait_for_load_state("networkidle")  # Keep for pagination, or replace with selector if needed
    except Exception as exc:
        print(f"Error in get_all_listings_by_city for city '{city_query}': {exc}")
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
            inbound_mb = snap.get("inbound", {}).get("megabytes", 0)
            outbound_mb = snap.get("outbound", {}).get("megabytes", 0)
            total_gb = snap.get("total", {}).get("gigabytes", 0)
            console.print(
                f"[cyan]Estimated proxy data[/] "
                f"inbound={inbound_mb} MB, "
                f"outbound={outbound_mb} MB, "
                f"total≈{total_gb} GB"
            )
            # Logging handlers flush removed; using prints now