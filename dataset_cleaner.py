import json
import re
from collections import Counter

# ==========================================
# CONFIG
# ==========================================

INPUT_FILE = "clean_dataset.jsonl"
OUTPUT_FILE = "final_filtered_dataset.jsonl"

MIN_WORDS = 120
MAX_WORDS = 1800

# ==========================================
# GLOBAL STORAGE
# ==========================================

seen_content = set()

# ==========================================
# STRONG FILTER
# ==========================================

def is_noisy(text):

    lower = text.lower()

    noise_score = 0

    # ======================================
    # BAD PAGES
    # ======================================

    BAD_PATTERNS = [

        "table of contents",
        "contents",
        "preface",
        "foreword",
        "contributors",
        "list of contributors",
        "list of abbreviations",
        "abbreviations",
        "bibliography",
        "references",
        "further reading",
        "all rights reserved",
        "isbn",
        "published by",
        "companion website",
        "acknowledgements",
        "acknowledgments",
        "editor",
        "editors",
        "author affiliations",
        "copyright",
        "index"
    ]

    for pattern in BAD_PATTERNS:

        if pattern in lower:
            noise_score += 3

    # ======================================
    # TOO MANY YEARS
    # reference-heavy pages
    # ======================================

    years = re.findall(
        r"\b(19|20)\d{2}\b",
        text
    )

    if len(years) > 25:
        noise_score += 2

    # ======================================
    # TOO MANY CAPITAL WORDS
    # ======================================

    caps = re.findall(
        r"\b[A-Z]{2,}\b",
        text
    )

    if len(caps) > 50:
        noise_score += 2

    # ======================================
    # TOO MANY COMMAS
    # contributor pages
    # ======================================

    if text.count(",") > 100:
        noise_score += 2

    # ======================================
    # TOO MANY NAMES
    # ======================================

    names = re.findall(
        r"\b[A-Z][a-z]+\s[A-Z][a-z]+\b",
        text
    )

    if len(names) > 40:
        noise_score += 2

    # ======================================
    # TOO MANY SHORT TOKENS
    # abbreviation pages
    # ======================================

    short_tokens = re.findall(
        r"\b[A-Z0-9\-]{2,6}\b",
        text
    )

    if len(short_tokens) > 70:
        noise_score += 2

    # ======================================
    # TOO REPETITIVE
    # ======================================

    words = text.lower().split()

    if len(words) > 50:

        common_words = Counter(words)

        most_common = common_words.most_common(1)[0][1]

        repetition_ratio = most_common / len(words)

        if repetition_ratio > 0.08:
            noise_score += 2

    # ======================================
    # FINAL DECISION
    # ======================================

    return noise_score >= 4

# ==========================================
# CLEAN TEXT
# ==========================================

def clean_text(text):

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

    # remove multiple spaces
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

    # remove repeated punctuation
    text = re.sub(
        r"[=~_]{2,}",
        " ",
        text
    )

    return text.strip()

# ==========================================
# REMOVE DUPLICATE SENTENCES
# ==========================================

def deduplicate_sentences(text):

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
# MAIN
# ==========================================

total = 0
saved = 0
removed = 0
duplicates = 0

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as infile, open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as outfile:

    for line in infile:

        total += 1

        try:

            data = json.loads(line)

            content = data.get(
                "content",
                ""
            )

            # ==================================
            # CLEAN
            # ==================================

            content = clean_text(content)

            content = deduplicate_sentences(
                content
            )

            # ==================================
            # WORD COUNT FILTER
            # ==================================

            word_count = len(
                content.split()
            )

            if word_count < MIN_WORDS:
                removed += 1
                continue

            if word_count > MAX_WORDS:
                removed += 1
                continue

            # ==================================
            # NOISE FILTER
            # ==================================

            if is_noisy(content):

                removed += 1

                print(
                    f"[-] Removed Noisy "
                    f"Entry {total}"
                )

                continue

            # ==================================
            # GLOBAL DEDUP
            # ==================================

            content_hash = hash(
                content[:1200]
            )

            if content_hash in seen_content:

                duplicates += 1

                continue

            seen_content.add(
                content_hash
            )

            # ==================================
            # UPDATE CONTENT
            # ==================================

            data["content"] = content

            data["word_count"] = word_count

            # ==================================
            # SAVE
            # ==================================

            outfile.write(
                json.dumps(
                    data,
                    ensure_ascii=False
                )
                + "\n"
            )

            saved += 1

        except Exception as e:

            print("ERROR:", e)

# ==========================================
# FINAL STATS
# ==========================================

print("\n================================")
print("FINAL FILTERING COMPLETE")
print("================================")
print(f"Total Entries: {total}")
print(f"Saved Entries: {saved}")
print(f"Removed Noise: {removed}")
print(f"Removed Duplicates: {duplicates}")
print(f"Output File: {OUTPUT_FILE}")
print("================================")