"""Capture live API screenshots from the local preview server."""
import os, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright, Frame

LOCAL   = "http://localhost:8503"
OUT     = Path("assets")
OUT.mkdir(exist_ok=True)
API_KEY = os.environ["ABUSEIPDB_KEY"]


def wait(page, secs):
    page.wait_for_timeout(int(secs * 1000))


def shot(page, name):
    p = str(OUT / f"{name}.png")
    page.screenshot(path=p, full_page=False)
    print(f"  {p}")


def get_frame(page):
    for f in page.frames:
        if "~/+/" in f.url:
            return f
    for f in page.frames:
        if f.locator("[data-baseweb='tab']").count() > 0:
            return f
    return page.main_frame


def click_tab(frame: Frame, label: str):
    frame.locator("[data-baseweb='tab']").filter(has_text=label).first.click(timeout=20000)


env = {**os.environ, "ABUSEIPDB_KEY": API_KEY}
proc = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "scripts/live_preview.py",
     "--server.port", "8503", "--server.headless", "true",
     "--browser.gatherUsageStats", "false"],
    env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
print("Starting local preview server...")
time.sleep(10)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=50)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(LOCAL, wait_until="networkidle", timeout=30000)
        wait(page, 6)

        frame = get_frame(page)
        tabs = frame.locator("[data-baseweb='tab']").all_text_contents()
        print(f"Tabs: {tabs}")

        # ── Blacklist Feed ────────────────────────────────────────────────────
        print("Blacklist Feed...")
        click_tab(frame, "Blacklist")
        wait(page, 12)   # live API call
        page.evaluate("window.scrollTo(0, 0)")
        shot(page, "10_live_blacklist_top")
        page.evaluate("window.scrollBy(0, 420)")
        wait(page, 2)
        shot(page, "11_live_blacklist_table")
        page.evaluate("window.scrollBy(0, 420)")
        wait(page, 2)
        shot(page, "12_live_blacklist_chart")

        # ── IP Analysis: 8.8.8.8 ─────────────────────────────────────────────
        print("IP Analysis (8.8.8.8)...")
        click_tab(frame, "IP Analysis")
        wait(page, 2)
        page.evaluate("window.scrollTo(0, 0)")
        inp = frame.locator("input").first
        inp.click()
        inp.type("8.8.8.8", delay=80)
        wait(page, 1)
        frame.locator("button:has-text('Analyze IP')").first.click()
        wait(page, 9)
        page.evaluate("window.scrollTo(0, 0)")
        shot(page, "13_live_ip_top")
        page.evaluate("window.scrollBy(0, 430)")
        wait(page, 2)
        shot(page, "14_live_ip_gauge")
        page.evaluate("window.scrollBy(0, 430)")
        wait(page, 2)
        shot(page, "15_live_ip_detail")

        browser.close()
        print("Done.")
finally:
    proc.terminate()
    print("Server stopped.")
