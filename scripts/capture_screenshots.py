"""Capture screenshots of every major section of the live app."""
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Frame

APP_URL = "https://ipthreatscope.streamlit.app/"
OUT = Path("assets")
OUT.mkdir(exist_ok=True)


def wait(page: Page, secs: float = 3.0):
    page.wait_for_timeout(int(secs * 1000))


def shot(page: Page, name: str):
    path = str(OUT / f"{name}.png")
    page.screenshot(path=path, full_page=False)
    print(f"  saved {path}")


def get_frame(page: Page) -> Frame:
    """Return the Streamlit app frame (the ~/+/ iframe)."""
    for frame in page.frames:
        if "~/+/" in frame.url:
            return frame
    # fallback: frame with tabs
    for frame in page.frames:
        tabs = frame.locator("[data-baseweb='tab']").all_text_contents()
        if tabs:
            return frame
    return page.main_frame


def click_tab(frame: Frame, label: str, timeout: int = 20000):
    """Click a Streamlit tab by partial text (icon name prefix is ignored via :has-text)."""
    frame.locator(f"[data-baseweb='tab']").filter(has_text=label).first.click(timeout=timeout)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1400, "height": 860})
    page = ctx.new_page()

    print("Loading app...")
    page.goto(APP_URL, wait_until="networkidle", timeout=60000)
    wait(page, 8)

    # Debug: list frames and their tabs
    for f in page.frames:
        tabs = f.locator("[data-baseweb='tab']").all_text_contents()
        if tabs:
            print(f"Frame {f.url[:60]}: tabs={tabs[:6]}")

    # 1 ── Hero landing
    shot(page, "01_hero")

    frame = get_frame(page)
    print(f"Using frame: {frame.url[:80]}")

    # 2 ── Single IP Preview
    print("Single IP Preview...")
    click_tab(frame, "Single IP Preview")
    wait(page, 2)
    frame.locator("input").first.fill("185.220.101.47")
    frame.locator("button:has-text('Preview')").first.click()
    wait(page, 5)
    page.evaluate("window.scrollTo(0, 0)")
    shot(page, "02_demo_ip_input")
    page.evaluate("window.scrollBy(0, 420)")
    wait(page, 1.5)
    shot(page, "03_demo_ip_gauge")

    # 3 ── Sample Data → Blacklist
    print("Sample Data - Blacklist...")
    click_tab(frame, "Sample Data")
    wait(page, 3)
    page.evaluate("window.scrollTo(0, 0)")
    shot(page, "04_demo_sample_blacklist")

    # 4 ── Sample Data → IP Analysis
    print("Sample Data - IP Analysis...")
    click_tab(frame, "IP Analysis Example")
    wait(page, 3)
    page.evaluate("window.scrollTo(0, 0)")
    shot(page, "05_demo_sample_ip")
    page.evaluate("window.scrollBy(0, 500)")
    wait(page, 1.5)
    shot(page, "06_demo_sample_ip_detail")

    # 5 ── Upload JSON tab
    print("Upload JSON tab...")
    click_tab(frame, "Upload JSON")
    wait(page, 2)
    page.evaluate("window.scrollTo(0, 0)")
    shot(page, "07_demo_upload")

    # 6 ── Connect API Key
    print("Connect tab...")
    click_tab(frame, "Connect API Key")
    wait(page, 2)
    page.evaluate("window.scrollTo(0, 0)")
    shot(page, "08_connect")

    ctx.close()
    browser.close()

print("\nAll screenshots done.")
