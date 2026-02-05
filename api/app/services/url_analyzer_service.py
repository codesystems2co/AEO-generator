"""Fetch and parse a URL for meta tags and content (external SEO data)."""
import re
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.schemas import URLAnalyzeResponse


USER_AGENT = "AEO-SEO-Generator/1.0 (Compatible; Analysis Bot)"


def _normalize_url(url: str) -> str:
    s = url.strip()
    if s and not s.startswith(("http://", "https://")):
        s = "https://" + s
    return s


def _text_from_soup(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def analyze_url(url: str) -> URLAnalyzeResponse:
    url = _normalize_url(url)
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        return URLAnalyzeResponse(
            url=url,
            h1_list=[],
            headings=[],
            word_count=0,
            status_code=getattr(e.response, "status_code", None),
            error=str(e),
        )
    except Exception as e:
        return URLAnalyzeResponse(
            url=url,
            h1_list=[],
            headings=[],
            word_count=0,
            error=str(e),
        )

    title = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    meta_desc = None
    meta = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    if meta and meta.get("content"):
        meta_desc = meta["content"].strip()
    og_title = None
    og_desc = None
    for meta in soup.find_all("meta", property=re.compile(r"og:", re.I)):
        p = (meta.get("property") or "").lower()
        c = meta.get("content") or ""
        if p == "og:title":
            og_title = c.strip()
        elif p == "og:description":
            og_desc = c.strip()

    h1_list = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]
    headings = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        headings.append(tag.get_text(strip=True))

    body_text = _text_from_soup(soup)
    words = re.findall(r"\S+", body_text)
    word_count = len(words)

    return URLAnalyzeResponse(
        url=url,
        title=title,
        meta_description=meta_desc or og_desc,
        og_title=og_title or title,
        og_description=og_desc or meta_desc,
        h1_list=h1_list,
        headings=headings[:50],
        word_count=word_count,
        status_code=resp.status_code,
    )
