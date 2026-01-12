import asyncio
import random
from playwright.async_api import Page

def get_element_by_id(page: Page, element_id: str):
    return page.locator(f"#{element_id}").first

def get_elements_by_classname(page: Page, class_name: str):
    return page.locator(f".{class_name}")

async def scroll_like_human(page: Page, delay: float, max_scrolls: int = 30) -> None:

    # This gets the scroll height of the body of the page
    previous_height = await page.evaluate("document.body.scrollHeight")
    
    for i in range(max_scrolls):
        # 1. Smooth scroll relative to current position
        scroll_amount = random.randint(100, 600)
        # 2. This evaluation simulates a smooth scroll by a random amount
        await page.evaluate(f"""
            window.scrollBy({{
                top: {scroll_amount},
                behavior: 'smooth'
            }});
        """)

        # 2. Wait for the smooth animation AND the network
        await asyncio.sleep(delay)
        
        # 3. Check if we actually moved or if height grew
        new_height = await page.evaluate("document.body.scrollHeight")
        current_scroll_pos = await page.evaluate("window.pageYOffset + window.innerHeight")

        # Logic: If height hasn't changed AND we are at the bottom, we are done
        if new_height == previous_height and current_scroll_pos >= new_height:
            print("Reached the end of the page.")
            break
            
        previous_height = new_height
