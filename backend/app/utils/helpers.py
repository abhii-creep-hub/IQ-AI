import logging
from typing import Any


def format_file_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def paginate_list(items: list, page: int = 1, size: int = 10) -> dict[str, Any]:
    start = (page - 1) * size
    end = start + size
    return {
        "items": items[start:end],
        "total": len(items),
        "page": page,
        "size": size,
        "pages": (len(items) + size - 1) // size,
    }


def sanitize_filename(filename: str) -> str:
    import re
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename.strip('. ')
    return filename[:255]
