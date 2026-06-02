from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 860})
    page.goto("https://ipthreatscope.streamlit.app/", wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(9000)

    for sel in ['[data-baseweb="tab"]', 'li[role="tab"]', 'div[role="tab"]', '[data-testid*="tab"]']:
        els = page.locator(sel).all_text_contents()
        if els:
            print(f"{sel}: {els[:8]}")

    btns = page.locator("button").all_text_contents()
    print("buttons:", [b.strip() for b in btns if b.strip()][:20])

    # Dump page title and any visible headings
    h = page.locator("h1, h2, h3, h4").all_text_contents()
    print("headings:", h[:10])

    page.screenshot(path="assets/debug.png")
    browser.close()
