"""Record Part 2 — live IP analysis via local preview server with scrolling."""
import os, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright, Frame

API_KEY = os.environ["ABUSEIPDB_KEY"]
VID_DIR = Path("assets/video_tmp")
VID_DIR.mkdir(parents=True, exist_ok=True)
LOCAL   = "http://localhost:8504"
IP      = "1.1.1.1"   # Cloudflare DNS — low score, clean interesting result


def ms(secs): return int(secs * 1000)

def scroll(page, dy, pause=0.8):
    page.evaluate(f"window.scrollBy(0, {dy})")
    page.wait_for_timeout(ms(pause))

def get_frame(page):
    for f in page.frames:
        if "localhost" in f.url and "~/+/" in f.url: return f
    for f in page.frames:
        if f.locator("[data-baseweb='tab']").count(): return f
    return page.main_frame

def click_tab(frame: Frame, label: str):
    frame.locator("[data-baseweb='tab']").filter(has_text=label).first.click(timeout=20000)


env = {**os.environ, "ABUSEIPDB_KEY": API_KEY}
proc = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "scripts/live_preview.py",
     "--server.port", "8504", "--server.headless", "true",
     "--browser.gatherUsageStats", "false"],
    env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
print("Starting local server...")
time.sleep(10)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=40)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(VID_DIR / "p2"),
            record_video_size={"width": 1280, "height": 720},
        )
        (VID_DIR / "p2").mkdir(exist_ok=True)
        page = ctx.new_page()

        print("Loading local app...")
        page.goto(LOCAL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(ms(5))

        frame = get_frame(page)

        # ── IP Analysis tab ───────────────────────────────────────────────────
        print("Navigating to IP Analysis...")
        click_tab(frame, "IP Analysis")
        page.wait_for_timeout(ms(2))
        page.evaluate("window.scrollTo(0, 0)")

        # Enter IP and analyze
        inp = frame.locator("input").first
        inp.click()
        inp.type(IP, delay=80)
        page.wait_for_timeout(ms(1.2))
        frame.locator("button:has-text('Analyze IP')").first.click()
        page.wait_for_timeout(ms(9))   # live API call

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(ms(1.5))

        # Scroll through results progressively
        scroll(page, 300, 1.8)   # reveal Analysis header + top of gauge
        scroll(page, 280, 1.8)   # reveal gauge fully + IP summary
        scroll(page, 260, 1.8)   # reveal country / usage type / network
        scroll(page, 260, 1.5)   # reveal timeline
        scroll(page, 240, 1.5)   # reveal raw intel expander
        page.wait_for_timeout(ms(2))

        ctx.close()
        browser.close()
finally:
    proc.terminate()
    print("Server stopped.")

vids = list((VID_DIR / "p2").glob("*.webm"))
if vids:
    dest = VID_DIR / "part2.webm"
    vids[0].rename(dest)
    print(f"Part 2 saved: {dest}  ({dest.stat().st_size//1024} KB)")
else:
    print("ERROR: no video found")
