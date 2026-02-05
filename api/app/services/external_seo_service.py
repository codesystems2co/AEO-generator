"""External SEO APIs: Moz Links API and SEMrush (optional, require API keys)."""
from typing import Optional
import hashlib
import time
import requests

from app.config import settings
from app.schemas import ExternalSEOMozResponse, ExternalSEOSemrushResponse


def _moz_auth_header() -> Optional[str]:
    if settings.MOZ_API_TOKEN:
        return settings.MOZ_API_TOKEN
    if settings.MOZ_ACCESS_ID and settings.MOZ_SECRET_KEY:
        expires = int(time.time()) + 300
        s = settings.MOZ_ACCESS_ID + "\n" + str(expires)
        h = hashlib.sha1((settings.MOZ_SECRET_KEY + s).encode()).hexdigest()
        return ":".join([settings.MOZ_ACCESS_ID, str(expires), h])
    return None


def fetch_moz_metrics(url: str) -> ExternalSEOMozResponse:
    """Fetch Domain Authority / Page Authority from Moz Links API (v2)."""
    if not settings.moz_configured:
        return ExternalSEOMozResponse(
            url=url,
            available=False,
            message="Moz API not configured. Set MOZ_API_TOKEN or MOZ_ACCESS_ID and MOZ_SECRET_KEY.",
        )
    auth = _moz_auth_header()
    headers = {}
    if settings.MOZ_API_TOKEN:
        headers["x-moz-token"] = settings.MOZ_API_TOKEN
    else:
        headers["Authorization"] = "Bearer " + auth
    try:
        r = requests.get(
            "https://lsapi.seomoz.com/v2/url_metrics/" + requests.utils.quote(url, safe=""),
            params={"Cols": "103616137252"},
            headers=headers,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        return ExternalSEOMozResponse(
            url=url,
            available=True,
            message="OK",
            domain_authority=data.get("domain_authority"),
            page_authority=data.get("page_authority"),
            spam_score=data.get("spam_score"),
        )
    except requests.RequestException as e:
        return ExternalSEOMozResponse(
            url=url,
            available=True,
            message=f"Request failed: {e}",
        )
    except Exception as e:
        return ExternalSEOMozResponse(
            url=url,
            available=True,
            message=str(e),
        )


def fetch_semrush_overview(domain: str, database: str = "us") -> ExternalSEOSemrushResponse:
    """Fetch domain overview from SEMrush (organic traffic, keywords, rank)."""
    if not settings.semrush_configured:
        return ExternalSEOSemrushResponse(
            domain=domain,
            available=False,
            message="SEMrush API not configured. Set SEMRUSH_API_KEY.",
        )
    try:
        r = requests.get(
            "https://api.semrush.com/",
            params={
                "type": "domain_ranks",
                "key": settings.SEMRUSH_API_KEY,
                "domain": domain.strip(),
                "database": database,
            },
            timeout=10,
        )
        r.raise_for_status()
        body = r.text.strip()
        if not body:
            return ExternalSEOSemrushResponse(
                domain=domain,
                available=True,
                message="No data returned for domain.",
            )
        lines = body.split("\n")
        if len(lines) < 2:
            return ExternalSEOSemrushResponse(
                domain=domain,
                available=True,
                message="Parsed no rows.",
            )
        headers = [h.strip() for h in lines[0].split(";")]
        values = [v.strip() for v in lines[1].split(";")]
        row = dict(zip(headers, values))
        rank = None
        if "Rk" in row and row["Rk"].isdigit():
            rank = int(row["Rk"])
        return ExternalSEOSemrushResponse(
            domain=domain,
            available=True,
            message="OK",
            rank=rank,
            organic_traffic=None,
            organic_keywords=None,
        )
    except requests.RequestException as e:
        return ExternalSEOSemrushResponse(
            domain=domain,
            available=True,
            message=f"Request failed: {e}",
        )
    except Exception as e:
        return ExternalSEOSemrushResponse(
            domain=domain,
            available=True,
            message=str(e),
        )
