import fitz
import json
import re
from uuid import uuid4

# ==========================================
# CONFIG
# ==========================================

PDF_FILES = [

    "book1.pdf",
    "book2.pdf"
]

OUTPUT_FILE = "clean_dataset.jsonl"

MIN_WORDS = 80
MAX_WORDS = 2500

# ==========================================
# STRONG CLEANER
# ==========================================

def clean_text(text):

    original_text = text

    lower = text.lower()

    # ======================================
    # NOISE SCORE
    # ======================================

    noise_score = 0

    # --------------------------------------
    # BAD STRUCTURAL PATTERNS
    # --------------------------------------

    BAD_PATTERNS = [

        "list of contributors",
        "contributors",
        "list of abbreviations",
        "table of contents",
        "contents",
        "bibliography",
        "references",
        "all rights reserved",
        "published by",
        "isbn",
        "editor",
        "editors",
        "author affiliations",
        "copyright",
        "acknowledgements",
        "acknowledgments",
        "further reading",
        "index"
    ]

    for pattern in BAD_PATTERNS:

        if pattern in lower:
            noise_score += 3

    # ======================================
    # TOO MANY CAPS WORDS
    # usually abbreviation/contributor pages
    # ======================================

    capital_words = re.findall(
        r"\b[A-Z]{2,}\b",
        original_text
    )

    if len(capital_words) > 40:
        noise_score += 2

    # ======================================
    # TOO MANY COMMAS
    # contributor pages
    # ======================================

    comma_count = original_text.count(",")

    if comma_count > 80:
        noise_score += 2

    # ======================================
    # TOO MANY SHORT MEDICAL CODES
    # abbreviation pages
    # ======================================

    short_tokens = re.findall(
        r"\b[A-Z0-9\-]{2,6}\b",
        original_text
    )

    if len(short_tokens) > 60:
        noise_score += 3

    # ======================================
    # TOO MANY YEARS / REFERENCES
    # citation-heavy pages
    # ======================================

    years = re.findall(
        r"\b(19|20)\d{2}\b",
        original_text
    )

    if len(years) > 25:
        noise_score += 2

    # ======================================
    # TOO MANY NAMES
    # contributor pages
    # ======================================

    names = re.findall(
        r"\b[A-Z][a-z]+\s[A-Z][a-z]+\b",
        original_text
    )

    if len(names) > 25:
        noise_score += 2

    # ======================================
    # TOO MANY VERY SHORT LINES
    # TOC / abbreviation pages
    # ======================================

    lines = original_text.split("\n")

    short_lines = 0

    for line in lines:

        if len(line.split()) <= 4:
            short_lines += 1

    if short_lines > 20:
        noise_score += 2

    # ======================================
    # REJECT PAGE
    # ======================================

    if noise_score >= 4:

        return None

    # ======================================
    # CLEAN TEXT
    # ======================================

    # remove urls
    text = re.sub(
        r"http\S+",
        " ",
        text
    )

    # remove emails
    text = re.sub(
        r"\S+@\S+",
        " ",
        text
    )

    # remove excessive spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    # remove weird unicode
    text = re.sub(
        r"[^\x00-\x7F]+",
        " ",
        text
    )

    # remove isolated numbers
    text = re.sub(
        r"\b\d+\b",
        " ",
        text
    )

    # remove repeated punctuation
    text = re.sub(
        r"[=~_]{2,}",
        " ",
        text
    )

    # remove extra dots
    text = re.sub(
        r"\.{2,}",
        ".",
        text
    )

    text = text.strip()

    return text

# ==========================================
# REMOVE DUPLICATE SENTENCES
# ==========================================

def remove_duplicate_sentences(text):

    sentences = re.split(
        r'(?<=[.!?])\s+',
        text
    )

    seen = set()

    cleaned = []

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence.split()) < 5:
            continue

        normalized = sentence.lower()

        if normalized in seen:
            continue

        seen.add(normalized)

        cleaned.append(sentence)

    return " ".join(cleaned)

# ==========================================
# EXTRACT PDF
# ==========================================

def extract_pdf(pdf_path):

    print(f"\n[+] Reading: {pdf_path}")

    doc = fitz.open(pdf_path)

    pages_data = []

    for page_num in range(len(doc)):

        try:

            page = doc[page_num]

            text = page.get_text()

            if not text:
                continue

            # ==================================
            # CLEAN
            # ==================================

            text = clean_text(text)

            if not text:
                print(
                    f"[-] Skipped Noise "
                    f"Page {page_num+1}"
                )
                continue

            # ==================================
            # REMOVE DUPLICATES
            # ==================================

            text = remove_duplicate_sentences(
                text
            )

            word_count = len(text.split())

            # ==================================
            # SKIP BAD SIZES
            # ==================================

            if word_count < MIN_WORDS:

                print(
                    f"[-] Tiny Page "
                    f"{page_num+1}"
                )

                continue

            if word_count > MAX_WORDS:

                print(
                    f"[-] Huge Page "
                    f"{page_num+1}"
                )

                continue

            # ==================================
            # SAVE PAGE
            # ==================================

            page_data = {

                "id": str(uuid4()),

                "source": pdf_path,

                "page":
                    page_num + 1,

                "word_count":
                    word_count,

                "content":
                    text
            }

            pages_data.append(
                page_data
            )

            print(
                f"[+] Saved Page "
                f"{page_num+1}"
            )

        except Exception as e:

            print(
                f"[ERROR] Page "
                f"{page_num+1}: {e}"
            )

    return pages_data

# ==========================================
# MAIN
# ==========================================

all_pages = []

for pdf_file in PDF_FILES:

    pages = extract_pdf(pdf_file)

    all_pages.extend(pages)

# ==========================================
# GLOBAL DEDUPLICATION
# ==========================================

print("\n[+] Removing duplicate pages...")

unique_pages = []

seen_hashes = set()

for page in all_pages:

    content_hash = hash(
        page["content"][:1000]
    )

    if content_hash in seen_hashes:
        continue

    seen_hashes.add(content_hash)

    unique_pages.append(page)

# ==========================================
# SAVE DATASET
# ==========================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    for item in unique_pages:

        f.write(
            json.dumps(
                item,
                ensure_ascii=False
            )
            + "\n"
        )

# ==========================================
# FINAL STATS
# ==========================================

print("\n================================")
print("STRONG CLEAN DATASET CREATED")
print("================================")
print(f"Original Pages: {len(all_pages)}")
print(f"Final Pages: {len(unique_pages)}")
print(f"Saved File: {OUTPUT_FILE}")
print("================================")