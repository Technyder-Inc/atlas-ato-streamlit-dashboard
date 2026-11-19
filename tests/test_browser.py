"""Pixel-level regression against the actual supplied index.html design.

Run with: pytest -m browser tests/test_browser.py
This uses the immutable seed CSV fixtures, so client updates won't break visual tests.
"""

from __future__ import annotations

import io
import shutil
from pathlib import Path

import pytest

from atlas.data import build_dashboard
from atlas.renderer import render_dashboard

playwright = pytest.importorskip("playwright.sync_api")
Image = pytest.importorskip("PIL.Image")
ImageChops = pytest.importorskip("PIL.ImageChops")

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "tests" / "fixtures" / "data"
ORIGINAL = (ROOT / "site" / "reference.html").read_text(encoding="utf-8")
GENERATED = render_dashboard(build_dashboard(SEED, ROOT))


def _image(page, html: str, tab: str, guide: str | None = None):
    page.set_content(html)
    if tab != "overview":
        page.locator(f'button[data-tab="{tab}"]').click()
    if guide:
        page.locator(f'button[data-guide="{guide}"]').click()
    return Image.open(io.BytesIO(page.screenshot(full_page=True))).convert("RGB")


@pytest.mark.browser
@pytest.mark.parametrize("tab", ["overview", "assessments", "controls", "docs", "poam", "github", "linux"])
def test_every_tab_pixel_identical_to_original_sample(tab: str) -> None:
    with playwright.sync_playwright() as driver:
        options = {"headless": True, "args": ["--no-sandbox"]}
        chromium_path = shutil.which("chromium") or shutil.which("chromium-browser")
        if chromium_path:
            options["executable_path"] = chromium_path
        browser = driver.chromium.launch(**options)
        first = browser.new_page(viewport={"width": 1300, "height": 900}, device_scale_factor=1)
        second = browser.new_page(viewport={"width": 1300, "height": 900}, device_scale_factor=1)
        try:
            ref = _image(first, ORIGINAL, tab)
            ours = _image(second, GENERATED, tab)
            assert ref.size == ours.size, f"{tab} height or width changed"
            assert ImageChops.difference(ref, ours).getbbox() is None, f"{tab} differs from index.html"
        finally:
            browser.close()


@pytest.mark.browser
def test_linux_au12_selection_pixel_identical_to_original_sample() -> None:
    with playwright.sync_playwright() as driver:
        options = {"headless": True, "args": ["--no-sandbox"]}
        chromium_path = shutil.which("chromium") or shutil.which("chromium-browser")
        if chromium_path:
            options["executable_path"] = chromium_path
        browser = driver.chromium.launch(**options)
        first = browser.new_page(viewport={"width": 1300, "height": 900}, device_scale_factor=1)
        second = browser.new_page(viewport={"width": 1300, "height": 900}, device_scale_factor=1)
        try:
            ref = _image(first, ORIGINAL, "linux", "AU-12")
            ours = _image(second, GENERATED, "linux", "AU-12")
            assert ImageChops.difference(ref, ours).getbbox() is None
            assert second.locator("#content pre").inner_text() == (
                "sudo systemctl status auditd\nsudo auditctl -l"
            )
        finally:
            browser.close()
