"""Builds the optional public-figure pool: one licensed photo per person on the
committed list, fetched from Wikimedia Commons once, with attribution recorded.

Considerate and resumable: one request at a time with a gap between them, rate
limits honoured, and progress saved after every person. Requests name Wikimedia
files only; no query photo is involved at any point.
"""

from __future__ import annotations

import collections
import html.parser
import http.client
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Counter, Dict, List, Optional

import cv2
import numpy as np

from face_pipeline.attribution import ATTRIBUTION_FILENAME
from face_pipeline.detector import detect_face

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
IMAGE_URL_PREFIXES = ("https://upload.wikimedia.org/", "https://thumb.wikimedia.org/")
USER_AGENT = "AlterEgoFinder/1.0 (https://github.com/esst-prog2/AlterEgo_Finder)"
THUMBNAIL_WIDTH = 500
METADATA_BATCH = 50  # the API's limit on titles per request
REQUEST_GAP_S = 3  # Commons answered 429 at about 1 request/s, and not at this gap
REQUEST_TIMEOUT_S = 40
DEFAULT_RETRY_WAIT_S = 60
MAX_RETRY_WAIT_S = 300
MAX_CONSECUTIVE_FAILURES = 5
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_AUTHOR_CHARS = 200

_ALLOWED_LICENSE = re.compile(r"^(CC0|Public domain|CC BY(-SA)? \d.*)$", re.IGNORECASE)
_SAFE_FOLDER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.,'()\- ]*$")


class PoolError(Exception):
    """The build cannot continue; what it has so far is kept."""


class _TextOnly(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []
        self._hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._hidden += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._hidden:
            self._hidden -= 1

    def handle_data(self, data):
        if not self._hidden:
            self.parts.append(data)


def plain_text(raw_html: str) -> str:
    """Commons' author field is HTML written by anyone: keep only its text."""
    parser = _TextOnly()
    parser.feed(raw_html)
    parser.close()
    text = " ".join("".join(parser.parts).split())
    # Some Commons templates repeat the name in a hidden element.
    half = len(text) // 2
    if len(text) % 2 == 0 and text[:half] == text[half:]:
        text = text[:half]
    return text[:MAX_AUTHOR_CHARS]


def license_allowed(short_name: str) -> bool:
    return bool(_ALLOWED_LICENSE.match(short_name.strip()))


def _open(url: str, retried: bool = False):
    """One polite request. A 429 waits as told and retries once, then stops the build."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        return urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_S)
    except urllib.error.HTTPError as e:
        if e.code != 429:
            raise
        if retried:
            raise PoolError(
                "Wikimedia is rate limiting this build, so it stopped. What it has is "
                "kept: run the same command again later to continue."
            ) from e
        retry_after = (e.headers.get("Retry-After") or "") if e.headers else ""
        wait = int(retry_after) if retry_after.isdigit() else DEFAULT_RETRY_WAIT_S
        time.sleep(min(wait, MAX_RETRY_WAIT_S))
        return _open(url, retried=True)


def _fetch_metadata(titles: List[str]) -> Dict[str, dict]:
    """imageinfo per file title, for one batch of titles."""
    query = urllib.parse.urlencode({
        "action": "query", "format": "json", "prop": "imageinfo",
        "iiprop": "url|extmetadata", "iiurlwidth": THUMBNAIL_WIDTH,
        "titles": "|".join(f"File:{t}" for t in titles),
    })
    time.sleep(REQUEST_GAP_S)
    with _open(f"{COMMONS_API}?{query}") as response:
        body = json.load(response)["query"]
    # Commons normalises titles (e.g. first letter, underscores); map them back.
    renamed = {n["to"]: n["from"] for n in body.get("normalized", [])}
    info = {}
    for page in body["pages"].values():
        if page.get("imageinfo"):
            title = renamed.get(page["title"], page["title"])
            info[title[len("File:"):]] = page["imageinfo"][0]
    return info


def _load_state(pool_dir: Path) -> dict:
    path = pool_dir / ATTRIBUTION_FILENAME
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"images": {}, "skipped": {}}


def _save_state(pool_dir: Path, state: dict) -> None:
    pool_dir.mkdir(parents=True, exist_ok=True)
    path = pool_dir / ATTRIBUTION_FILENAME
    part = path.with_name(path.name + ".part")
    part.write_text(json.dumps(state, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(part, path)


def _as_jpeg(data: bytes, image: np.ndarray) -> bytes:
    if data.startswith(b"\xff\xd8"):
        return data
    ok, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ok:
        raise ValueError("could not encode image")
    return buffer.tobytes()


def _judge_metadata(info: Optional[dict]) -> Optional[str]:
    """Why this image cannot be used, judged before downloading it; None if fine."""
    if info is None:
        return "no_metadata"
    meta = info.get("extmetadata", {})
    if not license_allowed(meta.get("LicenseShortName", {}).get("value", "")):
        return "licence"
    if not plain_text(meta.get("Artist", {}).get("value", "")):
        return "author"
    if not info.get("thumburl", "").startswith(IMAGE_URL_PREFIXES):
        return "host"
    return None


def _download(url: str) -> Optional[bytes]:
    """The image's bytes, or None if it is over the size limit."""
    time.sleep(REQUEST_GAP_S)
    with _open(url) as response:
        data = response.read(MAX_IMAGE_BYTES + 1)
    return None if len(data) > MAX_IMAGE_BYTES else data


def build_pool(people: List[dict], pool_dir: Path, limit: int) -> Counter:
    """Fetch images for ``people`` in order until ``pool_dir`` holds ``limit``.

    Returns counts for this run: ``saved``, ``fetch_failed`` and ``skipped_<reason>``.
    People already saved or rejected on an earlier run are not fetched again.
    Raises ``PoolError`` if it has to stop; progress is saved either way.
    """
    state = _load_state(pool_dir)
    stats: Counter = collections.Counter()
    failures = 0

    def relative(person: dict) -> str:
        return f"{person['folder']}/{person['folder']}_0001.jpg"

    # Someone taken off the list leaves the pool. Only images this build recorded
    # are removed, never anything else in the folder.
    listed = {relative(p) for p in people}
    for image in [i for i in state["images"] if i not in listed]:
        path = pool_dir / image
        path.unlink(missing_ok=True)
        if path.parent.is_dir() and not any(path.parent.iterdir()):
            path.parent.rmdir()
        del state["images"][image]
        stats["removed"] += 1
    if stats["removed"]:
        _save_state(pool_dir, state)

    pending = [
        p for p in people
        if relative(p) not in state["images"] and p["qid"] not in state["skipped"]
    ]
    position = 0
    while len(state["images"]) < limit and position < len(pending):
        batch = pending[position: position + METADATA_BATCH]
        position += METADATA_BATCH
        try:
            metadata = _fetch_metadata([p["file"] for p in batch])
        except (OSError, http.client.HTTPException, ValueError, KeyError) as e:
            raise PoolError(f"Could not reach Wikimedia ({e}). Run the same command again to continue.") from e

        for person in batch:
            if len(state["images"]) >= limit:
                break
            if not _SAFE_FOLDER.match(person["folder"]):
                raise PoolError(f"Unsafe folder name in the list: {person['folder']}")

            info = metadata.get(person["file"])
            reason = _judge_metadata(info)
            image = data = None
            if reason is None:
                try:
                    data = _download(info["thumburl"])
                except (OSError, http.client.HTTPException) as e:
                    stats["fetch_failed"] += 1
                    failures += 1
                    if failures >= MAX_CONSECUTIVE_FAILURES:
                        raise PoolError(
                            f"Repeated network failures ({e}). What the build has is kept: "
                            "run the same command again to continue."
                        ) from e
                    continue
                failures = 0
                if data is None:
                    reason = "too_large"
                else:
                    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if image is None:
                        reason = "undecodable"
                    elif detect_face(image) is None:
                        reason = "no_face"

            if reason is not None:
                stats[f"skipped_{reason}"] += 1
                state["skipped"][person["qid"]] = reason
                _save_state(pool_dir, state)
                continue

            destination = pool_dir / relative(person)
            destination.parent.mkdir(parents=True, exist_ok=True)
            part = destination.with_name(destination.name + ".part")
            part.write_bytes(_as_jpeg(data, image))
            os.replace(part, destination)
            meta = info["extmetadata"]
            state["images"][relative(person)] = {
                "name": person["name"],
                "author": plain_text(meta["Artist"]["value"]),
                "license": meta["LicenseShortName"]["value"].strip(),
                "source": info.get("descriptionurl", ""),
            }
            _save_state(pool_dir, state)
            stats["saved"] += 1
            print(f"  {len(state['images'])}/{limit} {person['folder']}", flush=True)
    return stats
