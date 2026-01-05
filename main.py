import os
import asyncio
from dotenv import load_dotenv
# This only works for sync code -> from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright, Page

load_dotenv()

MERCADOLIBRE_URL = os.getenv("MERCADOLIBRE_APARTAMENTOS_URL")
SEARCHBOX_HTML_ID = "cb1-edit"

# Make sure to indicate that page is of type Page
def get_element_by_id(page: Page, element_id: str):
    return page.locator(f"#{element_id}").first

async def main():
    # Simple Request with Playwright to env URL
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        page = await browser.new_page()
        await page.goto(MERCADOLIBRE_URL)
        searchbox = get_element_by_id(page, SEARCHBOX_HTML_ID)
        await searchbox.fill("San Antonio de Los Altos")
        # Enter key press simulation
        await searchbox.press("Enter")
        # Wait some time to see results
        await asyncio.sleep(5)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())