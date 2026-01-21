import pytest

from src.utils.scraper import (
    extract_coordinates_from_staticmap,
    get_current_page_number,
    get_element_by_id,
    get_elements_by_classname,
)


class FakeLocator:
    def __init__(self, *, count: int = 0, text: str | None = None, attr: dict | None = None):
        self._count = count
        self._text = text
        self._attr = attr or {}
        self._first = self

    async def count(self) -> int:
        return self._count

    @property
    def first(self):
        return self._first

    async def text_content(self):
        return self._text

    async def get_attribute(self, name: str):
        return self._attr.get(name)


class FakePage:
    def __init__(self, url: str = "https://example.test/"):
        self.url = url
        self.seen_selectors: list[str] = []
        self._locators: dict[str, FakeLocator] = {}

    def with_locator(self, selector: str, locator: FakeLocator):
        self._locators[selector] = locator
        return self

    def locator(self, selector: str):
        self.seen_selectors.append(selector)
        return self._locators.get(selector, FakeLocator())


def test_get_element_by_id_builds_css_id_selector():
    page = FakePage().with_locator("#cb1-edit", FakeLocator(count=1))
    loc = get_element_by_id(page, "cb1-edit")
    assert page.seen_selectors[-1] == "#cb1-edit"
    assert loc is page._locators["#cb1-edit"].first


def test_get_elements_by_classname_builds_css_class_selector():
    page = FakePage().with_locator(".andes", FakeLocator(count=1))
    _ = get_elements_by_classname(page, "andes")
    assert page.seen_selectors[-1] == ".andes"


@pytest.mark.asyncio
async def test_get_current_page_number_from_dom_selector():
    page = FakePage().with_locator('button[aria-current="true"]', FakeLocator(count=1, text="7"))
    assert await get_current_page_number(page) == "7"


@pytest.mark.asyncio
async def test_get_current_page_number_from_url_p_param_when_dom_missing():
    page = FakePage(url="https://example.test/search?p=3")
    assert await get_current_page_number(page) == "3"


@pytest.mark.asyncio
async def test_get_current_page_number_from_url_desde_offset():
    page = FakePage(url="https://example.test/search/_Desde_100")
    # 100 offset, 50 per page => page 3
    assert await get_current_page_number(page) == "3"


@pytest.mark.asyncio
async def test_extract_coordinates_from_staticmap_parses_center_param():
    src = "https://maps.google.com/staticmap?center=10.5%2C-66.9&zoom=15"
    page = FakePage().with_locator(".ui-pdp-image", FakeLocator(count=1, attr={"src": src}))
    lat, lon = await extract_coordinates_from_staticmap(page, "ui-pdp-image")
    assert lat == 10.5
    assert lon == -66.9


@pytest.mark.asyncio
async def test_extract_coordinates_from_staticmap_returns_none_when_missing():
    page = FakePage()
    lat, lon = await extract_coordinates_from_staticmap(page, "ui-pdp-image")
    assert lat is None
    assert lon is None
