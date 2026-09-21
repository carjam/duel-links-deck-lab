"""Downloads and caches card art, for embedding into a rendered deck page.

Images are cached to disk once (keyed by card_id) so re-rendering the same
deck doesn't re-download anything, then base64-embedded as a data URI so the
rendered HTML is a single self-contained file -- safe to move, email, or
open directly via ``file://`` without any relative-path or CORS issues.
"""

from __future__ import annotations

import base64
import os

import requests

DEFAULT_IMAGE_CACHE_DIR = os.path.expanduser("~/.cache/dl-deck-lab/card-images")


def get_cached_image_path(card_id: str, image_url: str, cache_dir: str = DEFAULT_IMAGE_CACHE_DIR) -> str:
    """Downloads ``image_url`` to ``cache_dir`` if not already cached, and
    returns the local file path either way."""
    os.makedirs(cache_dir, exist_ok=True)
    ext = os.path.splitext(image_url)[1] or ".jpg"
    path = os.path.join(cache_dir, f"{card_id}{ext}")
    if not os.path.exists(path):
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        with open(path, "wb") as f:
            f.write(response.content)
    return path


def to_data_uri(image_path: str) -> str:
    ext = os.path.splitext(image_path)[1].lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{encoded}"
