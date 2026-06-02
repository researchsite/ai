"""Record live API sections against local Streamlit server."""
import os, subprocess, time, sys
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Frame

API_KEY  = os.environ["ABUSEIPDB_KEY"]
LOCAL    = "http://localhost:8502"
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
        if "localhost" in frame.url and "~/+/" in frame.url:
            return frame
    for frame in page.frames:
        if frame.locator("[data-baseweb='tab']").count() > 0:
            return frame
    return page.main_frame


def click_tab(frame: Frame, label: str):
    frame.locator("[data-baseweb='tab']").filter(has_text=label).first.click(timeout=20000)


# Start local Streamlit on port 8502
proc = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "app/main.py",
     "--server.port", "8502", "--server.headless", "true",
     "--browser.gatherUsageStats", "false"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
print("Waiting for local server...")
time.sleep(8)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=60)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(VID_DIR),
            record_video_size={"width": 1280, "height": 720},
        )
        page = ctx.new_page()

        print("Loading local app...")
        page.goto(LOCAL, wait_until="networkidle", timeout=30000)
        wait(page, 5)

        frame = get_frame(page)
        tabs = frame.locator("[data-baseweb='tab']").all_text_contents()
        print(f"Tabs: {tabs}")

        # ── Connect API key ───────────────────────────────────────────────────
        print("Connecting API key...")
        click_tab(frame, "Connect API Key")
        wait(page, 2)
        key_input = frame.locator("input[type='password']").first
        key_input.click()
        key_input.type(API_KEY, delay=15)
        wait(page, 1.5)
        frame.locator("button:has-text('Connect')").first.click()
        wait(page, 8)

        frame = get_frame(page)
        tabs = frame.locator("[data-baseweb='tab']").all_text_contents()
        print(f"Post-auth tabs: {tabs}")

        # ── Blacklist Feed ────────────────────────────────────────────────────
        print("Live Blacklist Feed...")
        click_tab(frame, "Blacklist")
        wait(page, 10)  # API call takes a few seconds
        page.evaluate("window.scrollTo(0, 0)")
        shot(page, "10_live_blacklist_top")
        page.evaluate("window.scrollBy(0, 430)")
        wait(page, 2)
        shot(page, "11_live_blacklist_table")
        page.evaluate("window.scrollBy(0, 380)")
        wait(page, 2)
        shot(page, "12_live_blacklist_chart")
        page.evaluate("window.scrollTo(0, 0)")
        wait(page, 2)

        # ── IP Analysis ───────────────────────────────────────────────────────
        print("Live IP Analysis...")
        click_tab(frame, "IP Analysis")
        wait(page, 2)
        page.evaluate("window.scrollTo(0, 0)")
        ip_input = frame.locator("input").first
        ip_input.click()
        ip_input.type("8.8.8.8", delay=80)
        wait(page, 1)
        frame.locator("button:has-text('Analyze IP')").first.click()
        wait(page, 8)
        page.evaluate("window.scrollTo(0, 0)")
        shot(page, "13_live_ip_top")
        page.evaluate("window.scrollBy(0, 430)")
        wait(page, 2)
        shot(page, "14_live_ip_gauge")
        page.evaluate("window.scrollBy(0, 380)")
        wait(page, 2)
        shot(page, "15_live_ip_detail")
        page.evaluate("window.scrollTo(0, 0)")
        wait(page, 2)

        print("Closing...")
        ctx.close()
        browser.close()

finally:
    proc.terminate()
    print("Local server stopped.")

# Save video
videos = list(VID_DIR.glob("*.webm"))
if videos:
    dest = OUT / "live_walkthrough.webm"
    videos[0].rename(dest)
    print(f"Video: {dest}  ({dest.stat().st_size // 1024} KB)")
