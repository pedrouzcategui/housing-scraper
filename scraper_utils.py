import asyncio
from playwright.async_api import Page

def get_element_by_id(page: Page, element_id: str):
    return page.locator(f"#{element_id}").first

def get_elements_by_classname(page: Page, class_name: str):
    return page.locator(f".{class_name}")

async def scroll_to_load_all(page: Page, pause: float = 1.0, max_scrolls: int = 30):
    """Scroll the page to load lazy content until no more height changes or max_scrolls reached."""
    previous_height = await page.evaluate("() => document.body.scrollHeight") # This gives you the entire height of the page
    for _ in range(max_scrolls):
        await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)") # This evaluate function is like calling an eval on javascript
        await asyncio.sleep(pause)
        new_height = await page.evaluate("() => document.body.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height