import asyncio
import os
import re
import sys
from datetime import datetime, timedelta
from urllib.parse import quote

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from playwright.async_api import async_playwright

# ── Load .env ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# ========================= CONFIG =========================
LINKEDIN_EMAIL    = os.getenv("LINKEDIN_EMAIL", "").strip()
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "").strip()

SERVICE_ACCOUNT_FILE = r"F:\data Engineer Projects\Scrap_auto_mailer_json\firm-capsule-483603-e6-7d50e96d654c.json"
SPREADSHEET_ID = "1tRotBzXCFZfH6DsUAXyvnbC8wT79VYoxiPZOHzVk-XM"
SHEET_NAME     = "Sheet1"

SEARCH_TIMEOUT      = 300    # 5 minutes per search query
MIN_VALID_PAGE_TEXT = 1000
SCROLL_PAUSE        = 2      # seconds between scrolls
SCROLL_AMOUNT       = 800    # pixels per scroll

SEARCH_QUERIES = [
    "data analyst hiring",
    "Sr data analyst hiring",
]

SESSION_DIR = os.path.join(BASE_DIR, "linkedin_browser_session")
# ==========================================================


# ========================= DATE ===========================
now = datetime.now()
if now.hour >= 17:
    DATE_TO_USE = (now + timedelta(days=1)).strftime("%m/%d/%Y")
    print(f"After 5 PM  → writing TOMORROW : {DATE_TO_USE}")
else:
    DATE_TO_USE = now.strftime("%m/%d/%Y")
    print(f"Before 5 PM → writing TODAY    : {DATE_TO_USE}")
# ==========================================================


EMAIL_REGEX     = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
FORM_LINK_REGEX = r"https?://docs\.google\.com/forms/[^\s\)\]\'\"<>]+"


def clean_url(url):
    return re.sub(r"[)\].,;\'\"]+$", "", url)


def get_search_url(query):
    encoded = quote(query.strip(), safe="")
    return (
        "https://www.linkedin.com/search/results/content/"
        f"?keywords={encoded}"
        "&datePosted=past-24h"
        "&sortBy=date_posted"
    )


# ====================== GOOGLE SHEETS =====================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

print("Connecting to Google Sheets...")
try:
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc    = gspread.authorize(creds)
    sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    print("Connected to Google Sheet\n")
except Exception as e:
    print(f"Sheet connection failed: {e}")
    sys.exit(1)


def get_existing_emails():
    try:
        all_values = sheet.get_all_values()
        existing   = set()
        for row in all_values[1:]:
            if len(row) > 1 and row[1].strip():
                existing.add(row[1].strip().lower())
        print(f"Loaded {len(existing)} existing emails from sheet")
        return existing
    except Exception as e:
        print(f"Could not read sheet: {e}")
        return set()


def append_to_sheet(new_records):
    if not new_records:
        return
    current_emails = get_existing_emails()
    truly_new = []
    for record in new_records:
        email = record["Email"].strip().lower()
        if email:
            if email not in current_emails:
                truly_new.append(record)
                current_emails.add(email)
        else:
            truly_new.append(record)
    if not truly_new:
        print("  Nothing new to write.")
        return
    rows = [[r["Date"], r["Email"], r.get("Apply Link", "")] for r in truly_new]
    try:
        sheet.append_rows(rows, value_input_option="USER_ENTERED")
        print(f"  ✅ Written {len(rows)} rows to Google Sheet")
    except Exception as e:
        print(f"  ❌ Sheet write error: {e}")


# ========================= STATE ==========================
seen_emails = set()
seen_links  = set()
all_records = []
# ==========================================================


def extract_and_save(text):
    global seen_emails, seen_links, all_records

    found_emails = []
    for match in re.findall(EMAIL_REGEX, text):
        email = match.lower().strip()
        if (
            not email.endswith("@gmail.com")
            and "linkedin.com" not in email
            and "sentry.io"    not in email
            and "example.com"  not in email
            and len(email) > 6
            and email not in seen_emails
        ):
            found_emails.append(email)
    found_emails = list(dict.fromkeys(found_emails))

    found_links = []
    for link in re.findall(FORM_LINK_REGEX, text):
        cleaned = clean_url(link.strip())
        if cleaned not in seen_links:
            found_links.append(cleaned)
    found_links = list(dict.fromkeys(found_links))

    if found_emails:
        print(f"  📧 New emails : {found_emails}")
    if found_links:
        print(f"  🔗 New links  : {found_links}")

    if not found_emails and not found_links:
        return 0

    new_records = []
    paired = min(len(found_emails), len(found_links))

    for i in range(paired):
        new_records.append({"Date": DATE_TO_USE, "Email": found_emails[i], "Apply Link": found_links[i]})
        seen_emails.add(found_emails[i])
        seen_links.add(found_links[i])

    for email in found_emails[paired:]:
        new_records.append({"Date": DATE_TO_USE, "Email": email, "Apply Link": ""})
        seen_emails.add(email)

    for link in found_links[paired:]:
        new_records.append({"Date": DATE_TO_USE, "Email": "", "Apply Link": link})
        seen_links.add(link)

    append_to_sheet(new_records)
    all_records.extend(new_records)
    return len(new_records)


# ===================== EXPAND POSTS =======================
async def expand_all_posts(page):
    """
    FIX 2: Click all '...more' / 'see more' buttons to expand
    truncated posts so hidden emails become visible in page text.
    """
    # LinkedIn uses these selectors for the expand button
    more_selectors = [
        "button.feed-shared-inline-show-more-text__see-more-less-toggle",
        "button.see-more",
        "button[aria-label='see more']",
        "span.feed-shared-text-view__text--toggle",
        ".feed-shared-update-v2__description button",
        "button:has-text('more')",
    ]

    clicked = 0
    for selector in more_selectors:
        try:
            buttons = await page.locator(selector).all()
            for btn in buttons:
                try:
                    if await btn.is_visible():
                        await btn.click()
                        clicked += 1
                        await asyncio.sleep(0.2)
                except Exception:
                    pass
        except Exception:
            pass

    if clicked > 0:
        print(f"  🔓 Expanded {clicked} post(s) — hidden emails now visible")
        await asyncio.sleep(0.5)   # let expanded content render


# ===================== SCROLL =============================
async def scroll_feed(page):
    """
    FIX 1: Scroll LinkedIn's internal feed container, not window.
    LinkedIn renders results inside a scrollable div, not the page body.
    Falls back to window scroll if container not found.
    """
    # Try scrolling LinkedIn's search results container first
    scrolled = await page.evaluate("""
        () => {
            // LinkedIn search results container selectors (try each)
            const selectors = [
                '.search-results-container',
                '.scaffold-finite-scroll__content',
                '.search-results__list',
                'div[data-finite-scroll-hotspot-top]',
                '.core-rail',
            ];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.scrollHeight > el.clientHeight) {
                    el.scrollBy(0, 800);
                    return 'container:' + sel;
                }
            }
            // Fallback: scroll window
            window.scrollBy(0, 800);
            return 'window';
        }
    """)
    return scrolled


# ===================== LOGIN ==============================
async def login(page):
    print("\n" + "="*60)
    print("  LINKEDIN LOGIN")
    print("="*60)

    if not LINKEDIN_EMAIL:
        print(f"❌ LINKEDIN_EMAIL empty — check {BASE_DIR}\\.env")
    if not LINKEDIN_PASSWORD:
        print(f"❌ LINKEDIN_PASSWORD empty — check {BASE_DIR}\\.env")

    await page.goto("https://www.linkedin.com/login", timeout=30000, wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)

    # Pre-fill email
    email_field = None
    for sel in ["input#username", "input[name='session_key']", "input[type='email']"]:
        loc = page.locator(sel).first
        try:
            if await loc.count() > 0 and await loc.is_visible():
                email_field = loc
                break
        except Exception:
            pass

    if email_field:
        await email_field.fill(LINKEDIN_EMAIL)
        print(f"Email pre-filled : {LINKEDIN_EMAIL}")
        await page.wait_for_timeout(400)
    else:
        print("Could not pre-fill email — type manually in browser")

    # Pre-fill password
    pass_field = None
    for sel in ["input#password", "input[name='session_password']", "input[type='password']"]:
        loc = page.locator(sel).first
        try:
            if await loc.count() > 0 and await loc.is_visible():
                pass_field = loc
                break
        except Exception:
            pass

    if pass_field:
        await pass_field.fill(LINKEDIN_PASSWORD)
        print("Password pre-filled")
        await page.wait_for_timeout(400)
    else:
        print("Could not pre-fill password — type manually in browser")

    print("\n" + "="*60)
    print("  ACTION NEEDED")
    print("  1. Click 'Sign in' in the browser")
    print("  2. Solve CAPTCHA/OTP if LinkedIn asks")
    print("  3. Wait until you see the LinkedIn HOME FEED")
    print("  4. Come back here and press ENTER")
    print("="*60)
    input("\nPress ENTER after you see the LinkedIn feed ▶ ")

    await page.wait_for_timeout(2000)
    url = page.url.lower()
    if any(x in url for x in ["login", "checkpoint", "challenge", "authwall"]):
        print("Still on login page — complete verification then press ENTER...")
        input("Press ENTER once you see the feed ▶ ")
        await page.wait_for_timeout(2000)

    print("✅ Login confirmed — session saved to disk")
    print("✅ Future runs will skip login completely\n")


async def ensure_logged_in(page):
    print("Checking existing LinkedIn session...")
    try:
        await page.goto("https://www.linkedin.com/feed/", timeout=30000, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"Could not reach feed: {e}")

    url = page.url.lower()
    print(f"After feed check: {page.url}")

    if any(x in url for x in ["login", "checkpoint", "challenge", "authwall"]):
        print("Session NOT authenticated — starting login...")
        await login(page)
    else:
        print("✅ Already logged in — session restored\n")


# ===================== SEARCH =============================
async def run_search(page, query):
    url = get_search_url(query)

    print("\n" + "="*70)
    print(f"SEARCH  : {query}")
    print(f"FILTER  : Posts + Past 24 hours")
    print(f"TIMEOUT : 5 minutes")
    print("="*70)

    await page.goto(url, timeout=30000, wait_until="domcontentloaded")
    await page.wait_for_timeout(5000)

    # Safety: did LinkedIn redirect to login?
    current_url = page.url.lower()
    if any(x in current_url for x in ["/checkpoint/", "login-challenge", "/challenge/", "/login"]):
        raise RuntimeError(f"LinkedIn redirected to login instead of results: {page.url}")

    try:
        initial_text = await page.locator("body").inner_text(timeout=10000)
    except Exception as e:
        raise RuntimeError(f"Could not read page: {e}")

    if len(initial_text) < MIN_VALID_PAGE_TEXT:
        raise RuntimeError(f"Page too short ({len(initial_text)} chars) — not authenticated?")

    print(f"✅ Results loaded ({len(initial_text)} chars)\n")

    search_start  = asyncio.get_running_loop().time()
    scroll_count  = 0
    last_char_count = 0

    while True:
        elapsed = asyncio.get_running_loop().time() - search_start
        if elapsed >= SEARCH_TIMEOUT:
            print(f"\n⏱ 5 minutes completed for '{query}'.")
            break

        scroll_count += 1

        # ── FIX 2: Expand all truncated posts before reading ──
        await expand_all_posts(page)

        # ── Read full page text ──
        try:
            text = await page.locator("body").inner_text(timeout=10000)
        except Exception as e:
            print(f"Could not read page: {e}")
            text = ""

        char_count = len(text)
        char_delta = char_count - last_char_count
        last_char_count = char_count

        print(f"\n--- Scroll #{scroll_count} | {char_count} chars (+{char_delta} new) ---")
        count = extract_and_save(text)
        print(f"New this scroll: {count} | Session total: {len(all_records)}")

        elapsed = asyncio.get_running_loop().time() - search_start
        remaining = int(SEARCH_TIMEOUT - elapsed)
        print(f"Time remaining: {remaining}s")

        if elapsed >= SEARCH_TIMEOUT:
            break

        # ── FIX 1: Scroll the correct container ──
        scroll_target = await scroll_feed(page)
        print(f"Scrolled via: {scroll_target}")
        await asyncio.sleep(SCROLL_PAUSE)

    print(f"\nFinished: {query}")


# ========================= MAIN ===========================
async def main():
    print("\n" + "="*70)
    print("       LINKEDIN EMAIL SCRAPER")
    print("="*70)
    print(f"Date         : {DATE_TO_USE}")
    print(f"Session dir  : {SESSION_DIR}")
    print(f"Queries      : {SEARCH_QUERIES}")
    print(f"Per search   : 5 minutes")
    print(f"Email loaded : {LINKEDIN_EMAIL if LINKEDIN_EMAIL else '❌ EMPTY'}\n")

    global seen_emails
    seen_emails = get_existing_emails()

    async with async_playwright() as p:
        context = None
        try:
            context = await p.chromium.launch_persistent_context(
                SESSION_DIR,
                headless=False,
                viewport={"width": 1280, "height": 800},
                args=[
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-background-timer-throttling",
                ]
            )

            page = context.pages[0] if context.pages else await context.new_page()

            await page.goto("https://www.linkedin.com/", timeout=30000, wait_until="domcontentloaded")
            await ensure_logged_in(page)

            for query in SEARCH_QUERIES:
                await run_search(page, query)

            print("\n" + "="*70)
            print("COMPLETE")
            print("="*70)
            print(f"Total records   : {len(all_records)}")
            print(f"Unique emails   : {len(seen_emails)}")
            print(f"Date written    : {DATE_TO_USE}")
            print("="*70)

        except KeyboardInterrupt:
            print("\nStopped by user.")
        except Exception as e:
            print(f"\nERROR: {e}")
        finally:
            if context:
                await context.close()


if __name__ == "__main__":
    asyncio.run(main())