"""Record Part 1 — cloud app demo section with proper scrolling."""
from pathlib import Path
from playwright.sync_api import sync_playwright, Frame

APP_URL = "https://ipthreatscope.streamlit.app/"
VID_DIR = Path("assets/video_tmp")
VID_DIR.mkdir(parents=True, exist_ok=True)

IP = "185.220.101.47"


def ms(secs): return int(secs * 1000)

def scroll(page, dy, pause=0.8):
    page.evaluate(f"window.scrollBy(0, {dy})")
    page.wait_for_timeout(ms(pause))

def get_frame(page):
    for f in page.frames:
        if "~/+/" in f.url: return f
    for f in page.frames:
        if f.locator("[data-baseweb='tab']").count(): return f
    return page.main_frame

def click_tab(frame: Frame, label: str):
    frame.locator("[data-baseweb='tab']").filter(has_text=label).first.click(timeout=20000)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, slow_mo=40)
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 720},
        record_video_dir=str(VID_DIR / "p1"),
        record_video_size={"width": 1280, "height": 720},
    )
    (VID_DIR / "p1").mkdir(exist_ok=True)
    page = ctx.new_page()

    # ── 1. Hero landing ───────────────────────────────────────────────────────
    print("Loading app...")
    page.goto(APP_URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(ms(7))
    scroll(page, 0)   # ensure at top

    # ── 2. Demo → Single IP Preview — type + Preview ──────────────────────────
    print("Demo: entering IP...")
    frame = get_frame(page)
    click_tab(frame, "Single IP Preview")
    page.wait_for_timeout(ms(2))
    scroll(page, 280, 0.5)    # scroll so input is visible mid-screen

    inp = frame.locator("input").first
    inp.click()
    inp.type(IP, delay=70)
    page.wait_for_timeout(ms(1.2))
    frame.locator("button:has-text('Preview')").first.click()
    page.wait_for_timeout(ms(6))   # wait for sample render

    # Scroll down in steps to reveal each section
    page.wait_for_timeout(ms(0.5))
    scroll(page, 320, 1.5)   # reveal gauge
    scroll(page, 300, 1.5)   # reveal country / usage type
    scroll(page, 280, 1.5)   # reveal timeline
    scroll(page, 260, 1.2)   # reveal raw intel expander
    page.wait_for_timeout(ms(1.5))

    # Scroll back to top before next tab
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(ms(1.5))

    # ── 3. Sample Data → Blacklist ────────────────────────────────────────────
    print("Demo: sample blacklist...")
    click_tab(frame, "Sample Data")
    page.wait_for_timeout(ms(3))
    scroll(page, 350, 1.5)   # reveal table rows
    scroll(page, 350, 1.5)   # reveal score distribution chart
    page.wait_for_timeout(ms(1.5))
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(ms(1))

    # ── 4. Connect tab ────────────────────────────────────────────────────────
    print("Demo: connect tab...")
    click_tab(frame, "Connect API Key")
    page.wait_for_timeout(ms(2.5))

    ctx.close()
    browser.close()

# Rename output
vids = list((VID_DIR / "p1").glob("*.webm"))
if vids:
    dest = VID_DIR / "part1.webm"
    vids[0].rename(dest)
    print(f"Part 1 saved: {dest}  ({dest.stat().st_size//1024} KB)")
else:
    print("ERROR: no video found")
