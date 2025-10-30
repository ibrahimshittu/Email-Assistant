from __future__ import annotations

import re
from bs4 import BeautifulSoup


QUOTE_SPLIT_RE = re.compile(r"^On .* wrote:$", re.MULTILINE)
SIG_RE = re.compile(r"--\s*$", re.MULTILINE)


def html_to_text(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ")
    return normalize_text(text)


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_quotes_and_signature(text: str) -> str:
    if not text:
        return ""
    # Remove quoted replies heuristically
    parts = QUOTE_SPLIT_RE.split(text)
    main = parts[0] if parts else text
    # Remove signature starting with --
    sig_match = SIG_RE.search(main)
    if sig_match:
        main = main[: sig_match.start()].strip()
    return main
