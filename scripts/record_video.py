"""Record a full walkthrough video of ThreatScope Analytics."""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Frame

APP_URL  = "https://ipthreatscope.streamlit.app/"
API_KEY  = os.environ["ABUSEIPDB_KEY"]
OUT      = Path("assets")
VID_DIR  = OUT / "video_tmp"
VID_DIR.mkdir(parents=True, exist_ok=True)
OUT.mkdir(exist_ok=True)


def wait(page: Page, secs: float):
    page.wait_for_timeout(int(secs * 1000))


def shot(page: Page, name: str):
    path = str(OUT / f"{name}.png")
    page.screenshot(path=path, full_page=False)
    print(f"  screenshot: {path}")


def get_frame(page: Page) -> Frame:
    for frame in page.frames:
        if "~/+/" in frame.url:
            return frame
    for frame in page.frames:
        if frame.locator("[data-baseweb='tab']").count() > 0:
            return frame
    return page.main_frame


def click_tab(frame: Frame, label: str):
    frame.locator("[data-baseweb='tab']").filter(has_text=label).first.click(timeout=20000)


def slow_type(locator, text: str, delay_ms: int = 60):
    """Type text character by character for a natural video effect."""
    locator.click()
    for ch in text:
        locator.press(ch)
        time.sleep(delay_ms / 1000)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, slow_mo=80)
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 720},
        record_video_dir=str(VID_DIR),
        record_video_size={"width": 1280, "height": 720},
    )
    page = ctx.new_page()

    # ── 1. Landing / hero ────────────────────────────────────────────────────
    print("Loading app...")
    page.goto(APP_URL, wait_until="networkidle", timeout=60000)
    wait(page, 6)
    shot(page, "09_live_hero")

    frame = get_frame(page)
    print(f"Frame: {frame.url[:80]}")

    # ── 2. Demo → Single IP Preview ──────────────────────────────────────────
    print("Demo: Single IP Preview...")
    click_tab(frame, "Single IP Preview")
    wait(page, 2)
    ip_input = frame.locator("input").first
    slow_type(ip_input, "185.220.101.47")
    wait(page, 1)
    frame.locator("button:has-text('Preview')").first.click()
    wait(page, 6)
    page.evaluate("window.scrollBy(0, 380)")
    wait(page, 2.5)
    page.evaluate("window.scrollBy(0, 320)")
    wait(page, 2)
    page.evaluate("window.scrollTo(0, 0)")
    wait(page, 1.5)

    # ── 3. Demo → Sample Data ────────────────────────────────────────────────
    print("Demo: Sample Data...")
    click_tab(frame, "Sample Data")
    wait(page, 3)
    page.evaluate("window.scrollBy(0, 400)")
    wait(page, 2)
    page.evaluate("window.scrollTo(0, 0)")
    wait(page, 1)

    click_tab(frame, "IP Analysis Example")
    wait(page, 3)
    page.evaluate("window.scrollBy(0, 500)")
    wait(page, 2.5)
    page.evaluate("window.scrollTo(0, 0)")
    wait(page, 1.5)

    # ── 4. Connect API Key ───────────────────────────────────────────────────
    print("Connecting API key...")
    click_tab(frame, "Connect API Key")
    wait(page, 2)
    key_input = frame.locator("input[type='password']").first
    key_input.click()
    key_input.type(API_KEY, delay=18)   # type() fires React onChange; delay gives natural look
    wait(page, 1.5)
    frame.locator("button:has-text('Connect')").first.click()
    wait(page, 10)   # Streamlit reruns the full app after session_state change

    # ── 5. Live Blacklist Feed ────────────────────────────────────────────────
    print("Live Blacklist Feed...")
    wait(page, 4)   # extra wait for Streamlit rerun after connect
    frame = get_frame(page)
    tabs = frame.locator("[data-baseweb='tab']").all_text_contents()
    print(f"  Post-auth tabs: {tabs}")
    # Tab label includes icon prefix, e.g. "list Global Blacklist Feed"
    click_tab(frame, "Blacklist")
    wait(page, 8)
    page.evaluate("window.scrollTo(0, 0)")
    shot(page, "10_live_blacklist_top")
    page.evaluate("window.scrollBy(0, 450)")
    wait(page, 2)
    shot(page, "11_live_blacklist_table")
    page.evaluate("window.scrollBy(0, 400)")
    wait(page, 2)
    shot(page, "12_live_blacklist_chart")
    page.evaluate("window.scrollTo(0, 0)")
    wait(page, 2)

    # ── 6. Live IP Analysis ───────────────────────────────────────────────────
    print("Live IP Analysis...")
    click_tab(frame, "IP Analysis")   # matches "manage_search IP Analysis"
    wait(page, 2)
    ip_input2 = frame.locator("input").first
    slow_type(ip_input2, "8.8.8.8")
    wait(page, 1)
    frame.locator("button:has-text('Analyze IP')").first.click()
    wait(page, 7)
    page.evaluate("window.scrollTo(0, 0)")
    shot(page, "13_live_ip_top")
    page.evaluate("window.scrollBy(0, 450)")
    wait(page, 2)
    shot(page, "14_live_ip_gauge")
    page.evaluate("window.scrollBy(0, 400)")
    wait(page, 2)
    shot(page, "15_live_ip_detail")
    page.evaluate("window.scrollTo(0, 0)")
    wait(page, 2)

    print("Closing — saving video...")
    ctx.close()
    browser.close()

# Find and rename the recorded video
videos = list(VID_DIR.glob("*.webm"))
if videos:
    dest = OUT / "walkthrough.webm"
    videos[0].rename(dest)
    print(f"\nVideo saved: {dest}  ({dest.stat().st_size // 1024} KB)")
else:
    print("No video file found.")
