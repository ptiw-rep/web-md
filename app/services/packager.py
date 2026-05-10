import io
import zipfile

def build_zip(md_filename: str, markdown: str, image_blobs: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(md_filename, markdown.encode("utf-8"))
        for name, data in image_blobs.items():
            zf.writestr(f"static/{name}", data)
    return buf.getvalue()