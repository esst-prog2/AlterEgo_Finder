"""Photo credits stored with a dataset (see face_pipeline.wikidata_pool).

Licences such as CC BY require the author and licence wherever a photo is shown.
Credits come from strangers on the internet, so callers must display them as plain
text, and only ``safe_source_url`` decides what may become a link.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Optional

ATTRIBUTION_FILENAME = "attribution.json"
_COMMONS_PAGE = re.compile(r"^https://commons\.wikimedia\.org/wiki/[^\s\"'<>]+$")


def load_attribution(dataset_dir: Path) -> Dict[str, dict]:
    """Credits by ``<person folder>/<file name>``; empty if the dataset records none."""
    path = Path(dataset_dir) / ATTRIBUTION_FILENAME
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("images", {})
    except (OSError, ValueError):
        return {}


def credit_for(credits: Optional[Dict[str, dict]], image_path) -> Optional[dict]:
    if not credits:
        return None
    path = Path(image_path)
    return credits.get(f"{path.parent.name}/{path.name}")


def safe_source_url(url: str) -> Optional[str]:
    """``url`` if it is a Wikimedia Commons page, otherwise None."""
    return url if _COMMONS_PAGE.match(url or "") else None
