"""
Fetching job description text from a URL.

This is a best-effort convenience, not a guaranteed feature: job sites
build their pages in wildly different ways (some render the posting text
directly in HTML, some load it via JavaScript we can't execute here,
some block simple scripted requests entirely). When this fails or
returns garbage, that's expected sometimes - it's exactly why the UI
also offers a "paste text instead" option as a fallback that always
works, since you can always see and copy the text yourself in a browser.
"""

import requests
from bs4 import BeautifulSoup

# A generic browser User-Agent - many sites block requests with no
# User-Agent header (or a default library one like "python-requests/...")
# on the assumption that only real browsers make legitimate requests.
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_jd_text_from_url(url: str) -> str:
    """
    Fetch a URL and pull out its visible text as a best-effort attempt at
    the job description content.

    We strip <script> and <style> tags before extracting text, since
    their contents aren't visible page text and would just be noise -
    everything else on the page comes through, so the result may include
    site navigation/footer text alongside the actual posting. That's an
    accepted tradeoff for keeping this simple; the chunking step's bullet
    -marker filtering (Phase 2) already discards a lot of that noise.
    """
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Collapse the many blank/whitespace-only lines that come out of
    # get_text() on real-world HTML into a clean line-per-statement text,
    # matching the shape our chunking step expects.
    lines = [line.strip() for line in text.split("\n")]
    non_empty_lines = [line for line in lines if line]
    return "\n".join(non_empty_lines)
