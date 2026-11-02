"""Tests for face_pipeline.wikidata_pool with a fake Wikimedia (no network)."""

import io
import json
import urllib.error
import urllib.parse
from email.message import Message
from pathlib import Path

import cv2
import numpy as np
import pytest

from face_pipeline import wikidata_pool as wp

FIXTURES = Path(__file__).parent / "fixtures"
FACE = (FIXTURES / "obama_1.jpg").read_bytes()
OTHER_FACE = (FIXTURES / "biden_1.jpg").read_bytes()
PNG_FACE = cv2.imencode(".png", cv2.imread(str(FIXTURES / "obama_2.jpg")))[1].tobytes()
BLANK = cv2.imencode(".jpg", np.full((300, 300, 3), 255, dtype=np.uint8))[1].tobytes()


def _person(i):
    return {"qid": f"Q{i}", "name": f"Person {i}", "folder": f"Person_{i}", "file": f"File {i}.jpg",
            "occupation": "actor", "sitelinks": 100 - i}


class _Response(io.BytesIO):
    def __init__(self, body):
        super().__init__(body)
        self.headers = {"Content-Length": str(len(body))}


class FakeWikimedia:
    """Answers the Commons API and image URLs; `files` overrides per file title."""

    def __init__(self):
        self.files = {}
        self.requests = []
        self.limit_next = 0
        self.retry_after = "7"

    def info(self, title):
        spec = {"license": "CC BY-SA 4.0", "artist": '<a href="https://x">Jane <b>Doe</b></a>',
                "body": FACE, "url": None, **self.files.get(title, {})}
        meta = {"LicenseShortName": {"value": spec["license"]}, "Artist": {"value": spec["artist"]}}
        if spec["license"] is None:
            del meta["LicenseShortName"]
        if spec["artist"] is None:
            del meta["Artist"]
        slug = urllib.parse.quote(title.replace(" ", "_"))
        return {"extmetadata": meta,
                "thumburl": spec["url"] or f"https://upload.wikimedia.org/thumb/{slug}/500px.jpg",
                "descriptionurl": f"https://commons.wikimedia.org/wiki/File:{slug}"}

    def urlopen(self, request, timeout=None):
        url = request.full_url
        assert request.get_header("User-agent", "").startswith("AlterEgoFinder")
        assert timeout
        self.requests.append(url)
        if self.limit_next:
            self.limit_next -= 1
            headers = Message()
            if self.retry_after:
                headers["Retry-After"] = self.retry_after
            raise urllib.error.HTTPError(url, 429, "Too Many Requests", headers, None)
        if url.startswith(wp.COMMONS_API):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            titles = [t[len("File:"):] for t in query["titles"][0].split("|")]
            pages = {str(i): {"title": f"File:{t}", "imageinfo": [self.info(t)]} for i, t in enumerate(titles)}
            return _Response(json.dumps({"query": {"pages": pages}}).encode())
        title = urllib.parse.unquote(url.split("/thumb/")[1].split("/")[0]).replace("_", " ")
        return _Response(self.files.get(title, {}).get("body", FACE))

    def image_requests(self):
        return [u for u in self.requests if "/thumb/" in u]


@pytest.fixture
def net(monkeypatch):
    fake = FakeWikimedia()
    monkeypatch.setattr(wp.urllib.request, "urlopen", fake.urlopen)
    fake.sleeps = []
    monkeypatch.setattr(wp.time, "sleep", fake.sleeps.append)
    return fake


def _state(pool):
    return json.loads((pool / "attribution.json").read_text(encoding="utf-8"))


def test_saves_images_with_attribution(tmp_path, net):
    pool = tmp_path / "wikidata"

    stats = wp.build_pool([_person(1), _person(2)], pool, limit=2)

    assert stats["saved"] == 2
    assert (pool / "Person_1" / "Person_1_0001.jpg").read_bytes() == FACE
    entry = _state(pool)["images"]["Person_1/Person_1_0001.jpg"]
    assert entry["author"] == "Jane Doe"  # HTML stripped
    assert entry["license"] == "CC BY-SA 4.0"
    assert entry["source"] == "https://commons.wikimedia.org/wiki/File:File_1.jpg"


def test_stops_at_the_limit(tmp_path, net):
    stats = wp.build_pool([_person(i) for i in range(5)], tmp_path / "w", limit=2)
    assert stats["saved"] == 2
    assert len(net.image_requests()) == 2


@pytest.mark.parametrize("license_name, allowed", [
    ("CC BY 4.0", True), ("CC BY-SA 3.0", True), ("CC0", True), ("Public domain", True),
    ("CC BY-NC 4.0", False), ("CC BY-ND 2.0", False), ("CC BY-NC-SA 4.0", False),
    ("GODL-India", False), ("Fair use", False), ("", False),
])
def test_licence_allowlist(license_name, allowed):
    assert wp.license_allowed(license_name) is allowed


def test_disallowed_licence_is_skipped_and_the_next_person_used(tmp_path, net):
    net.files["File 1.jpg"] = {"license": "CC BY-NC 4.0"}
    pool = tmp_path / "w"

    stats = wp.build_pool([_person(1), _person(2)], pool, limit=1)

    assert stats["saved"] == 1 and stats["skipped_licence"] == 1
    assert not (pool / "Person_1").exists()
    assert (pool / "Person_2" / "Person_2_0001.jpg").exists()
    assert len(net.image_requests()) == 1  # no download of the unlicensed image


def test_missing_licence_or_author_is_skipped(tmp_path, net):
    net.files["File 1.jpg"] = {"license": None}
    net.files["File 2.jpg"] = {"artist": None}
    stats = wp.build_pool([_person(1), _person(2)], tmp_path / "w", limit=2)
    assert stats["saved"] == 0
    assert stats["skipped_licence"] == 1 and stats["skipped_author"] == 1


def test_image_with_no_face_is_skipped(tmp_path, net):
    net.files["File 1.jpg"] = {"body": BLANK}
    pool = tmp_path / "w"
    stats = wp.build_pool([_person(1)], pool, limit=1)
    assert stats["skipped_no_face"] == 1
    assert not (pool / "Person_1").exists()


def test_undecodable_image_is_skipped(tmp_path, net):
    net.files["File 1.jpg"] = {"body": b"not an image"}
    assert wp.build_pool([_person(1)], tmp_path / "w", limit=1)["skipped_undecodable"] == 1


def test_wrong_host_is_not_fetched(tmp_path, net):
    net.files["File 1.jpg"] = {"url": "https://evil.example/x.jpg"}
    net.files["File 2.jpg"] = {"url": "http://upload.wikimedia.org/thumb/File_2.jpg/500px.jpg"}
    stats = wp.build_pool([_person(1), _person(2)], tmp_path / "w", limit=2)
    assert stats["skipped_host"] == 2
    assert net.image_requests() == [] and not any("evil" in u for u in net.requests)


def test_oversized_image_is_skipped(tmp_path, net, monkeypatch):
    monkeypatch.setattr(wp, "MAX_IMAGE_BYTES", 100)
    assert wp.build_pool([_person(1)], tmp_path / "w", limit=1)["skipped_too_large"] == 1


def test_non_jpeg_is_saved_as_jpeg(tmp_path, net):
    net.files["File 1.jpg"] = {"body": PNG_FACE}
    pool = tmp_path / "w"
    wp.build_pool([_person(1)], pool, limit=1)
    saved = (pool / "Person_1" / "Person_1_0001.jpg").read_bytes()
    assert saved.startswith(b"\xff\xd8") and cv2.imdecode(np.frombuffer(saved, np.uint8), cv2.IMREAD_COLOR) is not None


def test_unsafe_folder_in_the_list_is_refused(tmp_path, net):
    bad = {**_person(1), "folder": "../outside"}
    with pytest.raises(wp.PoolError, match="outside"):
        wp.build_pool([bad], tmp_path / "w", limit=1)


def test_waits_between_image_requests(tmp_path, net):
    wp.build_pool([_person(1), _person(2)], tmp_path / "w", limit=2)
    assert net.sleeps.count(wp.REQUEST_GAP_S) >= 2
    assert wp.REQUEST_GAP_S >= 3


def test_429_waits_as_told_then_retries(tmp_path, net):
    net.limit_next = 1
    stats = wp.build_pool([_person(1)], tmp_path / "w", limit=1)
    assert stats["saved"] == 1
    assert 7 in net.sleeps


def test_429_without_retry_after_waits_a_minute_and_long_waits_are_capped(tmp_path, net):
    net.limit_next = 1
    net.retry_after = None
    wp.build_pool([_person(1)], tmp_path / "w", limit=1)
    assert wp.DEFAULT_RETRY_WAIT_S in net.sleeps

    net.limit_next = 1
    net.retry_after = "99999"
    wp.build_pool([_person(2)], tmp_path / "w2", limit=1)
    assert wp.MAX_RETRY_WAIT_S in net.sleeps


def test_second_429_stops_with_a_resume_message_keeping_the_work(tmp_path, net):
    pool = tmp_path / "w"
    wp.build_pool([_person(1)], pool, limit=1)
    net.limit_next = 2

    with pytest.raises(wp.PoolError, match="again"):
        wp.build_pool([_person(1), _person(2)], pool, limit=2)

    assert (pool / "Person_1" / "Person_1_0001.jpg").exists()
    assert "Person_1/Person_1_0001.jpg" in _state(pool)["images"]


def test_resume_refetches_nothing_and_finishes(tmp_path, net):
    pool = tmp_path / "w"
    people = [_person(i) for i in range(3)]
    wp.build_pool(people, pool, limit=2)
    first = len(net.image_requests())

    stats = wp.build_pool(people, pool, limit=3)

    assert stats["saved"] == 1
    assert len(net.image_requests()) == first + 1
    assert sorted(_state(pool)["images"]) == [f"Person_{i}/Person_{i}_0001.jpg" for i in range(3)]


def test_people_rejected_once_are_not_fetched_again(tmp_path, net):
    net.files["File 1.jpg"] = {"body": BLANK}
    pool = tmp_path / "w"
    people = [_person(1), _person(2)]
    wp.build_pool(people, pool, limit=2)
    first = len(net.image_requests())

    wp.build_pool(people, pool, limit=2)

    assert len(net.image_requests()) == first
    assert _state(pool)["skipped"]["Q1"] == "no_face"


def test_nothing_to_do_makes_no_requests(tmp_path, net):
    pool = tmp_path / "w"
    wp.build_pool([_person(1)], pool, limit=1)
    net.requests.clear()
    wp.build_pool([_person(1)], pool, limit=1)
    assert net.requests == []


def test_network_failures_on_an_image_are_not_remembered_as_rejections(tmp_path, net, monkeypatch):
    real = net.urlopen

    def flaky(request, timeout=None):
        if "/thumb/" in request.full_url and "File_1" in request.full_url:
            raise TimeoutError("timed out")
        return real(request, timeout)

    monkeypatch.setattr(wp.urllib.request, "urlopen", flaky)
    pool = tmp_path / "w"
    stats = wp.build_pool([_person(1), _person(2)], pool, limit=2)

    assert stats["fetch_failed"] == 1 and stats["saved"] == 1
    assert "Q1" not in _state(pool).get("skipped", {})


def test_repeated_network_failures_stop_the_build(tmp_path, net, monkeypatch):
    monkeypatch.setattr(wp.urllib.request, "urlopen", lambda request, timeout=None: (_ for _ in ()).throw(OSError("down")))
    with pytest.raises(wp.PoolError, match="again"):
        wp.build_pool([_person(i) for i in range(20)], tmp_path / "w", limit=20)


def test_metadata_is_requested_in_batches(tmp_path, net):
    people = [_person(i) for i in range(wp.METADATA_BATCH + 1)]
    wp.build_pool(people, tmp_path / "w", limit=len(people))
    assert sum(u.startswith(wp.COMMONS_API) for u in net.requests) == 2


def test_requests_name_only_wikimedia_files(tmp_path, net):
    wp.build_pool([_person(1)], tmp_path / "w", limit=1)
    assert net.requests and all(
        u.startswith((wp.COMMONS_API, "https://upload.wikimedia.org/")) for u in net.requests
    )


@pytest.mark.parametrize("raw, text", [
    ("Plain Name", "Plain Name"),
    ('<a href="x">Jane</a> &amp; <span>Joe</span>', "Jane & Joe"),
    ("<script>alert(1)</script>Real", "Real"),
    ("  many \n  spaces ", "many spaces"),
])
def test_plain_text(raw, text):
    assert wp.plain_text(raw) == text


def test_plain_text_is_capped():
    assert len(wp.plain_text("x" * 1000)) <= wp.MAX_AUTHOR_CHARS


def test_both_wikimedia_image_hosts_are_accepted(tmp_path, net):
    # Commons serves many thumbnails from thumb.wikimedia.org: found in the real
    # build, where this check rejected most of the famous names (2026-11-02).
    net.files["File 1.jpg"] = {"url": "https://thumb.wikimedia.org/wikipedia/commons/thumb/File_1.jpg/500px.jpg"}
    net.files["File 2.jpg"] = {"url": "https://upload.wikimedia.org/thumb/File_2.jpg/500px.jpg"}
    stats = wp.build_pool([_person(1), _person(2)], tmp_path / "w", limit=2)
    assert stats["saved"] == 2


def test_lookalike_hosts_are_refused():
    for url in ("https://thumb.wikimedia.org.evil.example/x.jpg",
                "https://upload.wikimedia.org.evil.example/x.jpg",
                "https://evil.example/https://thumb.wikimedia.org/x.jpg"):
        info = {"extmetadata": {"LicenseShortName": {"value": "CC0"}, "Artist": {"value": "A"}}, "thumburl": url}
        assert wp._judge_metadata(info) == "host"


def test_doubled_author_text_is_collapsed():
    assert wp.plain_text("Unknown authorUnknown author") == "Unknown author"
    assert wp.plain_text("Abab") == "Abab"


def test_person_removed_from_the_list_leaves_the_pool(tmp_path, net):
    pool = tmp_path / "w"
    wp.build_pool([_person(1), _person(2)], pool, limit=2)
    keep_bytes = (pool / "Person_2" / "Person_2_0001.jpg").read_bytes()

    stats = wp.build_pool([_person(2), _person(3)], pool, limit=2)

    assert stats["removed"] == 1
    assert not (pool / "Person_1").exists()
    assert "Person_1/Person_1_0001.jpg" not in _state(pool)["images"]
    assert (pool / "Person_2" / "Person_2_0001.jpg").read_bytes() == keep_bytes
    assert (pool / "Person_3" / "Person_3_0001.jpg").exists()  # the place is refilled


def test_removal_touches_only_what_the_pool_recorded(tmp_path, net):
    pool = tmp_path / "w"
    wp.build_pool([_person(1)], pool, limit=1)
    other = pool / "Not_From_The_List"
    other.mkdir()
    (other / "mine.jpg").write_bytes(b"x")

    wp.build_pool([_person(1)], pool, limit=1)

    assert (other / "mine.jpg").exists()
