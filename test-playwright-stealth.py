import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from utils.console import console


async def main():
    # This is the recommended usage. All pages created will have stealth applied:
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto('https://bot.sannysoft.com/')
        await page.pause()
        await page.screenshot(path=f'example-stealthy-playwright.png')
        webdriver_status = await page.evaluate("navigator.webdriver")
        console.print("from new_page:", webdriver_status)

        different_context = await browser.new_context()
        page_from_different_context = await different_context.new_page()

        different_context_status = await page_from_different_context.evaluate("navigator.webdriver")
        console.print("from new_context:", different_context_status)


asyncio.run(main())