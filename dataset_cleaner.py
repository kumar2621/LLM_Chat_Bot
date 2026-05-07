import json
import re
import hashlib

# ==========================================
# CONFIG
# ==========================================

INPUT_FILE = "clean_diabetes_dataset.jsonl"

OUTPUT_FILE = "final_filtered_dataset.jsonl"

# ==========================================
# REMOVE URL TYPES
# ==========================================

BAD_URL_KEYWORDS = [

    # language
    "/es",
    "/fr",
    "/de",
    "/ru",
    "/ar",

    # marketing
    "donate",
    "fundraise",
    "campaign",
    "shop",
    "store",
    "merchandise",
    "event",
    "events",

    # stories/emotional
    "stories",
    "champion",
    "meet-",
    "alex",

    # legal/advocacy
    "rights",
    "advocacy",
    "safe-at-school",
    "air-travel",

    # resource pages
    "resources",
    "resource",
    "assistance",

    # misc weak pages
    "podcast",
    "webinar",
    "community",
    "camp",
]

# ==========================================
# REMOVE PHRASES
# ==========================================

REMOVE_PATTERNS = [

    "Give Today and Change lives",
    "Donate Today",
    "Shop ADA",
    "Learn More",
    "Read More",
    "Explore Camps",
    "Community Connections",
    "American Diabetes Association",

    # footer junk
    "All rights reserved",

    # repetitive CTA
    "Join our fight",
    "Take action today",
]

# ==========================================
# STORAGE
# ==========================================

seen_docs = set()

seen_paragraphs = set()

# ==========================================
# CLEANER
# ==========================================

def clean_text(text):

    # remove bad phrases
    for pattern in REMOVE_PATTERNS:

        text = text.replace(pattern, "")

    # normalize spaces
    text = re.sub(r"\s+", " ", text)

    # remove weird chars
    text = re.sub(
        r"[^\x00-\x7F]+",
        " ",
        text
    )

    return text.strip()

# ==========================================
# HASH
# ==========================================

def md5(text):

    return hashlib.md5(
        text.encode("utf-8")
    ).hexdigest()

# ==========================================
# PARAGRAPH DEDUP
# ==========================================

def remove_duplicate_paragraphs(text):

    paragraphs = re.split(r'(?<=\.)\s+', text)

    unique_paragraphs = []

    for para in paragraphs:

        para = para.strip()

        if len(para.split()) < 8:
            continue

        h = md5(para)

        if h in seen_paragraphs:
            continue

        seen_paragraphs.add(h)

        unique_paragraphs.append(para)

    return " ".join(unique_paragraphs)

# ==========================================
# MAIN
# ==========================================

saved = 0
skipped = 0

with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
     open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:

    for line in infile:

        try:

            data = json.loads(line)

            url = data.get("url", "").lower()

            title = data.get("title", "")

            headings = data.get("headings", [])

            content = data.get("content", "")

            # ==================================
            # REMOVE BAD URLS
            # ==================================

            if any(
                bad in url
                for bad in BAD_URL_KEYWORDS
            ):

                skipped += 1
                continue

            # skip homepage
            if url.rstrip("/") == "https://diabetes.org":

                skipped += 1
                continue

            # ==================================
            # CLEAN
            # ==================================

            content = clean_text(content)

            # ==================================
            # REMOVE DUP PARAGRAPHS
            # ==================================

            content = remove_duplicate_paragraphs(
                content
            )

            # ==================================
            # SKIP SMALL CONTENT
            # ==================================

            if len(content.split()) < 120:

                skipped += 1
                continue

            # ==================================
            # FULL DOC DEDUP
            # ==================================

            doc_hash = md5(content)

            if doc_hash in seen_docs:

                skipped += 1
                continue

            seen_docs.add(doc_hash)

            # ==================================
            # SAVE
            # ==================================

            final_data = {

                "url": url,

                "title": title,

                "headings": headings,

                "content": content,

                "word_count":
                    len(content.split())
            }

            outfile.write(
                json.dumps(
                    final_data,
                    ensure_ascii=False
                )
                + "\n"
            )

            saved += 1

            print(f"[+] Saved: {title}")

        except Exception as e:

            print("ERROR:", e)

# ==========================================
# DONE
# ==========================================

print("\n==============================")
print("FINAL FILTERING COMPLETED")
print("==============================")
print(f"Saved Pages: {saved}")
print(f"Skipped Pages: {skipped}")
print(f"Output File: {OUTPUT_FILE}")
print("==============================")