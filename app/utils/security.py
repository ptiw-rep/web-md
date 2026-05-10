import re
from urllib.parse import urlparse
from fastapi import HTTPException
from app.config import get_settings

def validate_url(url: str) -> None:
    settings = get_settings()
    try:
        parsed = urlparse(url)
        if not parsed.scheme or parsed.scheme not in ("http", "https"):
            raise ValueError("Only HTTP/HTTPS schemes allowed")
        if not parsed.netloc:
            raise ValueError("Missing domain")

        hostname = parsed.hostname or ""
        if re.match(r"^(?:127\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|0\.0\.0\.0|localhost)", hostname):
            raise HTTPException(403, detail="Internal/private domains not allowed (SSRF protection)")

        domain = parsed.netloc.lower()
        
        # ✅ Use the parsed set properties
        if settings.allowed_domains_set and not any(domain.endswith(d) for d in settings.allowed_domains_set):
            raise HTTPException(403, detail=f"Domain not in allowed list: {domain}")
        if settings.blocked_domains_set and any(domain.endswith(d) for d in settings.blocked_domains_set):
            raise HTTPException(403, detail=f"Domain blocked: {domain}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=f"Invalid URL: {e}")