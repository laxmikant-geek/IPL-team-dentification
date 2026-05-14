"""
ESPN Cricinfo IPL Photo Downloader

Downloads images for a specific IPL team from ESPN Cricinfo photo galleries.
Uses Selenium (headless Chrome) to handle JavaScript-rendered content,
filtering by year (default: 2025).

Usage:
    python download_images.py --team RR
    python download_images.py --team RCB --year 2025
    python download_images.py --team SRH --out raw-images/SRH

Team codes:
    RR   Rajasthan Royals
    RCB  Royal Challengers Bengaluru
    SRH  Sunrisers Hyderabad
    CSK  Chennai Super Kings
    DC   Delhi Capitals
    IPL  IPL 2025 series gallery

Requirements:
    pip install selenium requests beautifulsoup4 webdriver-manager
"""

import re
import time
import hashlib
import argparse
from pathlib import Path
from urllib.parse import urlparse
from collections import Counter

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Team configuration
# ---------------------------------------------------------------------------
TEAM_CONFIG = {
    "RR": {
        "name": "Rajasthan Royals",
        "url": "https://www.espncricinfo.com/team/rajasthan-royals-335977/photo",
        "out_dir": "raw-images/RR",
    },
    "RCB": {
        "name": "Royal Challengers Bengaluru",
        "url": "https://www.espncricinfo.com/team/royal-challengers-bengaluru-335970/photo",
        "out_dir": "raw-images/RCB",
    },
    "SRH": {
        "name": "Sunrisers Hyderabad",
        "url": "https://www.espncricinfo.com/team/sunrisers-hyderabad-628333/photo",
        "out_dir": "raw-images/SRH",
    },
    "CSK": {
        "name": "Chennai Super Kings",
        "url": "https://www.espncricinfo.com/team/chennai-super-kings-335973/photo",
        "out_dir": "raw-images/csk",
    },
    "DC": {
        "name": "Delhi Capitals",
        "url": "https://www.espncricinfo.com/team/delhi-capitals-333979/photo",
        "out_dir": "raw-images/Delhi capitals",
    },
    "GT": {
        "name": "Gujarat Titans",
        "url": "https://www.espncricinfo.com/team/gujarat-titans-1298423/photo",
        "out_dir": "raw-images/GT",
    },
    "KKR": {
        "name": "Kolkata Knight Riders",
        "url": "https://www.espncricinfo.com/team/kolkata-knight-riders-381943/photo",
        "out_dir": "raw-images/KKR",
    },
    "LSG": {
        "name": "Lucknow Super Giants",
        "url": "https://www.espncricinfo.com/team/lucknow-super-giants-1298541/photo",
        "out_dir": "raw-images/LSG",
    },
    "MI": {
        "name": "Mumbai Indians",
        "url": "https://www.espncricinfo.com/team/mumbai-indians-335974/photo",
        "out_dir": "raw-images/MI",
    },
    "PBKS": {
        "name": "Punjab Kings",
        "url": "https://www.espncricinfo.com/team/punjab-kings-335976/photo",
        "out_dir": "raw-images/PBKS",
    },
    "IPL": {
        "name": "IPL 2025 Series Gallery",
        "url": "https://www.espncricinfo.com/series/ipl-2025-1449924/photo",
        "out_dir": "raw-images/downloaded",
    },
}

# CDN image URL pattern
IMAGE_URL_PATTERN = re.compile(
    r"https://img\d+\.hscicdn\.com/image/upload/[^\s\"'<>]+\.(?:jpg|jpeg|png|webp|avif)",
    re.IGNORECASE,
)

# Matches a 4-digit year (20xx) in surrounding text
YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")

# Request headers that mimic a real browser to avoid 403 responses
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.espncricinfo.com/",
}

# ---------------------------------------------------------------------------
# Selenium helpers
# ---------------------------------------------------------------------------

def _get_driver():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError as exc:
        raise SystemExit(
            "Selenium / webdriver-manager not installed.\n"
            "Run:  pip install selenium webdriver-manager beautifulsoup4"
        ) from exc

    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium import webdriver

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={HEADERS['User-Agent']}")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def _click_year_filter(driver, year: int) -> bool:
    """Try to find and click a year filter button/tab. Returns True if clicked."""
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException

    year_str = str(year)
    selectors = [
        f"//button[normalize-space()='{year_str}']",
        f"//a[normalize-space()='{year_str}']",
        f"//li[normalize-space()='{year_str}']",
        f"//span[normalize-space()='{year_str}']",
        f"//*[contains(@class,'year') and normalize-space()='{year_str}']",
        f"//*[contains(@data-year,'{year_str}')]",
    ]
    for xpath in selectors:
        try:
            el = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].click();", el)
            print(f"[*] Clicked year filter: {year_str}")
            time.sleep(2)
            return True
        except (NoSuchElementException, ElementClickInterceptedException):
            continue
    return False


def _scroll_to_bottom(driver, pause: float = 2.0):
    """Scroll the page until no new content loads."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def _fetch_page_source(url: str, year: int, scroll_pause: float = 2.0) -> str:
    """Open *url* in headless Chrome, try year filter, scroll, return HTML."""
    print("[*] Starting headless Chrome …")
    driver = _get_driver()
    try:
        driver.get(url)
        time.sleep(3)  # wait for initial JS render

        if not _click_year_filter(driver, year):
            print(f"[!] No year-filter button found; will filter by year in metadata.")

        print("[*] Scrolling to trigger lazy-load …")
        _scroll_to_bottom(driver, pause=scroll_pause)
        source = driver.page_source
    finally:
        driver.quit()
    return source


# ---------------------------------------------------------------------------
# Image extraction with year filtering
# ---------------------------------------------------------------------------

def _extract_images_with_year(html: str, year: int) -> list[str]:
    """
    Parse the page HTML to extract image URLs, filtering to those associated
    with *year*. Falls back to all images when no year metadata is found.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Build a map: filename → detected year, using two strategies.
    year_tagged: dict[str, int] = {}

    # Strategy 1 – scan embedded <script> JSON blobs for year context
    for script in soup.find_all("script"):
        text = script.string or ""
        if "hscicdn" not in text:
            continue
        for img_url in IMAGE_URL_PATTERN.findall(text):
            filename = urlparse(img_url).path.split("/")[-1]
            if filename in year_tagged:
                continue
            idx = text.find(img_url)
            window = text[max(0, idx - 300): idx + 300]
            matches = YEAR_PATTERN.findall(window)
            if matches:
                year_tagged[filename] = int(Counter(matches).most_common(1)[0][0])

    # Strategy 2 – walk up the DOM from each <img> to find a date element
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not IMAGE_URL_PATTERN.match(src):
            continue
        filename = urlparse(src).path.split("/")[-1]
        if filename in year_tagged:
            continue
        parent = img.parent
        for _ in range(6):
            if parent is None:
                break
            matches = YEAR_PATTERN.findall(parent.get_text(" ", strip=True))
            if matches:
                year_tagged[filename] = int(Counter(matches).most_common(1)[0][0])
                break
            parent = parent.parent

    # Collect all unique image URLs
    all_urls: dict[str, str] = {}   # filename → url
    for url in IMAGE_URL_PATTERN.findall(html):
        filename = urlparse(url).path.split("/")[-1]
        if filename not in all_urls:
            all_urls[filename] = url

    if not all_urls:
        return []

    # Apply year filter
    if year_tagged:
        filtered = [all_urls[fn] for fn in all_urls if year_tagged.get(fn) == year]
        if filtered:
            print(f"[+] Year filter applied: {len(filtered)}/{len(all_urls)} images match {year}.")
            return filtered
        available = sorted(set(year_tagged.values()))
        print(
            f"[!] Year filter for {year} matched 0 images "
            f"(detected years: {available}).\n"
            f"    Returning all {len(all_urls)} images instead."
        )
    else:
        print(
            f"[!] No year metadata found. "
            f"Returning all {len(all_urls)} images (manual filtering may be needed)."
        )

    return list(all_urls.values())


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------

def _safe_filename(url: str) -> str:
    path = urlparse(url).path
    name = path.split("/")[-1]
    return name if name else hashlib.md5(url.encode()).hexdigest()[:12] + ".jpg"


def _download_image(url: str, dest: Path, session: requests.Session) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        resp = session.get(url, timeout=30, stream=True)
        resp.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=8192):
                fh.write(chunk)
        return True
    except requests.RequestException as exc:
        print(f"  [!] Failed {url}: {exc}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    team_choices = list(TEAM_CONFIG.keys())

    parser = argparse.ArgumentParser(
        description="Download IPL team photos from ESPN Cricinfo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Teams:\n" + "\n".join(
            f"  {k:4s}  {v['name']}" for k, v in TEAM_CONFIG.items()
        ),
    )
    parser.add_argument(
        "--team",
        choices=team_choices,
        required=True,
        metavar="TEAM",
        help="Team code: " + ", ".join(team_choices),
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="Only download photos from this year (default: 2025)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Override output directory (default: per-team folder under raw-images/)",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Override gallery URL (default: team's configured URL)",
    )
    parser.add_argument(
        "--scroll-pause",
        type=float,
        default=2.0,
        help="Seconds to wait between scroll steps (default: 2.0)",
    )
    args = parser.parse_args()

    config = TEAM_CONFIG[args.team]
    gallery_url = args.url or config["url"]
    out_dir = Path(args.out) if args.out else Path(config["out_dir"])

    print(f"[+] Team   : {config['name']} ({args.team})")
    print(f"[+] Year   : {args.year}")
    print(f"[+] Source : {gallery_url}")
    print(f"[+] Output : {out_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)

    # Step 1 – fetch rendered HTML
    html = _fetch_page_source(gallery_url, args.year, scroll_pause=args.scroll_pause)

    # Step 2 – extract & filter image URLs by year
    urls = _extract_images_with_year(html, args.year)
    if not urls:
        print("[!] No images found. The page structure may have changed.")
        return

    print(f"[+] Downloading {len(urls)} image(s) to {out_dir} …")

    # Step 3 – download
    session = requests.Session()
    session.headers.update(HEADERS)

    ok = fail = 0
    for i, url in enumerate(urls, 1):
        filename = _safe_filename(url)
        dest = out_dir / filename

        if dest.exists():
            print(f"  [{i}/{len(urls)}] Already exists – skipping {filename}")
            ok += 1
            continue

        print(f"  [{i}/{len(urls)}] {filename} …", end=" ", flush=True)
        if _download_image(url, dest, session):
            print("OK")
            ok += 1
        else:
            fail += 1

    print(f"\n[+] Done. {ok} saved, {fail} failed.")
    print(f"[+] Images saved to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
