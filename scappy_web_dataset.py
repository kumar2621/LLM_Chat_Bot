import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time
import re

# =====================================================
# CONFIG
# =====================================================

START_URL = "https://diabetes.org/about-diabetes"

ALLOWED_DOMAIN = "diabetes.org"

OUTPUT_FILE = "clean_diabetes_dataset.jsonl"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120 Safari/537.36"
    ),

    # Force English pages
    "Accept-Language": "en-US,en;q=0.9"
}

# =====================================================
# FILTERS
# =====================================================

ALLOWED_KEYWORDS = [
    "diabetes",
    "prediabetes",
    "type-1",
    "type-2",
    "a1c",
    "insulin",
    "glucose",
    "blood-sugar",
    "gestational",
    "obesity",
    "nutrition",
    "prevention",
    "symptoms",
    "technology",
    "care",
    "vaccinations",
    "complications"
]

BAD_URLS = [
    "donate",
    "shop",
    "store",
    "event",
    "events",
    "fundraise",
    "merchandise",
    "newsletter",
    "privacy-policy",
    "terms",
    "account",
    "login",
    "signup",
    "register",
    "sponsors",
    "advertise",
    "media",
    "press"
]

SKIP_EXTENSIONS = [
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".zip",
    ".mp4",
    ".mp3"
]

# =====================================================
# STORAGE
# =====================================================

visited_urls = set()

saved_content_hashes = set()

# =====================================================
# URL VALIDATION
# =====================================================

def is_valid_url(url):

    parsed = urlparse(url)

    # stay inside domain
    if parsed.netloc != ALLOWED_DOMAIN:
        return False

    # remove fragments
    url = url.split("#")[0]

    # skip files
    if any(
        url.lower().endswith(ext)
        for ext in SKIP_EXTENSIONS
    ):
        return False

    # block non-English pages
    blocked_languages = [
        "/es/",
        "/fr/",
        "/de/",
        "/ar/",
        "/ru/",
        "/zh/",
        "/hi/",
        "/pt/",
        "/jp/",
        "/ko/"
    ]

    if any(
        lang in url.lower()
        for lang in blocked_languages
    ):
        return False

    # block bad urls
    if any(
        bad in url.lower()
        for bad in BAD_URLS
    ):
        return False

    # keep diabetes-related pages only
    if not any(
        keyword in url.lower()
        for keyword in ALLOWED_KEYWORDS
    ):
        return False

    return True


# =====================================================
# TEXT CLEANER
# =====================================================

def clean_text(text):

    # remove extra spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    # remove weird characters
    text = re.sub(
        r"[^\x00-\x7F]+",
        " ",
        text
    )

    # remove emails
    text = re.sub(
        r"\S+@\S+",
        "",
        text
    )

    # remove phone numbers
    text = re.sub(
        r"\+?\d[\d\s\-]{8,}",
        "",
        text
    )

    return text.strip()


# =====================================================
# SAVE DATA
# =====================================================

def save_data(data):

    with open(
        OUTPUT_FILE,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            json.dumps(
                data,
                ensure_ascii=False
            )
            + "\n"
        )


# =====================================================
# MAIN CRAWLER
# =====================================================

def crawl(url):

    if url in visited_urls:
        return

    visited_urls.add(url)

    print(f"\n[+] Crawling: {url}")

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )

        if response.status_code != 200:

            print(
                f"[-] Failed: {response.status_code}"
            )

            return

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # =================================================
        # TARGET ONLY MAIN CONTENT BLOCKS
        # =================================================

        main_blocks = soup.select(
            ".text-content.text-block"
        )

        # fallback selectors
        if not main_blocks:

            main_blocks = soup.select(
                "main"
            )

        if not main_blocks:

            main_blocks = soup.select(
                "article"
            )

        if not main_blocks:

            print("[-] No Main Content Found")
            return

        all_content = []

        headings = []

        # =================================================
        # PROCESS EACH BLOCK
        # =================================================

        for block in main_blocks:

            # remove junk tags
            for tag in block([
                "script",
                "style",
                "nav",
                "footer",
                "header",
                "aside",
                "form",
                "button",
                "svg"
            ]):

                tag.decompose()

            # ---------------------------------------------
            # headings
            # ---------------------------------------------

            for h in block.find_all(
                ["h1", "h2", "h3"]
            ):

                text = h.get_text(
                    " ",
                    strip=True
                )

                if text:
                    headings.append(text)

            # ---------------------------------------------
            # paragraphs
            # ---------------------------------------------

            paragraphs = []

            for p in block.find_all("p"):

                text = p.get_text(
                    " ",
                    strip=True
                )

                if text:
                    paragraphs.append(text)

            content = " ".join(paragraphs)

            content = clean_text(content)

            if len(content.split()) > 50:

                all_content.append(content)

        # =================================================
        # FINAL CONTENT
        # =================================================

        final_content = " ".join(all_content)

        final_content = clean_text(
            final_content
        )

        # skip tiny pages
        if len(final_content.split()) < 100:

            print(
                "[-] Skipping Small Content"
            )

            return

        # =================================================
        # REMOVE DUPLICATE CONTENT
        # =================================================

        content_hash = hash(final_content)

        if content_hash in saved_content_hashes:

            print(
                "[-] Duplicate Content"
            )

            return

        saved_content_hashes.add(
            content_hash
        )

        # =================================================
        # PAGE TITLE
        # =================================================

        title = ""

        if soup.title:

            title = soup.title.get_text(
                strip=True
            )

        # =================================================
        # SAVE DATA
        # =================================================

        page_data = {

            "url": url,

            "title": title,

            "headings": headings,

            "content": final_content,

            "word_count":
                len(final_content.split())
        }

        save_data(page_data)

        print(f"[+] Saved: {title}")

        # =================================================
        # FIND NEXT LINKS
        # =================================================

        for a_tag in soup.find_all(
            "a",
            href=True
        ):

            next_url = urljoin(
                url,
                a_tag["href"]
            )

            next_url = next_url.split("#")[0]

            if is_valid_url(next_url):

                crawl(next_url)

        # respect website
        time.sleep(1)

    except Exception as e:

        print(f"[ERROR] {url}")
        print(e)


# =====================================================
# START
# =====================================================

crawl(START_URL)

print("\n====================================")
print("CRAWLING COMPLETED")
print(f"Visited URLs: {len(visited_urls)}")
print(f"Output File: {OUTPUT_FILE}")
print("====================================")