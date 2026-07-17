"""SEO analyzer — meta tags, headings, images, links, structured data."""

import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup


def analyze_seo(url: str, resp, soup: BeautifulSoup) -> dict:
    """Run comprehensive SEO analysis on a page."""
    issues = []
    warnings = []
    passed = []

    # Title tag
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None
    if not title:
        issues.append("Missing <title> tag")
    elif len(title) < 30:
        warnings.append(f"Title too short ({len(title)} chars, recommend 50-60)")
    elif len(title) > 60:
        warnings.append(f"Title too long ({len(title)} chars, recommend 50-60)")
    else:
        passed.append(f"Title length OK ({len(title)} chars)")

    # Meta description
    meta_desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    meta_desc = meta_desc_tag.get("content", "").strip() if meta_desc_tag else None
    if not meta_desc:
        issues.append("Missing meta description")
    elif len(meta_desc) < 120:
        warnings.append(f"Meta description short ({len(meta_desc)} chars, recommend 150-160)")
    elif len(meta_desc) > 160:
        warnings.append(f"Meta description too long ({len(meta_desc)} chars, recommend 150-160)")
    else:
        passed.append(f"Meta description length OK ({len(meta_desc)} chars)")

    # H1 tags
    h1_tags = soup.find_all("h1")
    if len(h1_tags) == 0:
        issues.append("No <h1> tag found")
    elif len(h1_tags) > 1:
        warnings.append(f"Multiple <h1> tags ({len(h1_tags)}) — recommend exactly 1")
    else:
        passed.append("Single <h1> tag present")

    # Heading hierarchy
    headings = soup.find_all(re.compile(r"^h[1-6]$"))
    heading_structure = [{"tag": h.name, "text": h.get_text(strip=True)[:80]} for h in headings[:20]]

    # Images without alt
    images = soup.find_all("img")
    imgs_no_alt = [img.get("src", "")[:60] for img in images if not img.get("alt")]
    if images:
        alt_ratio = (len(images) - len(imgs_no_alt)) / len(images) * 100
        if len(imgs_no_alt) > 0:
            warnings.append(f"{len(imgs_no_alt)}/{len(images)} images missing alt text ({alt_ratio:.0f}% have alt)")
        else:
            passed.append(f"All {len(images)} images have alt text")
    else:
        passed.append("No images on page")

    # Links analysis
    all_links = soup.find_all("a", href=True)
    parsed_url = urlparse(url)
    internal_links = []
    external_links = []
    for a in all_links:
        href = a.get("href", "")
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full_url = urljoin(url, href)
        link_domain = urlparse(full_url).netloc
        if link_domain == parsed_url.netloc:
            internal_links.append(full_url)
        else:
            external_links.append(full_url)

    if len(internal_links) < 3:
        warnings.append(f"Few internal links ({len(internal_links)}) — add more for better crawlability")

    # Canonical URL
    canonical = soup.find("link", rel="canonical")
    canonical_url = canonical.get("href") if canonical else None
    if canonical_url:
        passed.append(f"Canonical URL set: {canonical_url[:60]}")
    else:
        warnings.append("No canonical URL — may cause duplicate content issues")

    # Open Graph tags
    og_tags = soup.find_all("meta", property=re.compile(r"^og:"))
    og_data = {tag.get("property"): tag.get("content", "")[:80] for tag in og_tags}
    if "og:title" in og_data and "og:description" in og_data:
        passed.append("Open Graph tags present (og:title, og:description)")
    else:
        warnings.append("Missing Open Graph tags — social sharing won't look good")

    # Twitter Card
    twitter_tags = soup.find_all("meta", attrs={"name": re.compile(r"^twitter:")})
    if twitter_tags:
        passed.append("Twitter Card meta tags present")

    # Mobile viewport
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if viewport:
        passed.append("Mobile viewport meta tag present")
    else:
        issues.append("Missing viewport meta tag — page won't be mobile-friendly")

    # Robots meta
    robots_meta = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    robots_content = robots_meta.get("content", "") if robots_meta else None
    if robots_content and "noindex" in robots_content.lower():
        warnings.append(f"Page has noindex directive: {robots_content}")

    # Language attribute
    html_tag = soup.find("html")
    lang = html_tag.get("lang") if html_tag else None
    if lang:
        passed.append(f"Language attribute set: {lang}")
    else:
        warnings.append("Missing lang attribute on <html> tag")

    # Structured data (JSON-LD)
    json_ld = soup.find_all("script", type="application/ld+json")
    if json_ld:
        passed.append(f"{len(json_ld)} JSON-LD structured data block(s) found")
    else:
        warnings.append("No JSON-LD structured data — add for rich search results")

    # Favicon
    favicon = soup.find("link", rel=re.compile(r"icon", re.I))
    if favicon:
        passed.append("Favicon found")
    else:
        warnings.append("No favicon link tag found")

    # Word count
    text = soup.get_text(separator=" ", strip=True)
    word_count = len(text.split())
    if word_count < 300:
        warnings.append(f"Thin content ({word_count} words) — aim for 300+ for SEO")
    else:
        passed.append(f"Content length OK ({word_count} words)")

    # Calculate score
    max_score = 100
    score = max_score - (len(issues) * 10) - (len(warnings) * 3)
    score = max(0, min(100, score))

    return {
        "score": score,
        "issues_count": len(issues),
        "warnings_count": len(warnings),
        "passed_count": len(passed),
        "issues": issues,
        "warnings": warnings,
        "passed": passed,
        "details": {
            "title": title,
            "meta_description": meta_desc[:160] if meta_desc else None,
            "h1": [h.get_text(strip=True)[:80] for h in h1_tags],
            "headings_count": len(headings),
            "heading_structure": heading_structure[:10],
            "images_total": len(images),
            "images_missing_alt": len(imgs_no_alt),
            "internal_links": len(internal_links),
            "external_links": len(external_links),
            "canonical_url": canonical_url,
            "has_open_graph": bool(og_data),
            "has_twitter_card": bool(twitter_tags),
            "has_viewport": bool(viewport),
            "has_structured_data": bool(json_ld),
            "has_favicon": bool(favicon),
            "language": lang,
            "word_count": word_count,
        },
    }
