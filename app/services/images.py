import asyncio
import hashlib
import mimetypes
from pathlib import Path
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from app.config import get_settings

settings = get_settings()

def collect_images(base_url: str, html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    seen, images = set(), []
    for tag in soup.find_all("img"):
        src = tag.get("src") or tag.get("data-src") or tag.get("data-lazy-src") or ""
        if not src or src.startswith("data:"):
            continue
        abs_src = urljoin(base_url, src)
        if abs_src not in seen:
            seen.add(abs_src)
            images.append({"src_abs": abs_src, "alt": tag.get("alt", ""), "local_name": None})
        if len(images) >= settings.max_images:
            break
    return images

async def download_images(images: list[dict]) -> dict[str, bytes]:
    used_names: set[str] = set()
    blobs: dict[str, bytes] = {}

    async def _download(client: httpx.AsyncClient, img: dict) -> tuple[str | None, bytes | None]:
        try:
            r = await client.get(img["src_abs"], timeout=settings.image_download_timeout_s, follow_redirects=True)
            r.raise_for_status()
            if len(r.content) > settings.max_image_size_mb * 1024 * 1024:
                return None, None

            ct = r.headers.get("content-type", "")
            path = Path(urlparse(img["src_abs"]).path).name.split("?")[0]
            ext = mimetypes.guess_extension(ct.split(";")[0].strip()) or ".img"
            name = path if "." in path else f"{hashlib.md5(img['src_abs'].encode()).hexdigest()[:12]}{ext}"

            if name in used_names:
                stem = name.rsplit(".", 1)[0]
                ext = name.rsplit(".", 1)[1] if "." in name else "img"
                name = f"{stem}_{hashlib.md5(img['src_abs'].encode()).hexdigest()[:6]}.{ext}"
            used_names.add(name)
            img["local_name"] = name
            return name, r.content
        except Exception:
            return None, None

    async with httpx.AsyncClient(follow_redirects=True, headers={"User-Agent": "md-exporter/2.0"}) as client:
        results = await asyncio.gather(*[_download(client, img) for img in images])

    for name, data in results:
        if name and data:
            blobs[name] = data
    return blobs