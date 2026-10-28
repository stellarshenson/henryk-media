"""Browser fixtures of the studio page tests: Chromium opens a studio page served with fakes."""

from types import SimpleNamespace

from playwright.sync_api import expect, sync_playwright
import pytest


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def open_studio(browser, make_studio, serve):
    """Serve a studio with the given generators and open its page; returns studio, client, page.

    Further keyword arguments go to the browser context, such as color_scheme or timezone_id."""
    contexts = []

    def open_(generators: dict | None = None, viewport=(1280, 900), **context) -> SimpleNamespace:
        studio = make_studio(generators)
        client = serve(studio)
        context = browser.new_context(
            viewport={"width": viewport[0], "height": viewport[1]}, **context
        )
        contexts.append(context)
        page = context.new_page()
        requests: list[str] = []
        page.on("request", lambda request: requests.append(request.url))
        page.goto(client.url + "/")
        expect(page.locator("#image-select option")).to_have_count(4)
        return SimpleNamespace(studio=studio, client=client, page=page, requests=requests)

    yield open_
    for context in contexts:
        context.close()
