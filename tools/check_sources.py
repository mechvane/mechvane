#!/usr/bin/env python3
"""Automated source link and quotation verification for Mechvane research catalogs.

Extracts source URLs, literal quotations, and numerical values from research markdown files,
fetches remote sources (HTML, PDF) with browser User-Agent and per-host rate limiting,
caches responses under /tmp/quellen-cache, and validates reachability, quote presence,
and numerical claims.

Usage:
  python3 tools/check_sources.py                       # check all docs/research/*flash*.md
  python3 tools/check_sources.py docs/research/*.md    # check specific files
  python3 tools/check_sources.py --json                # machine-readable output
  python3 tools/check_sources.py --no-cache            # bypass disk cache
"""

import argparse
from dataclasses import dataclass, field, asdict
import datetime as dt
import difflib
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE_DIR = Path("/tmp/quellen-cache")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# HTML and Text Parsing Helpers
# ---------------------------------------------------------------------------

class HTMLToTextParser(HTMLParser):
    """Converts HTML markup into clean text, stripping scripts, styles and heads."""

    def __init__(self):
        super().__init__()
        self.pieces = []
        self.skip_depth = 0
        self.skip_tags = {"script", "style", "head", "noscript", "svg", "iframe"}
        self.block_tags = {
            "p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6",
            "br", "td", "th", "table", "section", "article", "header", "footer"
        }

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in self.skip_tags:
            self.skip_depth += 1
        elif t in self.block_tags:
            self.pieces.append("\n")

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in self.skip_tags:
            self.skip_depth = max(0, self.skip_depth - 1)
        elif t in self.block_tags:
            self.pieces.append("\n")

    def handle_data(self, data):
        if self.skip_depth == 0:
            self.pieces.append(data)

    def get_text(self) -> str:
        raw = "".join(self.pieces)
        lines = [line.strip() for line in raw.splitlines()]
        return "\n".join(l for l in lines if l)


def html_to_text(html_content: str) -> str:
    """Parse HTML string into readable plaintext."""
    parser = HTMLToTextParser()
    try:
        parser.feed(html_content)
        return parser.get_text()
    except Exception:
        # Fallback regex strip
        text = re.sub(r'<(script|style|head)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        return html.unescape(re.sub(r'\s+', ' ', text)).strip()


def normalize_text_for_matching(text: str) -> str:
    """Normalize dashes, quotation marks, and whitespace for fuzzy comparison."""
    # Normalize unicode hyphens/dashes
    text = re.sub(r'[\u2010-\u2015\u2212]', '-', text)
    # Remove all quotation marks (German low quotes, English curly quotes, guillemets, straight)
    text = re.sub(r'[\u201c\u201d\u201e"\'`«»]', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()


def clean_latex(s: str) -> str:
    """Simplify LaTeX math formatting found in research markdown files."""
    s = s.replace('{,}', ',')
    s = s.replace(r'\,', ' ')
    s = s.replace(r'\cdot', '*')
    s = s.replace(r'\pm', '±')
    s = s.replace(r'\le', '<=')
    s = s.replace(r'\ge', '>=')
    s = re.sub(r'\\text\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\mathbf\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\math[a-zA-Z]+\{([^}]*)\}', r'\1', s)
    return s


# ---------------------------------------------------------------------------
# Link, Quote, and Number Extraction
# ---------------------------------------------------------------------------

def extract_markdown_links(text: str) -> tuple[list[tuple[str, str]], str]:
    """Extract [anchor](url) links handling balanced parentheses within the URL.

    Returns:
      (links, text_with_links_removed)
    """
    links = []
    clean_pieces = []
    i = 0
    n = len(text)
    last_end = 0

    while i < n:
        if text[i] == '[':
            cb = text.find(']', i + 1)
            if cb != -1 and cb + 1 < n and text[cb + 1] == '(':
                depth = 1
                j = cb + 2
                while j < n and depth > 0:
                    if text[j] == '(':
                        depth += 1
                    elif text[j] == ')':
                        depth -= 1
                    j += 1
                if depth == 0:
                    anchor = text[i + 1:cb]
                    url = text[cb + 2:j - 1].strip()
                    links.append((anchor, url))
                    clean_pieces.append(text[last_end:i])
                    clean_pieces.append(" ")
                    last_end = j
                    i = j
                    continue
        i += 1
    clean_pieces.append(text[last_end:])
    clean_text = "".join(clean_pieces)
    return links, clean_text


def find_urls_in_text(text: str) -> list[str]:
    """Extract all valid HTTP/HTTPS URLs from a text block."""
    urls = []
    # 1. From markdown links
    md_links, text_without_md = extract_markdown_links(text)
    for _, u in md_links:
        if u.startswith(('http://', 'https://')):
            urls.append(u)
    # 2. From bare URLs (excluding markdown links and bracket delimiters)
    bare = re.findall(r'https?://[^\s<>\'\"`()\[\]]+', text_without_md)
    for b in bare:
        b = b.rstrip('.,;:)]}')
        if b.startswith(('http://', 'https://')) and b not in urls:
            urls.append(b)

    cleaned = []
    for u in urls:
        # Filter out incomplete placeholders or local development urls
        if '...' in u:
            continue
        if u.startswith(('http://localhost', 'http://127.0.0.1')):
            continue
        if u not in cleaned:
            cleaned.append(u)
    return cleaned


def find_quotes_in_text(text: str) -> list[str]:
    """Extract literal quotation strings from a markdown entry block."""
    lines = [re.sub(r'^\s*>\s*', '', l) for l in text.splitlines()]
    clean_text = "\n".join(lines)
    quotes = []

    # 1. German low-quote and English quotes: „...“ or “...” or "..."
    for m in re.finditer(r'[\u201e\u201c\"«]([^\u201c\u201d\"\n]+(?:\n[^\u201c\u201d\"\n]+)*)[\u201c\u201d\"»]', clean_text):
        q = re.sub(r'\s+', ' ', m.group(1)).strip().strip('*_')
        if len(q) >= 12 and not q.startswith(('[!NOTE]', '[!TIP]', '[!IMPORTANT]', '[!WARNING]')):
            if q not in quotes:
                quotes.append(q)

    # 2. Backtick code blocks with table rows / explicit data lines
    for m in re.finditer(r'`([^`\n]{15,})`', text):
        c = m.group(1).strip()
        if any(w in c for w in ('Thread d:', 'dk max', 'k max', 's nominal', 'Nominal Size:', 'P: ', 'dg:', 'M2,5', 'M3')):
            if c not in quotes:
                quotes.append(c)

    return quotes


def find_numbers_in_text(text: str) -> list[dict[str, str]]:
    """Extract distinct numerical values mentioned in the entry, ignoring URLs and page numbers."""
    # Strip URLs so hex hashes, ports, or IDs in URL paths are not treated as claimed numbers
    text = re.sub(r'https?://[^\s<>\'\"`()\[\]]+', '', text)
    # Strip citation page numbers (e.g., Seite 144, S. 2)
    text = re.sub(r'\b(?:Seite|S\.)\s+\d+\b', '', text)
    # Strip list item numbering prefixes at line starts
    text = re.sub(r'(?m)^\s*\d+\.\s+', '', text)

    cleaned = clean_latex(text)
    # Match numbers with German comma or decimal dot, and optional units
    raw_matches = re.finditer(r'[-+]?\b(\d+(?:[.,]\d+)?)\s*([a-zA-Z°%µμ/^*\-]+)?', cleaned)
    numbers = []
    seen = set()
    # Skip year numbers commonly found in bibliography metadata
    skip_years = {'2020', '2021', '2022', '2023', '2024', '2025', '2026', '1984', '1985', '1990', '1998', '2004', '2015', '2018', '2019'}

    for m in raw_matches:
        num_str = m.group(1)
        unit = m.group(2) or ''
        if num_str in skip_years:
            continue
        key = (num_str, unit)
        if key not in seen:
            seen.add(key)
            numbers.append({"number": num_str, "unit": unit})
    return numbers


# ---------------------------------------------------------------------------
# Document Entry Parsing
# ---------------------------------------------------------------------------

@dataclass
class Entry:
    file_path: Path
    title: str
    line: int
    urls: list[str] = field(default_factory=list)
    quotes: list[str] = field(default_factory=list)
    numbers: list[dict[str, str]] = field(default_factory=list)
    text: str = ""


def parse_markdown_entries(filepath: Path) -> list[Entry]:
    """Parse a markdown file into discrete research entries."""
    text = filepath.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)

    heading_re = re.compile(r'^(#{1,6})\s+(.+)$')
    q_item_re = re.compile(r'^\s*\*\s+\*\*(\[Q\d+\].*?)\*\*')
    num_item_re = re.compile(r'^\s*(\d+\.)\s+\*\*(.*?)\*\*')

    boundaries = []
    in_quellenliste = False

    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        hm = heading_re.match(line)
        if hm:
            level = len(hm.group(1))
            title = hm.group(2).strip()
            # Recognize list sections where each numbered child is a distinct entry
            if 'quellenliste' in title.lower() or 'quellenbelege' in title.lower():
                in_quellenliste = True
            elif level <= 2:
                in_quellenliste = False
            boundaries.append((idx, level, title))
            continue

        qm = q_item_re.match(line)
        if qm:
            boundaries.append((idx, 5, qm.group(1).strip()))
            continue

        if in_quellenliste:
            nm = num_item_re.match(line)
            if nm:
                boundaries.append((idx, 5, f"{nm.group(1)} {nm.group(2).strip()}"))
                continue

    boundaries.append((len(lines), 0, 'EOF'))

    entries = []
    for i in range(len(boundaries) - 1):
        start_idx, level, title = boundaries[i]
        end_idx = boundaries[i + 1][0]

        # Skip container headings that contain children
        has_child = False
        for j in range(i + 1, len(boundaries) - 1):
            if boundaries[j][0] < end_idx:
                has_child = True
                break
        if has_child:
            continue

        chunk_text = "".join(lines[start_idx:end_idx])
        urls = find_urls_in_text(chunk_text)
        if not urls:
            continue

        # Skip sections dedicated exclusively to listing already unreachable sources
        if 'nicht erreichbare quellen' in title.lower():
            continue

        # Skip summary tables when detailed individual entries exist below
        if 'übersichtstabelle' in title.lower() and any('detaillierte' in b[2].lower() for b in boundaries):
            continue

        quotes = find_quotes_in_text(chunk_text)
        numbers = find_numbers_in_text(chunk_text)

        clean_title = re.sub(r'[*_`#]', '', title).strip()
        if len(clean_title) > 60:
            clean_title = clean_title[:57] + '...'

        entries.append(Entry(
            file_path=filepath,
            title=clean_title,
            line=start_idx + 1,
            urls=urls,
            quotes=quotes,
            numbers=numbers,
            text=chunk_text
        ))

    # Special handling for files like normtabellen where tables in early sections
    # correspond to numbered items in Quellenliste at the end:
    if "normtabellen" in filepath.name:
        link_normtabellen_quotes(filepath, entries)

    return entries


def link_normtabellen_quotes(filepath: Path, entries: list[Entry]) -> None:
    """Link table quotes and numbers from top sections to corresponding URLs at bottom."""
    text = filepath.read_text(encoding="utf-8", errors="replace")
    # Find all table sections like ### 1. ISO 4762: ...
    section_matches = re.split(r'\n(?=###\s+\d+\.)', text)
    section_map = {}
    for sec in section_matches:
        m = re.match(r'###\s+(\d+)\.\s+([^:\n]+)', sec)
        if m:
            num = m.group(1)
            std = m.group(2).strip()
            quotes = find_quotes_in_text(sec)
            numbers = find_numbers_in_text(sec)
            section_map[num] = (quotes, numbers)

    for entry in entries:
        m = re.match(r'^(\d+)\.', entry.title)
        if m and m.group(1) in section_map:
            q, n = section_map[m.group(1)]
            if not entry.quotes:
                entry.quotes.extend(q)
            if not entry.numbers:
                entry.numbers.extend(n)


# ---------------------------------------------------------------------------
# Network Fetcher & Caching
# ---------------------------------------------------------------------------

class SourceFetcher:
    """Fetches remote URLs with rate limiting, timeouts, and local disk caching."""

    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR, timeout: int = 20, use_cache: bool = True):
        self.cache_dir = cache_dir
        self.timeout = timeout
        self.use_cache = use_cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.last_request_time: dict[str, float] = {}
        self.memory_cache: dict[str, dict] = {}

    def _rate_limit(self, host: str) -> None:
        """Enforce maximum of 1 request per second per host."""
        now = time.time()
        last = self.last_request_time.get(host, 0.0)
        elapsed = now - last
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        self.last_request_time[host] = time.time()

    def fetch(self, url: str) -> dict:
        """Fetch URL content or retrieve from cache."""
        if url in self.memory_cache:
            return self.memory_cache[url]

        key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        meta_file = self.cache_dir / f"{key}.json"
        txt_file = self.cache_dir / f"{key}.txt"

        if self.use_cache and meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                if txt_file.exists():
                    meta["text"] = txt_file.read_text(encoding="utf-8", errors="replace")
                else:
                    meta["text"] = ""
                self.memory_cache[url] = meta
                return meta
            except Exception:
                pass  # Fall through to re-fetch on cache corruption

        # Normalize URL path/query for non-ASCII characters
        parsed = urllib.parse.urlsplit(url)
        encoded_path = urllib.parse.quote(parsed.path, safe='/:?=&%')
        encoded_query = urllib.parse.quote(parsed.query, safe='/:?=&%')
        req_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, encoded_path, encoded_query, parsed.fragment))

        host = parsed.netloc.lower()
        self._rate_limit(host)

        req = urllib.request.Request(
            req_url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8",
                "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )

        ssl_ctx = ssl.create_default_context()
        # Fallback lenient context if system certificate authorities reject domain cert
        unverified_ssl_ctx = ssl._create_unverified_context()

        status_code = 0
        extracted_text = ""
        error_msg = ""
        content_type = ""

        try:
            try:
                resp_ctx = urllib.request.urlopen(req, timeout=self.timeout, context=ssl_ctx)
            except urllib.error.URLError as ue:
                if isinstance(ue.reason, ssl.SSLCertVerificationError):
                    resp_ctx = urllib.request.urlopen(req, timeout=self.timeout, context=unverified_ssl_ctx)
                else:
                    raise ue

            with resp_ctx as resp:
                status_code = resp.status
                content_type = resp.headers.get("Content-Type", "").lower()
                data = resp.read()

                # Process PDF or HTML
                is_pdf = "application/pdf" in content_type or url.lower().endswith(".pdf") or data.startswith(b"%PDF")

                if is_pdf:
                    raw_pdf_path = self.cache_dir / f"{key}.pdf"
                    raw_pdf_path.write_bytes(data)
                    try:
                        cmd = ["pdftotext", "-layout", str(raw_pdf_path), str(txt_file)]
                        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
                        if txt_file.exists():
                            extracted_text = txt_file.read_text(encoding="utf-8", errors="replace")
                    except Exception as e:
                        error_msg = f"pdftotext failed: {e}"
                else:
                    charset = resp.headers.get_content_charset() or "utf-8"
                    try:
                        decoded_html = data.decode(charset, errors="replace")
                    except Exception:
                        decoded_html = data.decode("utf-8", errors="replace")
                    extracted_text = html_to_text(decoded_html)
                    txt_file.write_text(extracted_text, encoding="utf-8", errors="replace")

        except urllib.error.HTTPError as he:
            status_code = he.code
            error_msg = str(he)
        except urllib.error.URLError as ue:
            status_code = 0  # 000 in reporting
            error_msg = str(ue.reason)
        except TimeoutError:
            status_code = 0
            error_msg = "Connection timed out"
        except Exception as e:
            status_code = 0
            error_msg = str(e)

        result = {
            "url": url,
            "status_code": status_code,
            "content_type": content_type,
            "error": error_msg,
            "text": extracted_text,
            "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat()
        }

        # Cache metadata
        meta_to_save = {k: v for k, v in result.items() if k != "text"}
        try:
            meta_file.write_text(json.dumps(meta_to_save, indent=2), encoding="utf-8")
        except OSError:
            pass

        self.memory_cache[url] = result
        return result


# ---------------------------------------------------------------------------
# Verification Logic
# ---------------------------------------------------------------------------

def check_quote_in_text(quote: str, doc_text: str) -> tuple[str, float]:
    """Check if quote is present in document text.

    Returns:
      (status, best_ratio) where status is 'ja', 'teilweise', or 'nein'.
    """
    # Strip boundary quotes and ellipses
    quote = quote.strip('„“”"\'`«» ')
    quote = re.sub(r'(\[\.\.\.\]|\.\.\.)+$', '', quote).strip()
    quote = re.sub(r'^(\[\.\.\.\]|\.\.\.)+', '', quote).strip()

    norm_q = normalize_text_for_matching(quote)
    norm_d = normalize_text_for_matching(doc_text)

    if not norm_q or not norm_d:
        return "-", 0.0

    # 1. Exact normalized match
    if norm_q in norm_d:
        return "ja", 1.0

    # 2. Check ellipsis splitting [...] or ...
    parts = [normalize_text_for_matching(p.strip()) for p in re.split(r'\[\.\.\.\]|\.\.\.', quote) if len(p.strip()) >= 10]
    if len(parts) > 1:
        matched = sum(1 for p in parts if p in norm_d)
        if matched == len(parts):
            return "ja", 1.0
        elif matched > 0:
            return "teilweise", matched / len(parts)

    # 3. Fuzzy search via anchor words and SequenceMatcher
    q_words = [w for w in re.findall(r'\b\w+\b', norm_q) if len(w) > 2]
    if not q_words:
        return "nein", 0.0

    anchor_len = min(4, len(q_words))
    anchor = " ".join(q_words[:anchor_len])
    best_ratio = 0.0

    pos = norm_d.find(anchor)
    while pos != -1:
        w_start = max(0, pos - 10)
        w_end = min(len(norm_d), pos + len(norm_q) + 10)
        window = norm_d[w_start:w_end]
        ratio = difflib.SequenceMatcher(None, norm_q, window).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
        if best_ratio >= 0.85:
            return "ja", best_ratio
        pos = norm_d.find(anchor, pos + 1)

    # 4. Overlapping window search across document
    target_len = len(norm_q)
    step = max(50, target_len // 2)
    q_word_set = set(q_words)
    for i in range(0, len(norm_d), step):
        chunk = norm_d[i: i + target_len + 30]
        chunk_words = set(re.findall(r'\b\w+\b', chunk))
        overlap = len(q_word_set & chunk_words)
        if overlap >= len(q_word_set) * 0.4:
            ratio = difflib.SequenceMatcher(None, norm_q, chunk).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
            if best_ratio >= 0.85:
                return "ja", best_ratio

    if best_ratio >= 0.85:
        return "ja", best_ratio
    elif best_ratio >= 0.50:
        return "teilweise", best_ratio
    return "nein", best_ratio


def check_number_in_text(num_str: str, doc_text: str) -> bool:
    """Check if number string is found in doc_text, supporting comma and dot."""
    clean_num = num_str.lstrip('+-')
    if ',' in clean_num:
        parts = clean_num.split(',')
        pattern = r'(?<!\d)' + re.escape(parts[0]) + r'[.,]' + re.escape(parts[1]) + r'(?!\d)'
    elif '.' in clean_num:
        parts = clean_num.split('.')
        pattern = r'(?<!\d)' + re.escape(parts[0]) + r'[.,]' + re.escape(parts[1]) + r'(?!\d)'
    else:
        pattern = r'(?<!\d)' + re.escape(clean_num) + r'(?!\d)'
    return bool(re.search(pattern, doc_text))


def verify_entry_url(entry: Entry, url: str, fetcher: SourceFetcher) -> dict:
    """Verify an entry against a specific URL."""
    fetch_res = fetcher.fetch(url)
    status_code = fetch_res["status_code"]
    doc_text = fetch_res.get("text", "")

    http_str = f"{status_code:03d}" if status_code > 0 else "000"

    # Verify quote
    if not entry.quotes or status_code != 200:
        quote_verdict = "–"
    else:
        q_results = [check_quote_in_text(q, doc_text)[0] for q in entry.quotes]
        if all(r == "ja" for r in q_results):
            quote_verdict = "ja"
        elif any(r in ("ja", "teilweise") for r in q_results):
            quote_verdict = "teilweise"
        else:
            quote_verdict = "nein"

    # Verify numbers
    if not entry.numbers or status_code != 200:
        num_str = "–"
        nums_found = 0
        nums_total = 0
        missing_nums = []
    else:
        found_count = 0
        missing_nums = []
        for n_info in entry.numbers:
            n_val = n_info["number"]
            if check_number_in_text(n_val, doc_text):
                found_count += 1
            else:
                missing_nums.append(f"{n_val} {n_info.get('unit', '')}".strip())
        nums_found = found_count
        nums_total = len(entry.numbers)
        num_str = f"{nums_found} von {nums_total}"

    return {
        "file": str(entry.file_path),
        "entry": entry.title,
        "line": entry.line,
        "url": url,
        "http": http_str,
        "status_code": status_code,
        "quote": quote_verdict,
        "numbers": num_str,
        "numbers_found": nums_found,
        "numbers_total": nums_total,
        "missing_numbers": missing_nums,
        "error": fetch_res.get("error", "")
    }


# ---------------------------------------------------------------------------
# Output Formatting
# ---------------------------------------------------------------------------

def generate_markdown_report(results_by_file: dict[str, list[dict]], command_str: str = "python3 tools/check_sources.py") -> str:
    """Format verification results as GitHub-flavored markdown with summary, auffaellige Eintraege, and tables."""
    lines = []
    total_sources = sum(len(res) for res in results_by_file.values())
    total_reachable = sum(sum(1 for r in res if r["status_code"] == 200) for res in results_by_file.values())
    total_unreachable = total_sources - total_reachable

    total_quotes_confirmed = sum(sum(1 for r in res if r["quote"] == "ja") for res in results_by_file.values())
    total_quotes_partial = sum(sum(1 for r in res if r["quote"] == "teilweise") for res in results_by_file.values())
    total_quotes_failed = sum(sum(1 for r in res if r["quote"] == "nein") for res in results_by_file.values())

    total_nums_checked = sum(sum(r.get("numbers_total", 0) for r in res if r["status_code"] == 200) for res in results_by_file.values())
    total_nums_found = sum(sum(r.get("numbers_found", 0) for r in res if r["status_code"] == 200) for res in results_by_file.values())

    # Collect auffaellige Eintraege (reachable HTTP 200 but numbers missing, or quote failed)
    suspicious = []
    for filepath, entries_res in results_by_file.items():
        rel_path = filepath
        try:
            rel_path = str(Path(filepath).relative_to(REPO_ROOT))
        except Exception:
            pass
        for r in entries_res:
            if r["status_code"] == 200:
                # If numbers were expected but none found, or only some found
                if r.get("numbers_total", 0) > 0 and r.get("numbers_found", 0) < r.get("numbers_total", 0):
                    suspicious.append({
                        "file": rel_path,
                        "entry": f"{r['entry']} (L{r['line']})",
                        "url": r["url"],
                        "found": r["numbers_found"],
                        "total": r["numbers_total"],
                        "missing": r.get("missing_numbers", [])
                    })

    lines.append(f"# Quellenprüfung: Lauf 1 ({dt.date.today().isoformat()})")
    lines.append("")
    lines.append(f"- **Datum:** {dt.date.today().isoformat()}")
    lines.append(f"- **Befehl:** `{command_str}`")
    lines.append(f"- **Geprüfte Markdown-Dateien:** {len(results_by_file)}")
    lines.append("")
    lines.append("## Zusammenfassung")
    lines.append("")
    lines.append(f"- **Quellen-Links gesamt:** {total_sources}")
    lines.append(f"- **Erreichbar (HTTP 200):** {total_reachable} von {total_sources} ({total_reachable / max(1, total_sources):.1%})")
    lines.append(f"- **Nicht erreichbar:** {total_unreachable} von {total_sources} (Bot-Sperren, 404, Timeouts)")
    lines.append(f"- **Zitate bestätigt:** {total_quotes_confirmed} voll bestätigt, {total_quotes_partial} teilweise bestätigt, {total_quotes_failed} nicht gefunden")
    lines.append(f"- **Zahlenwerte bestätigt:** {total_nums_found} von {total_nums_checked} Werten im Quelltext nachgewiesen ({total_nums_found / max(1, total_nums_checked):.1%})")
    lines.append("")

    lines.append("## Auffällige Einträge mit nicht gefundenen Zahlen")
    lines.append("")
    if not suspicious:
        lines.append("*Keine auffälligen Einträge mit fehlenden Zahlen gefunden.*")
        lines.append("")
    else:
        lines.append("Bei folgenden erreichbaren Quellen konnten einzelne oder alle im Katalog genannten Zahlen nicht im extrahierten Text gefunden werden:")
        lines.append("")
        lines.append("| Datei / Zeile | Eintrag | Gefunden | Fehlende Werte (Auszug) | URL |")
        lines.append("| :--- | :--- | :---: | :--- | :--- |")
        for s in suspicious:
            missing_sample = ", ".join(s["missing"][:6])
            if len(s["missing"]) > 6:
                missing_sample += f" ... (+{len(s['missing']) - 6} weitere)"
            short_url = f"[{s['url'][:45]}...]({s['url']})" if len(s['url']) > 45 else f"[{s['url']}]({s['url']})"
            lines.append(f"| `{s['file']}` | {s['entry']} | {s['found']}/{s['total']} | {missing_sample} | {short_url} |")
        lines.append("")

    lines.append("## Detaillierte Tabellen je Datei")
    lines.append("")

    for filepath, entries_res in results_by_file.items():
        rel_path = filepath
        try:
            rel_path = str(Path(filepath).relative_to(REPO_ROOT))
        except Exception:
            pass

        lines.append(f"### `{rel_path}`")
        lines.append("")
        if not entries_res:
            lines.append("*Keine externen Quell-URLs gefunden.*")
            lines.append("")
            continue

        lines.append("| Eintrag / Zeile | URL | HTTP | Zitat | Zahlen |")
        lines.append("| :--- | :--- | :---: | :---: | :---: |")
        for r in entries_res:
            entry_col = f"{r['entry']} (L{r['line']})"
            url_col = f"[{r['url'][:60]}...]({r['url']})" if len(r['url']) > 60 else f"[{r['url']}]({r['url']})"
            lines.append(f"| {entry_col} | {url_col} | {r['http']} | {r['quote']} | {r['numbers']} |")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI Main Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Verify research source URLs, quotes, and numbers."
    )
    parser.add_argument(
        "files", nargs="*",
        help="Markdown files to verify. If omitted, checks all docs/research/*flash*.md."
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output structured JSON results to stdout."
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Bypass local disk cache."
    )
    parser.add_argument(
        "--cache-dir", type=Path, default=DEFAULT_CACHE_DIR,
        help="Directory to cache fetched source pages and PDFs."
    )
    parser.add_argument(
        "--timeout", type=int, default=20,
        help="HTTP request timeout in seconds (default: 20)."
    )

    args = parser.parse_args()

    # Determine files to process
    if args.files:
        files = []
        for f_arg in args.files:
            f_path = Path(f_arg)
            if '*' in f_arg or '?' in f_arg:
                # Handle unexpanded glob patterns
                parent = f_path.parent if str(f_path.parent) != '' else Path('.')
                matched = sorted(parent.glob(f_path.name))
                files.extend(m.resolve() for m in matched if m.is_file())
            elif f_path.is_file():
                files.append(f_path.resolve())
    else:
        research_dir = REPO_ROOT / "docs" / "research"
        files = sorted(research_dir.glob("*flash*.md"))

    fetcher = SourceFetcher(
        cache_dir=args.cache_dir,
        timeout=args.timeout,
        use_cache=not args.no_cache
    )

    results_by_file: dict[str, list[dict]] = {}

    for file_path in files:
        if not file_path.is_file():
            continue
        entries = parse_markdown_entries(file_path)
        file_results = []
        for entry in entries:
            for url in entry.urls:
                res = verify_entry_url(entry, url, fetcher)
                file_results.append(res)
        results_by_file[str(file_path)] = file_results

    if args.json:
        json_output = {
            "metadata": {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "total_files": len(results_by_file),
                "total_urls": sum(len(r) for r in results_by_file.values())
            },
            "results": results_by_file
        }
        print(json.dumps(json_output, indent=2, ensure_ascii=False))
    else:
        cmd_str = "python3 " + " ".join(sys.argv)
        print(generate_markdown_report(results_by_file, command_str=cmd_str))

    # Always exit 0 (this is an informative report, not a test suite)
    sys.exit(0)


if __name__ == "__main__":
    main()
