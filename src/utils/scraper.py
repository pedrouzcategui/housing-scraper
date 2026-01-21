import asyncio
import random
from playwright.async_api import Page
from typing import Optional, Tuple
import urllib.parse

def get_element_by_id(page: Page, element_id: str):
    return page.locator(f"#{element_id}").first

def get_elements_by_classname(page: Page, class_name: str):
    return page.locator(f".{class_name}")

async def scroll_like_human(
    page: Page,
    delay: float,
    max_scrolls: int = 30,
    is_reverse: bool = False,
) -> None:

    # This gets the scroll height of the body of the page
    previous_height = await page.evaluate("document.body.scrollHeight")
    
    for i in range(max_scrolls):
        # 1. Smooth scroll relative to current position
        scroll_amount = random.randint(100, 600)
        if is_reverse:
            scroll_amount = -scroll_amount

        # 2. This evaluation simulates a smooth scroll by a random amount
        await page.evaluate(f"""
            window.scrollBy({{
                top: {scroll_amount},
                behavior: 'smooth'
            }});
        """)

        # 2. Wait for the smooth animation AND the network
        await asyncio.sleep(delay)
        
        if is_reverse:
            # Check if we've reached the top of the page
            current_scroll_pos = await page.evaluate("window.pageYOffset")
            if current_scroll_pos <= 0:
                print("Reached the top of the page.")
                break
            continue

        # 3. Check if we actually moved or if height grew
        new_height = await page.evaluate("document.body.scrollHeight")
        current_scroll_pos = await page.evaluate(
            "window.pageYOffset + window.innerHeight"
        )

        # Logic: If height hasn't changed AND we are at the bottom, we are done
        if new_height == previous_height and current_scroll_pos >= new_height:
            print("Reached the end of the page.")
            break
            
        previous_height = new_height

async def get_current_page_number(page: Page) -> str:
    # Try common DOM selectors first
    selectors = [
        'button[aria-current="true"]',
        'li[aria-current="page"]',
        '.andes-pagination__button--current',
        '.andes-pagination__button--selected'
    ]
    for sel in selectors:
        try:
            el = page.locator(sel)
            if await el.count() > 0:
                txt = (await el.first.text_content()).strip()
                if txt:
                    return txt
        except Exception:
            pass

    # Fallback: parse URL for common pagination params (page, Desde/offset)
    import re
    url = page.url or ""
    m = re.search(r'(?:[?&]p=(\d+))', url)
    if m:
        return m.group(1)
    m = re.search(r'(?:_Desde_?=?(\d+))', url)
    if m:
        # MercadoLibre uses offsets sometimes — compute approximate page
        try:
            offset = int(m.group(1))
            per_page = 50  # adjust if your search shows different results per page
            return str(offset // per_page + 1)
        except Exception:
            return m.group(1)
    return "unknown"

async def extract_coordinates_from_staticmap(
    page: Page,
    class_name: str,
) -> Tuple[Optional[float], Optional[float]]:
    """Extract latitude/longitude from a Google Static Maps <img> by parsing its src.

    Looks for an element with the given class name, reads its `src`, parses the
    `center=<lat>,<lon>` query param, and returns floats if available.
    """
    try:
        img = page.locator(f".{class_name}").first
        if await img.count() == 0:
            return None, None
        src = await img.get_attribute("src")
        if not src:
            return None, None

        parsed = urllib.parse.urlparse(src)
        qs = urllib.parse.parse_qs(parsed.query)
        center_vals = qs.get("center")
        if not center_vals:
            return None, None
        center = urllib.parse.unquote(center_vals[0])
        parts = center.split(",")
        if len(parts) != 2:
            return None, None
        try:
            lat = float(parts[0])
            lon = float(parts[1])
            return lat, lon
        except Exception:
            return None, None
    except Exception:
        return None, None
