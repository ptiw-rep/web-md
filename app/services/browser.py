import logging
from playwright.async_api import async_playwright, Error as PlaywrightError
from app.config import get_settings
from app.utils.security import validate_url

logger = logging.getLogger(__name__)
settings = get_settings()

class BrowserService:
    async def fetch_page(self, url: str) -> dict[str, str]:
        validate_url(url)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
            )
            context = await browser.new_context(
                user_agent="md-exporter/2.0 (+https://yourdomain.com/bot)",
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()
            try:
                logger.info(f"Fetching: {url}")
                response = await page.goto(url, wait_until="networkidle", timeout=settings.playwright_timeout_ms)
                if not response or not response.ok:
                    raise PlaywrightError(f"HTTP {response.status if response else 'Unknown'}")
                    
                html = await page.content()
                if len(html.encode()) > settings.max_page_size_mb * 1024 * 1024:
                    raise PlaywrightError("Page exceeds maximum size limit")
                    
                return {"html": html, "title": await page.title(), "final_url": page.url}
            finally:
                await context.close()
                await browser.close()