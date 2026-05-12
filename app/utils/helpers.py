import re
from urllib.parse import urlparse

def sanitize_folder_name(url: str, max_len: int = 50) -> str:
    """
    Convert URL to safe folder name.
    
    Examples:
    - https://example.com/page → example-com-page
    - https://httpbin.org/html → httpbin-org-html
    """
    parsed = urlparse(url)
    # Combine domain + path, remove scheme
    name = parsed.netloc + parsed.path.rstrip("/")
    # Replace non-alphanumeric with hyphens
    name = re.sub(r"[^\w\-.]", "-", name)
    # Collapse multiple hyphens
    name = re.sub(r"-+", "-", name)
    # Trim and lowercase
    name = name.strip("-").lower()
    # Truncate + add hash if needed to avoid collisions
    if len(name) > max_len:
        import hashlib
        hash_suffix = hashlib.md5(url.encode()).hexdigest()[:8]
        name = f"{name[:max_len-9]}-{hash_suffix}"
    return name or "page"