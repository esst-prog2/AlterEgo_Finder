#!/usr/bin/env python
"""Spike (OpenSpec change multi-photo-spike): would several photos per person help,
and how far does a walk from lookalike to lookalike get?

Compares one photo, best photo, averaged and extra photos for the top 10 only, on
about 50 people, each at a threshold fitted its own way. Then simulates the walk
with LFW standing in for the web.

Throwaway spike code. Photos stay in the gitignored data/spike_multiphoto/; only
scores, counts and public figures' names go into data/spike_multiphoto_results.json.
No request carries a query photo or anything derived from one, and the walk uses
no network.

Usage (from the repository root, in this order):
    python spike_multiphoto.py select
    python spike_multiphoto.py fetch [--limit N]
    python spike_multiphoto.py embed
    python spike_multiphoto.py measure
"""

from __future__ import annotations

import argparse
import http.client
import json
import random
import sys
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Set

import cv2
import numpy as np

from face_pipeline import wikidata_pool as pool
from face_pipeline.calibration import compute_far_threshold, normalise_name
from face_pipeline.detector import _find_faces
from face_pipeline.embedder import NoFaceDetectedError, extract_embedding
from face_pipeline.index import get_or_build_index, rank_matches
from face_pipeline.matching import load_thresholds

DATA = Path("data")
POOL_DIR = DATA / "wikidata"
OUT_DIR = DATA / "spike_multiphoto"
GALLERY_FILE = OUT_DIR / "gallery.json"
STATE_FILE = OUT_DIR / "state.json"
LFW_DIR = DATA / "lfw" / "lfw"
LFW_CACHE = DATA / "lfw" / "spike_multiphoto_embeddings.npz"  # the HW4 cache predates pick-largest-face
RESULTS_FILE = DATA / "spike_multiphoto_results.json"
QUERY = DATA / "my_photo" / "PK.jpg"
SECOND_PHOTO_DIR = DATA / "my_photo_test"

SEED = 20261103
GALLERY_SIZE = 50
EXTRA_PHOTOS = 3
MAX_DOWNLOADS = 8  # per person
FLOORS = (0.25, 0.15, 0.35)
ARMS = ("one", "best", "averaged", "top")
TOP = 10
STRANGERS_FIT, STRANGERS_TEST = 1000, 1000
SAME_PERSON_PHOTOS = 5  # per person, so a few very photographed people do not dominate
WALK_K = (5, 10, 20)
WALK_STEPS = 10
WALK_STRANGERS, WALK_SELF = 200, 100

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
ALLOWED_HOSTS = {"www.wikidata.org", "commons.wikimedia.org", "upload.wikimedia.org", "thumb.wikimedia.org"}
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")


# --- the measures (pure, see tests/test_spike_multiphoto.py) ---------------------


def _normalised(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def person_scores(queries: np.ndarray, photos: Sequence[np.ndarray], arm: str, top: int = TOP) -> np.ndarray:
    """Query-by-person scores. ``photos`` holds each person's unit vectors, pool photo first."""
    first = np.array([p[0] for p in photos])
    if arm == "one":
        return queries @ first.T
    if arm == "averaged":
        return queries @ _normalised(np.array([p.mean(axis=0) for p in photos])).T
    best = np.stack([(queries @ p.T).max(axis=1) for p in photos], axis=1)
    if arm == "best":
        return best
    if arm == "top":
        scores = queries @ first.T
        for q, row in enumerate(scores):
            leaders = np.argsort(-row)[:top]
            scores[q, leaders] = best[q, leaders]
        return scores
    raise ValueError(arm)


def pick_varied(anchor: np.ndarray, candidates: np.ndarray, keep: int) -> List[int]:
    """Indices of up to ``keep`` candidates, each the least like those already chosen."""
    chosen: List[int] = []
    reference = [anchor]
    remaining = list(range(len(candidates)))
    while remaining and len(chosen) < keep:
        closeness = [max(float(candidates[i] @ r) for r in reference) for i in remaining]
        pick = remaining[int(np.argmin(closeness))]
        chosen.append(pick)
        reference.append(candidates[pick])
        remaining.remove(pick)
    return chosen


@dataclass
class Walk:
    end: int
    score: float
    steps: int
    checked: Set[int]


def walk(query: np.ndarray, start: int, faces: np.ndarray, links: np.ndarray, max_steps: int) -> Walk:
    """From ``start``, move to the best neighbour while it beats the current face."""
    current, score, steps = start, float(faces[start] @ query), 0
    checked = {start}
    while steps < max_steps:
        neighbours = links[current]
        checked.update(int(n) for n in neighbours)
        scores = faces[neighbours] @ query
        best = int(np.argmax(scores))
        if scores[best] <= score:
            break
        current, score = int(neighbours[best]), float(scores[best])
        steps += 1
    return Walk(current, score, steps, checked)


def nearest_neighbours(faces: np.ndarray, k: int, chunk: int = 512) -> np.ndarray:
    """Each face's ``k`` most similar other faces, most similar first."""
    links = np.empty((len(faces), k), dtype=np.int32)
    for start in range(0, len(faces), chunk):
        block = faces[start: start + chunk] @ faces.T
        block[np.arange(len(block)), np.arange(start, start + len(block))] = -np.inf
        top = np.argpartition(-block, k - 1, axis=1)[:, :k]
        order = np.argsort(-np.take_along_axis(block, top, axis=1), axis=1)
        links[start: start + chunk] = np.take_along_axis(top, order, axis=1)
    return links


def fit_threshold(top1: np.ndarray) -> float:
    return compute_far_threshold(np.asarray(top1).tolist())


def rate_at_or_above(scores: np.ndarray, threshold: float) -> float:
    return float(np.mean(np.asarray(scores) >= threshold))


def same_person_hits(scores: np.ndarray, truth: Sequence[int], threshold: float) -> np.ndarray:
    """The right person is ranked first and reaches the threshold."""
    truth = np.asarray(truth)
    return (scores.argmax(axis=1) == truth) & (scores.max(axis=1) >= threshold)


# --- choosing the gallery --------------------------------------------------------


def _lfw_people() -> Dict[str, List[str]]:
    return {
        p.name: sorted(f"{p.name}/{f.name}" for f in p.glob("*.jpg"))
        for p in sorted(LFW_DIR.iterdir()) if p.is_dir()
    }


def _pool_people() -> Dict[str, dict]:
    people = json.loads((DATA / "wikidata_people.json").read_text(encoding="utf-8"))
    return {p["folder"]: p for p in people if (POOL_DIR / p["folder"]).is_dir()}


def cmd_select(_args) -> int:
    index = get_or_build_index(POOL_DIR)
    query = extract_embedding(cv2.imread(str(QUERY)))
    top = [entry.person for entry, _ in rank_matches(index, query)[:TOP]]

    people = _pool_people()
    lfw_names = {normalise_name(name) for name in _lfw_people()}
    in_lfw = [f for f in people if normalise_name(f) in lfw_names]

    chosen = list(dict.fromkeys(top + ["Bruce_Springsteen"]))
    by_occupation: Dict[str, List[str]] = {}
    rng = random.Random(SEED)
    for folder in rng.sample(sorted(in_lfw), len(in_lfw)):
        by_occupation.setdefault(people[folder]["occupation"], []).append(folder)
    while len(chosen) < GALLERY_SIZE and any(by_occupation.values()):
        for occupation in sorted(by_occupation):
            if by_occupation[occupation] and len(chosen) < GALLERY_SIZE:
                folder = by_occupation[occupation].pop()
                if folder not in chosen:
                    chosen.append(folder)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    GALLERY_FILE.write_text(json.dumps(chosen, indent=1), encoding="utf-8")
    with_lfw = sum(normalise_name(f) in lfw_names for f in chosen)
    print(f"{len(chosen)} people, {with_lfw} also in LFW. Written to {GALLERY_FILE}.")
    print(", ".join(chosen))
    return 0


# --- fetching extra photos -------------------------------------------------------


def _guarded_open(original):
    def opened(url, *args, **kwargs):
        host = urllib.parse.urlparse(url).hostname
        if host not in ALLOWED_HOSTS:
            raise pool.PoolError(f"Refusing a request to {host}")
        return original(url, *args, **kwargs)
    return opened


def _api_json(base: str, **params) -> dict:
    time.sleep(pool.REQUEST_GAP_S)
    with pool._open(f"{base}?{urllib.parse.urlencode({'format': 'json', **params})}") as response:
        return json.load(response)


def _category_of(qid: str) -> str | None:
    claims = _api_json(WIKIDATA_API, action="wbgetclaims", entity=qid, property="P373").get("claims", {})
    for claim in claims.get("P373", []):
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if value:
            return value
    return None


def _category_files(category: str) -> List[str]:
    body = _api_json(pool.COMMONS_API, action="query", list="categorymembers", cmtype="file",
                     cmlimit=200, cmtitle=f"Category:{category}")
    titles = [m["title"][len("File:"):] for m in body.get("query", {}).get("categorymembers", [])]
    return [t for t in titles if t.lower().endswith(IMAGE_SUFFIXES)]


def _fetch_person(person: dict, record: dict) -> None:
    """Downloads up to MAX_DOWNLOADS usable files, keeping the one-face ones."""
    category = _category_of(person["qid"])
    record["category"] = category
    if not category:
        return
    files = [f for f in _category_files(category) if f != person["file"]]
    record["files_in_category"] = len(files)
    random.Random(f"{SEED}{person['qid']}").shuffle(files)  # not alphabetical order

    folder = OUT_DIR / person["folder"]
    folder.mkdir(parents=True, exist_ok=True)
    rejected: Dict[str, int] = {}
    kept: List[dict] = []
    downloads = 0
    for start in range(0, len(files), pool.METADATA_BATCH):
        if downloads >= MAX_DOWNLOADS:
            break
        batch = files[start: start + pool.METADATA_BATCH]
        metadata = pool._fetch_metadata(batch)
        for title in batch:
            if downloads >= MAX_DOWNLOADS:
                break
            info = metadata.get(title)
            reason = pool._judge_metadata(info)
            if reason is None:
                downloads += 1
                data = pool._download(info["thumburl"])
                image = None if data is None else cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
                if image is None:
                    reason = "undecodable"
                else:
                    found = _find_faces(image)
                    if found is None:
                        reason = "no_face"
                    elif len(found[0]) != 1:
                        reason = "several_faces"
                    else:
                        try:
                            embedding = extract_embedding(image)
                        except NoFaceDetectedError:
                            reason = "no_face"
                        else:
                            name = f"{len(kept):02d}.jpg"
                            (folder / name).write_bytes(pool._as_jpeg(data, image))
                            meta = info["extmetadata"]
                            kept.append({
                                "file": name, "title": title, "source": info.get("descriptionurl", ""),
                                "license": meta["LicenseShortName"]["value"],
                                "author": pool.plain_text(meta["Artist"]["value"])[:pool.MAX_AUTHOR_CHARS],
                                "embedding": (embedding / np.linalg.norm(embedding)).tolist(),
                            })
            if reason is not None:
                rejected[reason] = rejected.get(reason, 0) + 1
    record["kept"] = kept
    record["rejected"] = rejected


def cmd_fetch(args) -> int:
    pool._open = _guarded_open(pool._open)
    people = _pool_people()
    gallery = json.loads(GALLERY_FILE.read_text(encoding="utf-8"))
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}
    failures = 0
    for folder in gallery[: args.limit]:
        if folder in state:
            continue
        record: dict = {}
        try:
            _fetch_person(people[folder], record)
        except (OSError, http.client.HTTPException, ValueError, KeyError) as e:
            failures += 1
            print(f"{folder}: failed ({e})", flush=True)
            if failures >= pool.MAX_CONSECUTIVE_FAILURES:
                print("Repeated failures: stopping. Run the same command to continue.")
                return 1
            continue
        except pool.PoolError as e:
            print(e)
            return 1
        failures = 0
        state[folder] = record
        part = STATE_FILE.with_name(STATE_FILE.name + ".part")
        part.write_text(json.dumps(state), encoding="utf-8")
        part.replace(STATE_FILE)
        print(f"{folder}: kept {len(record.get('kept', []))}, rejected {record.get('rejected', {})}, "
              f"category {record.get('category')!r}", flush=True)
    print(f"Done: {len(state)} of {len(gallery)} people.")
    return 0


# --- embedding LFW ---------------------------------------------------------------


def _split_lfw() -> dict:
    """Who plays which part, with fixed seeds. People in the pool are never strangers."""
    lfw = _lfw_people()
    in_pool = {normalise_name(f) for f in _pool_people()}
    outside = sorted(name for name in lfw if normalise_name(name) not in in_pool)
    rng = random.Random(SEED)
    shuffled = rng.sample(outside, len(outside))
    strangers_fit = shuffled[:STRANGERS_FIT]
    strangers_test = shuffled[STRANGERS_FIT: STRANGERS_FIT + STRANGERS_TEST]
    # The walk's own queries, kept out of its graph below.
    walk_strangers = shuffled[-WALK_STRANGERS:]
    candidates = [n for n in shuffled[STRANGERS_FIT + STRANGERS_TEST: -WALK_STRANGERS] if len(lfw[n]) >= 2]
    walk_self = candidates[:WALK_SELF]
    graph = [name for name in sorted(lfw) if name not in set(walk_strangers)]
    return {"lfw": lfw, "strangers_fit": strangers_fit, "strangers_test": strangers_test,
            "walk_strangers": walk_strangers, "walk_self": walk_self, "graph": graph}


def _same_person_queries(lfw: Dict[str, List[str]], gallery: List[str]) -> Dict[str, List[str]]:
    by_name = {normalise_name(name): name for name in lfw}
    queries = {}
    for folder in gallery:
        name = by_name.get(normalise_name(folder))
        if name:
            photos = list(lfw[name])
            random.Random(f"{SEED}{folder}").shuffle(photos)
            queries[folder] = photos[:SAME_PERSON_PHOTOS]
    return queries


def _needed_images(split: dict, gallery: List[str]) -> List[str]:
    lfw = split["lfw"]
    needed = set()
    for key in ("strangers_fit", "strangers_test", "walk_strangers", "graph"):
        needed.update(lfw[name][0] for name in split[key])
    needed.update(lfw[name][1] for name in split["walk_self"])
    for photos in _same_person_queries(lfw, gallery).values():
        needed.update(photos)
    return sorted(needed)


def _load_cache() -> Dict[str, np.ndarray]:
    if not LFW_CACHE.exists():
        return {}
    with np.load(LFW_CACHE) as data:
        return {key: data[key] for key in data.files}


def cmd_embed(_args) -> int:
    gallery = json.loads(GALLERY_FILE.read_text(encoding="utf-8"))
    needed = _needed_images(_split_lfw(), gallery)
    cache = _load_cache()
    todo = [rel for rel in needed if rel not in cache]
    print(f"{len(needed)} images needed, {len(todo)} to embed.", flush=True)
    for i, rel in enumerate(todo, start=1):
        try:
            vector = extract_embedding(cv2.imread(str(LFW_DIR / rel)))
            vector = vector / np.linalg.norm(vector)
        except NoFaceDetectedError:
            vector = np.zeros(512)  # remembered as "no face"
        cache[rel] = vector.astype(np.float32)
        if i % 500 == 0:
            np.savez(LFW_CACHE, **cache)
            print(f"  {i} of {len(todo)}", flush=True)
    np.savez(LFW_CACHE, **cache)
    print("Done.")
    return 0


# --- measuring --------------------------------------------------------------------


def _vectors(cache: Dict[str, np.ndarray], images: Sequence[str]) -> np.ndarray:
    """Unit vectors for the images in which a face was found."""
    vectors = [cache[i] for i in images if cache[i].any()]
    return np.array(vectors, dtype=np.float64)


def _pool_vectors(index) -> Dict[str, np.ndarray]:
    embeddings = _normalised(np.asarray(index.embeddings, dtype=np.float64))
    return {entry.person: embeddings[i] for i, entry in enumerate(index.entries)}


def _gallery_photos(gallery, state, pool_vectors, floor: float) -> List[np.ndarray]:
    photos = []
    for folder in gallery:
        anchor = pool_vectors[folder]
        kept = state.get(folder, {}).get("kept", [])
        candidates = np.array([k["embedding"] for k in kept], dtype=np.float64).reshape(-1, anchor.size)
        if len(candidates):
            candidates = candidates[candidates @ anchor >= floor]
        picked = pick_varied(anchor, candidates, EXTRA_PHOTOS)
        photos.append(np.vstack([anchor[None, :], candidates[picked]]))
    return photos


def _measure_arms(gallery, state, pool_vectors, cache, split, query, second, low, pool_high) -> dict:
    lfw = split["lfw"]
    fit = _vectors(cache, [lfw[n][0] for n in split["strangers_fit"]])
    test = _vectors(cache, [lfw[n][0] for n in split["strangers_test"]])
    per_person = _same_person_queries(lfw, gallery)
    same_vectors, truth = [], []
    for folder, images in per_person.items():
        vectors = _vectors(cache, images)
        same_vectors.extend(vectors)
        truth.extend([gallery.index(folder)] * len(vectors))
    same = np.array(same_vectors)
    truth = np.array(truth)

    results: dict = {"strangers_fit": len(fit), "strangers_test": len(test),
                     "same_person_queries": len(same), "same_person_people": len(per_person), "floors": {}}
    for floor in FLOORS:
        photos = _gallery_photos(gallery, state, pool_vectors, floor)
        counts = [len(p) for p in photos]
        has_extras = np.array([counts[t] > 1 for t in truth])
        by_arm: dict = {}
        one_hits = None
        one_threshold = None
        for arm in ARMS:
            threshold = fit_threshold(person_scores(fit, photos, arm).max(axis=1))
            test_top1 = person_scores(test, photos, arm).max(axis=1)
            same_scores = person_scores(same, photos, arm)
            own_scores = same_scores[np.arange(len(truth)), truth]
            hits = same_person_hits(same_scores, truth, threshold)
            if arm == "one":
                one_hits, one_threshold = hits, threshold
            own = person_scores(query[None, :], photos, arm)[0]
            order = np.argsort(-own)[:3]
            by_arm[arm] = {
                "threshold_high": threshold,
                "strangers_test_reaching": int((test_top1 >= threshold).sum()),
                "same_person_hits": int(hits.sum()),
                "same_person_median_own_score": float(np.median(own_scores)),
                "same_person_median_own_score_people_with_extras": float(np.median(own_scores[has_extras])),
                "same_person_hits_at_pool_high": int(same_person_hits(same_scores, truth, pool_high).sum()),
                "same_person_misses": sorted(gallery[t] for t, hit in zip(truth, hits) if not hit),
                "fixed_from_one_photo": int((hits & ~one_hits).sum()),
                "broken_from_one_photo": int((~hits & one_hits).sum()),
                "own_top": [{"person": gallery[i], "score": float(own[i]),
                             "label": "Same person" if own[i] >= threshold else
                                      "Alter Ego" if own[i] >= low else "Not You"} for i in order],
                "own_second_photo_score": float(second @ query),
                "own_second_photo_reaches": bool(second @ query >= threshold),
            }
            if arm == "top":
                by_arm[arm]["strangers_test_reaching_one_photo_threshold"] = int((test_top1 >= one_threshold).sum())
        misses = int((~one_hits).sum())
        results["floors"][str(floor)] = {
            "photos_total": int(sum(counts)), "photos_per_person": sorted(counts),
            "one_photo_misses": misses, "queries_for_people_with_extras": int(has_extras.sum()),
            "people_with_extras": sorted(g for g, c in zip(gallery, counts) if c > 1), "arms": by_arm,
        }
    return results


def _measure_walk(pool_vectors, cache, split, query, pool_high) -> dict:
    lfw = split["lfw"]
    names = [n for n in split["graph"] if cache[lfw[n][0]].any()]
    position = {n: i for i, n in enumerate(names)}
    faces = np.array([cache[lfw[n][0]] for n in names], dtype=np.float64)
    pool_matrix = np.array(list(pool_vectors.values()))

    def start_of(q: np.ndarray) -> int:
        top_match = pool_matrix[int(np.argmax(pool_matrix @ q))]
        return int(np.argmax(faces @ top_match))

    strangers = [cache[lfw[n][0]] for n in split["walk_strangers"] if cache[lfw[n][0]].any()]
    selves = [(cache[lfw[n][1]], position[n]) for n in split["walk_self"] if n in position and cache[lfw[n][1]].any()]

    results: dict = {"graph_faces": len(faces), "strangers": len(strangers), "people_with_a_face_in_the_graph": len(selves), "k": {}}
    for k in WALK_K:
        links = nearest_neighbours(faces, k)

        def run(q):
            result = walk(q, start_of(q), faces, links, WALK_STEPS)
            scores = faces @ q
            return result, float(scores.max()), int(scores.argmax())

        stranger_runs = [run(np.asarray(q, dtype=np.float64)) for q in strangers]
        self_runs = [(run(np.asarray(q, dtype=np.float64)), own) for q, own in selves]
        everyone = stranger_runs + [r for r, _ in self_runs]
        own_result = run(query)

        results["k"][str(k)] = {
            "median_faces_checked": float(np.median([len(r.checked) for r, _, _ in everyone])),
            "median_steps": float(np.median([r.steps for r, _, _ in everyone])),
            "strangers_found_true_best": sum(r.end == b for r, _, b in stranger_runs),
            "strangers_median_score_reached": float(np.median([r.score for r, _, _ in stranger_runs])),
            "strangers_median_true_best": float(np.median([s for _, s, _ in stranger_runs])),
            "strangers_ending_at_or_above_pool_high": sum(r.score >= pool_high for r, _, _ in stranger_runs),
            "strangers_exact_search_at_or_above_pool_high": sum(s >= pool_high for _, s, _ in stranger_runs),
            "people_led_back_to_own_face": sum(own in r.checked for (r, _, _), own in self_runs),
            "people_ending_on_own_face": sum(r.end == own for (r, _, _), own in self_runs),
            "people_exact_search_finds_own_face": sum(b == own for (_, _, b), own in self_runs),
            "own_photo": {"score_reached": own_result[0].score, "steps": own_result[0].steps,
                          "faces_checked": len(own_result[0].checked), "true_best": own_result[1],
                          "found_true_best": own_result[0].end == own_result[2]},
        }
    return results


def cmd_measure(_args) -> int:
    gallery = json.loads(GALLERY_FILE.read_text(encoding="utf-8"))
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    missing = [g for g in gallery if g not in state]
    if missing:
        print(f"Not fetched yet: {missing}", file=sys.stderr)
        return 1
    index = get_or_build_index(POOL_DIR)
    pool_vectors = _pool_vectors(index)
    low, high = load_thresholds(POOL_DIR / "config.json")
    cache = _load_cache()
    split = _split_lfw()
    query = _normalised(extract_embedding(cv2.imread(str(QUERY))).astype(np.float64))
    second_path = next(SECOND_PHOTO_DIR.glob("*.jpg"))
    second = _normalised(extract_embedding(cv2.imread(str(second_path))).astype(np.float64))

    results = {
        "seed": SEED,
        "gallery": gallery,
        "people_with_no_category": sum(not state[g].get("category") for g in gallery),
        "rejected_totals": _sum_counts(state[g].get("rejected", {}) for g in gallery),
        "arms": _measure_arms(gallery, state, pool_vectors, cache, split, query, second, low, high),
        "walk": _measure_walk(pool_vectors, cache, split, query, high),
    }
    RESULTS_FILE.write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=1))
    return 0


def _sum_counts(counts) -> Dict[str, int]:
    total: Dict[str, int] = {}
    for c in counts:
        for key, value in c.items():
            total[key] = total.get(key, 0) + value
    return total


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("select").set_defaults(run=cmd_select)
    fetch = commands.add_parser("fetch")
    fetch.add_argument("--limit", type=int, default=None, help="only the first N people, for a thin run")
    fetch.set_defaults(run=cmd_fetch)
    commands.add_parser("embed").set_defaults(run=cmd_embed)
    commands.add_parser("measure").set_defaults(run=cmd_measure)
    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
