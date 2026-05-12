import io
import zipfile
from datetime import datetime

def build_zip(md_filename: str, markdown: str, image_blobs: dict[str, bytes]) -> bytes:
    """Build ZIP for single page."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(md_filename, markdown.encode("utf-8"))
        for name, data in image_blobs.items():
            zf.writestr(f"static/{name}", data)
    return buf.getvalue()


def build_batch_zip(results: list[dict], errors: list[dict]) -> bytes:
    """
    Build ZIP for batch processing.
    
    Structure:
    batch_export_YYYYMMDD_HHMMSS.zip
    ├── INDEX.md                          # Summary with links + errors
    ├── example-com/
    │   ├── example-com.md
    │   └── static/
    │       ├── img1.jpg
    │       └── img2.png
    ├── httpbin-org/
    │   ├── httpbin-org.md
    │   └── static/
    │       └── logo.png
    └── ...
    """
    buf = io.BytesIO()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. Write INDEX.md summary
        index_content = _build_index_md(results, errors, timestamp)
        zf.writestr("INDEX.md", index_content.encode("utf-8"))
        
        # 2. Write each page's folder
        for result in results:
            folder = result["folder_name"]
            zf.writestr(f"{folder}/{folder}.md", result["markdown"].encode("utf-8"))
            for img_name, img_data in result["images"].items():
                zf.writestr(f"{folder}/static/{img_name}", img_data)
        
        # 3. Optional: Write errors.log if any failures
        if errors:
            error_log = "\n".join([f"{e['url']}: {e['error']}" for e in errors])
            zf.writestr("ERRORS.log", error_log.encode("utf-8"))
    
    return buf.getvalue()


def _build_index_md(results: list[dict], errors: list[dict], timestamp: str) -> str:
    """Generate INDEX.md with links to each page and error summary."""
    lines = [
        f"# Batch Export Summary",
        f"",
        f"**Generated:** `{timestamp}`",
        f"**Total URLs:** {len(results) + len(errors)}",
        f"**Successful:** {len(results)}",
        f"**Failed:** {len(errors)}",
        f"",
        f"---",
        f"",
        f"## ✅ Successful Conversions",
        f"",
    ]
    
    for r in results:
        # Markdown link: [Title](folder/folder.md)
        lines.append(f"- [{r['title']}]({r['folder_name']}/{r['folder_name']}.md)  ")
        lines.append(f"  - Source: `{r['original_url']}`  ")
        lines.append(f"  - Images: {len(r['images'])}  ")
        lines.append("")
    
    if errors:
        lines.extend([
            f"---",
            f"",
            f"## ❌ Failed Conversions",
            f"",
        ])
        for e in errors:
            lines.append(f"- `{e['url']}`: {e['error']}  ")
        lines.append("")
    
    lines.extend([
        f"---",
        f"",
        f"> 💡 Tip: Open any `.md` file in a Markdown viewer. Images are in each page's `static/` folder.",
    ])
    
    return "\n".join(lines)