# app/routes/batch.py
import asyncio
import io
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from app.services.browser import BrowserService
from app.services.images import collect_images, download_images
from app.services.converter import html_to_markdown
from app.services.packager import build_batch_zip
from app.utils.helpers import sanitize_folder_name
from app.auth import verify_api_key
from app.config import get_settings, Settings

router = APIRouter()
logger = logging.getLogger(__name__)


class BatchRequest(BaseModel):
    urls: list[str] = Field(..., min_items=1, description="List of URLs to convert")
    
    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: list[str]) -> list[str]:
        for url in v:
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"URL must start with http:// or https://: {url}")
        return v


@router.post("/convert/batch")
async def convert_batch(
    request: BatchRequest = Body(...),
    _token: str = Depends(verify_api_key),
    settings: Settings = Depends(get_settings)  # ← Inject settings
):
    """
    Convert multiple webpages to Markdown in a single ZIP.
    
    Each page gets its own folder: `<sanitized-name>/<name>.md + static/`
    Includes INDEX.md with summary and links.
    """
    urls = request.urls
    
    # ✅ Validate against config (dynamic, not hardcoded)
    if len(urls) > settings.batch_max_urls:
        raise HTTPException(
            400, 
            detail=f"Too many URLs: {len(urls)} > max {settings.batch_max_urls}. "
                   f"Adjust BATCH_MAX_URLS in .env or split your request."
        )
    
    # Process URLs concurrently with semaphore
    semaphore = asyncio.Semaphore(settings.batch_concurrency)
    browser = BrowserService()
    
    async def process_one(url: str) -> dict | None:
        async with semaphore:
            try:
                logger.info(f"Batch: Processing {url}")
                page_data = await browser.fetch_page(
                    url, 
                    timeout_ms=settings.batch_timeout_per_url_s * 1000
                )
                
                images = collect_images(page_data["final_url"], page_data["html"])
                image_blobs = await download_images(images)
                markdown = html_to_markdown(
                    page_data["html"], 
                    page_data["final_url"], 
                    images
                )
                markdown = f"# {page_data['title']}\n\n> **URL:** <{page_data['final_url']}>\n\n{markdown}"
                
                folder = sanitize_folder_name(url)
                
                return {
                    "folder_name": folder,
                    "original_url": url,
                    "title": page_data["title"],
                    "markdown": markdown,
                    "images": image_blobs,
                }
            except Exception as e:
                logger.warning(f"Batch: Failed {url}: {e}")
                return {"error": str(e), "url": url}
    
    tasks = [process_one(url) for url in urls]
    raw_results = await asyncio.gather(*tasks)
    
    results = [r for r in raw_results if r and "error" not in r]
    errors = [
        {"url": r["url"], "error": r["error"]} 
        for r in raw_results 
        if r and "error" in r
    ]
    
    if not results and errors:
        raise HTTPException(
            502,
            detail=f"All URLs failed: {[e['error'] for e in errors]}"
        )
    
    zip_bytes = build_batch_zip(results, errors)
    zip_filename = f"batch_export_{len(results)}_pages.zip"
    
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'}
    )