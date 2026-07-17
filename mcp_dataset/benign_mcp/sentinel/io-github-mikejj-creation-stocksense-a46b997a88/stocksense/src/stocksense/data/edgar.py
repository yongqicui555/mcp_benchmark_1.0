"""SEC EDGAR API client for filings and insider trades."""

import gzip
import time
import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from stocksense.data.cache import cik_cache, filings_cache

HEADERS = {
    "User-Agent": "StockSense contact@stocksense.dev",
    "Accept-Encoding": "gzip, deflate",
}

REQUEST_DELAY = 0.12  # EDGAR limit: 10 req/sec

_last_request_time = 0.0


def _edgar_get(url: str) -> bytes:
    """Make a rate-limited request to EDGAR. Returns response bytes."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < REQUEST_DELAY:
        time.sleep(REQUEST_DELAY - elapsed)

    req = Request(url)
    for k, v in HEADERS.items():
        req.add_header(k, v)

    try:
        with urlopen(req, timeout=30) as resp:
            _last_request_time = time.time()
            data = resp.read()
            # Decompress gzip if needed
            if data[:2] == b"\x1f\x8b":
                data = gzip.decompress(data)
            return data
    except (HTTPError, URLError) as e:
        raise RuntimeError(f"EDGAR request failed for {url}: {e}") from e


def _edgar_json(url: str) -> dict:
    """Fetch JSON from EDGAR."""
    import json
    return json.loads(_edgar_get(url))


def _build_cik_map() -> dict[str, str]:
    """Fetch ticker → CIK mapping. Cached for 24 hours."""
    cached = cik_cache.get("cik_map")
    if cached is not None:
        return cached

    data = _edgar_json("https://www.sec.gov/files/company_tickers.json")
    cik_map = {}
    for entry in data.values():
        ticker = entry["ticker"].upper()
        cik = str(entry["cik_str"]).zfill(10)
        cik_map[ticker] = cik

    cik_cache.set("cik_map", cik_map)
    return cik_map


def _resolve_cik(ticker: str) -> str:
    """Resolve a ticker to its 10-digit CIK string."""
    cik_map = _build_cik_map()
    ticker_upper = ticker.upper().replace("-", ".")
    cik = cik_map.get(ticker_upper)
    if cik is None:
        raise ValueError(f"Ticker '{ticker}' not found in SEC EDGAR")
    return cik


def fetch_filings(
    ticker: str,
    form_type: str = "10-K",
    limit: int = 10,
) -> list[dict]:
    """Fetch recent SEC filings metadata for a ticker.

    Returns list of dicts with: filing_date, accession_number, form_type,
    primary_document, items (for 8-K).
    """
    cache_key = f"filings:{ticker}:{form_type}:{limit}"
    cached = filings_cache.get(cache_key)
    if cached is not None:
        return cached

    cik = _resolve_cik(ticker)
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    data = _edgar_json(url)

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])
    items_list = recent.get("items", [])

    form_type_upper = form_type.upper()
    results = []
    for i, form in enumerate(forms):
        if form.upper() != form_type_upper:
            continue
        entry = {
            "filing_date": dates[i] if i < len(dates) else None,
            "accession_number": accessions[i] if i < len(accessions) else None,
            "form_type": form,
            "primary_document": primary_docs[i] if i < len(primary_docs) else None,
        }
        if form_type_upper == "8-K" and i < len(items_list):
            entry["items"] = items_list[i]
        results.append(entry)
        if len(results) >= limit:
            break

    filings_cache.set(cache_key, results)
    return results


def fetch_filing_document(ticker: str, accession_number: str) -> str:
    """Fetch the primary document text for a specific filing.

    Returns the document content as text, truncated to ~50k chars for LLM context.
    """
    cik = _resolve_cik(ticker)
    # Get filing metadata to find primary document filename
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    data = _edgar_json(url)

    recent = data.get("filings", {}).get("recent", {})
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])

    primary_doc = None
    for i, acc in enumerate(accessions):
        if acc == accession_number and i < len(primary_docs):
            primary_doc = primary_docs[i]
            break

    if primary_doc is None:
        raise ValueError(
            f"Filing {accession_number} not found for ticker '{ticker}'"
        )

    accession_clean = accession_number.replace("-", "")
    cik_num = str(int(cik))
    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{accession_clean}/{primary_doc}"
    raw = _edgar_get(doc_url).decode("utf-8", errors="replace")

    # Strip HTML tags for cleaner LLM consumption
    from html.parser import HTMLParser

    class _TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self._parts: list[str] = []

        def handle_data(self, data: str):
            self._parts.append(data)

        def get_text(self) -> str:
            return " ".join(self._parts)

    extractor = _TextExtractor()
    extractor.feed(raw)
    text = extractor.get_text()

    # Collapse whitespace
    import re
    text = re.sub(r"\s+", " ", text).strip()

    max_chars = 50_000
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n\n[Truncated — showing first {max_chars:,} of {len(text):,} characters]"

    return text


def fetch_insider_trades(ticker: str, limit: int = 20) -> list[dict]:
    """Fetch recent insider trades (Form 4) for a ticker.

    Returns list of dicts with: filing_date, insider_name, title,
    relationship, transaction_type, shares, price_per_share, value,
    transaction_date.
    """
    cache_key = f"insider:{ticker}:{limit}"
    cached = filings_cache.get(cache_key)
    if cached is not None:
        return cached

    cik = _resolve_cik(ticker)
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    data = _edgar_json(url)

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])

    # Collect Form 4 filings
    form4s = []
    for i, form in enumerate(forms):
        if form not in ("4", "4/A"):
            continue
        form4s.append({
            "filing_date": dates[i] if i < len(dates) else None,
            "accession": accessions[i] if i < len(accessions) else None,
            "primary_doc": primary_docs[i] if i < len(primary_docs) else None,
        })
        if len(form4s) >= limit:
            break

    # Parse each Form 4 XML
    trades = []
    cik_num = str(int(cik))
    for f4 in form4s:
        accession_clean = f4["accession"].replace("-", "")
        doc_name = f4["primary_doc"]
        # Strip XSLT prefix if present
        if "/" in doc_name:
            doc_name = doc_name.split("/")[-1]

        xml_url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{accession_clean}/{doc_name}"
        try:
            xml_bytes = _edgar_get(xml_url)
            parsed = _parse_form4_xml(xml_bytes, f4["filing_date"])
            trades.extend(parsed)
        except Exception:
            continue

    filings_cache.set(cache_key, trades)
    return trades


def _xml_text(element, tag: str) -> str | None:
    """Extract text from <tag><value>text</value></tag> or <tag>text</tag>."""
    node = element.find(tag)
    if node is None:
        return None
    # Try <value> child first
    value_node = node.find("value")
    if value_node is not None and value_node.text:
        return value_node.text.strip()
    if node.text:
        return node.text.strip()
    return None


def _parse_form4_xml(xml_bytes: bytes, filing_date: str) -> list[dict]:
    """Parse a Form 4 XML document into transaction records."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []

    # Extract insider info
    owner = root.find(".//reportingOwner")
    if owner is None:
        return []

    insider_name = _xml_text(owner, ".//rptOwnerName") or "Unknown"
    officer_title = _xml_text(owner, ".//officerTitle") or ""

    rel = owner.find(".//reportingOwnerRelationship")
    if rel is not None:
        is_officer = (_xml_text(rel, "isOfficer") or "") == "1"
        is_director = (_xml_text(rel, "isDirector") or "") == "1"
        is_ten_pct = (_xml_text(rel, "isTenPercentOwner") or "") == "1"
        if is_officer:
            relationship = "officer"
        elif is_director:
            relationship = "director"
        elif is_ten_pct:
            relationship = "10pct_owner"
        else:
            relationship = "other"
    else:
        relationship = "other"

    trades = []
    for txn in root.findall(".//nonDerivativeTransaction"):
        code = _xml_text(txn, ".//transactionCoding/transactionCode")
        if code not in ("P", "S"):
            continue

        shares_str = _xml_text(txn, ".//transactionAmounts/transactionShares")
        price_str = _xml_text(txn, ".//transactionAmounts/transactionPricePerShare")
        txn_date_str = _xml_text(txn, ".//transactionDate")

        try:
            shares = float(shares_str) if shares_str else 0
        except ValueError:
            shares = 0
        if shares <= 0:
            continue

        try:
            price = round(float(price_str), 2) if price_str else 0
        except ValueError:
            price = 0

        trades.append({
            "filing_date": filing_date,
            "transaction_date": txn_date_str,
            "insider_name": insider_name,
            "title": officer_title,
            "relationship": relationship,
            "transaction_type": "buy" if code == "P" else "sell",
            "shares": int(shares),
            "price_per_share": price,
            "value": round(shares * price, 2),
        })

    return trades
