import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from markdownify import markdownify as md

def html_to_markdown(html: str, base_url: str, images: list[dict]) -> str:
    soup = BeautifulSoup(html, "html.parser")
    src_map = {img["src_abs"]: f"static/{img['local_name']}" for img in images if img.get("local_name")}

    for tag in soup.find_all("img"):
        raw = tag.get("src") or ""
        if raw.startswith("data:"):
            tag.decompose()
            continue
        abs_src = urljoin(base_url, raw)
        if abs_src in src_map:
            tag["src"] = src_map[abs_src]

    for noise in soup.select("script, style, noscript, iframe, svg"):
        noise.decompose()

    markdown = md(str(soup), heading_style="ATX", bullets="-", newline_style="backslash")
    return re.sub(r"\n{3,}", "\n\n", markdown).strip()