import io
import re
import logging
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from fastapi.responses import StreamingResponse
from app.services.browser import BrowserService
from app.services.images import collect_images, download_images
from app.services.converter import html_to_markdown
from app.services.packager import build_zip

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/convert")
async def convert_get(url: str = Query(..., description="URL to convert")):
    return await _process(url)

@router.post("/convert")
async def convert_post(url: str = Body(..., embed=True, description="URL to convert")):
    return await _process(url)

async def _process(url: str):
    browser = BrowserService()
    try:
        page_data = await browser.fetch_page(url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Page fetch failed: {e}")
        raise HTTPException(502, detail=f"Failed to load page: {e}")

    images = collect_images(page_data["final_url"], page_data["html"])
    image_blobs = await download_images(images)
    markdown = html_to_markdown(page_data["html"], page_data["final_url"], images)
    markdown = f"# {page_data['title']}\n\n> **URL:** <{page_data['final_url']}>\n\n{markdown}"

    stem = re.sub(r"[^\w\-.]", "_", url.replace("https://", "").replace("http://", "").strip("/"))
    md_filename = f"{stem or 'page'}.md"
    zip_bytes = build_zip(md_filename, markdown, image_blobs)

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{stem or "page"}.zip"'}
    )