#!/usr/bin/env python
"""Regenerate data/wikidata_people.json, the committed list of people in the
optional public-figure pool. Only needed to change the selection: building the
pool (setup_data.py --wikidata) reads the list and never queries for people.

Usage (from the repository root):
    python refresh_wikidata_list.py
"""

from __future__ import annotations

import argparse
import datetime
import http.client
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent
SPARQL_URL = "https://query.wikidata.org/sparql"
USER_AGENT = "AlterEgoFinder/1.0 (https://github.com/esst-prog2/AlterEgo_Finder)"
OCCUPATIONS = {
    "film actor": "Q10800557",
    "association football player": "Q937857",
    "singer": "Q177220",
    "tennis player": "Q10833314",
    "racing driver": "Q10841764",
}
# No politicians, so a lookalike is never a political statement (2026-11-02). Being
# tagged with another occupation is not enough: Wikidata lists Fidel Castro and Kim
# Jong-il as film actors. Politician, statesperson, monarch, revolutionary.
EXCLUDED_OCCUPATIONS = ("Q82955", "Q372436", "Q116", "Q3242115")
# A backstop in case Wikidata's tags change: dictators and leaders widely held
# responsible for mass atrocities.
EXCLUDED_QIDS = frozenset({
    "Q39464",  # Pol Pot
    "Q48231",  # Idi Amin
    "Q1316",  # Saddam Hussein
    "Q19878",  # Muammar Gaddafi
    "Q44329",  # Bashar al-Assad
    "Q10665",  # Kim Jong-il
    "Q56226",  # Kim Jong-un
    "Q10707",  # Robert Mugabe
    "Q44819",  # Suharto
    "Q11256",  # Fidel Castro
    "Q2866",  # Alexander Lukashenka
    "Q7747",  # Vladimir Putin
})
MIN_SITELINKS = 40
EARLIEST_BIRTH_YEAR = 1920  # fewer paintings: portraits of older figures rarely are photos
ADULT_AGE = 18
DEFAULT_TOTAL = 650  # more than the pool's 500, as some images get skipped at build time
QUERY_TIMEOUT_S = 70
QUERY_ATTEMPTS = 3
RETRY_WAIT_S = 20
# Letters that Unicode decomposition does not reduce to ASCII.
_NO_DECOMPOSITION = str.maketrans({
    "ø": "o", "Ø": "O", "ł": "l", "Ł": "L", "đ": "d", "Đ": "D",
    "ß": "ss", "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE",
})
_ILLEGAL_IN_FOLDER = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class QueryError(Exception):
    """Wikidata did not answer, after retries."""


def folder_name(label: str) -> str:
    """A plain ASCII folder name, or "" if the name has no ASCII form.

    cv2.imread and imwrite silently fail on non-ASCII paths on Windows.
    """
    translated = label.translate(_NO_DECOMPOSITION)
    ascii_only = unicodedata.normalize("NFKD", translated).encode("ascii", "ignore").decode("ascii")
    cleaned = _ILLEGAL_IN_FOLDER.sub("", ascii_only).strip().rstrip(".")
    return re.sub(r"\s+", "_", cleaned)


def _query(occupation_qid: str) -> str:
    excluded = " ".join(f"wd:{qid}" for qid in EXCLUDED_OCCUPATIONS)
    return f"""SELECT ?p ?pLabel ?img ?n ?birth WHERE {{
      ?p wdt:P106 wd:{occupation_qid} ; wdt:P31 wd:Q5 ; wdt:P18 ?img ;
         wikibase:sitelinks ?n ; wdt:P569 ?birth .
      FILTER(?n >= {MIN_SITELINKS}) FILTER(YEAR(?birth) >= {EARLIEST_BIRTH_YEAR})
      FILTER NOT EXISTS {{ VALUES ?excluded {{ {excluded} }} ?p wdt:P106 ?excluded . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }} ORDER BY DESC(?n) LIMIT 400"""


def fetch_occupation(occupation_qid: str) -> List[dict]:
    """The query's result rows, retrying the endpoint's frequent 502 and 504."""
    url = f"{SPARQL_URL}?format=json&query={urllib.parse.quote(_query(occupation_qid))}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    error: Optional[Exception] = None
    for attempt in range(QUERY_ATTEMPTS):
        if attempt:
            time.sleep(RETRY_WAIT_S)
        try:
            with urllib.request.urlopen(request, timeout=QUERY_TIMEOUT_S) as response:
                return json.load(response)["results"]["bindings"]
        except (OSError, http.client.HTTPException, ValueError, KeyError) as e:
            error = e
    raise QueryError(f"Wikidata query for {occupation_qid} failed: {error}")


def adult_cutoff_year(current_year: int) -> int:
    """The latest birth year certain to be 18 already: only the year is compared,
    so someone born this many years ago might have a birthday still to come."""
    return current_year - ADULT_AGE - 1


def select_people(rows_by_occupation: Dict[str, List[dict]], cutoff_year: int, total: int) -> List[dict]:
    """The list's entries: round-robin across occupations, most sitelinks first.

    Dropped: people with no English label (their label is a Q number) or no ASCII
    form of it, anyone with a birth year after ``cutoff_year``, and repeats of a
    person or folder.
    The result does not depend on the order of the rows.
    """
    birth_years: Dict[str, int] = {}
    for rows in rows_by_occupation.values():
        for row in rows:
            qid = row["p"]["value"].rsplit("/", 1)[1]
            year = int(row["birth"]["value"][:4])
            birth_years[qid] = max(year, birth_years.get(qid, year))

    candidates: Dict[str, List[dict]] = {}
    for occupation, rows in rows_by_occupation.items():
        entries = {}
        for row in rows:
            qid = row["p"]["value"].rsplit("/", 1)[1]
            label = row["pLabel"]["value"]
            if (qid in EXCLUDED_QIDS or re.fullmatch(r"Q\d+", label)
                    or birth_years[qid] > cutoff_year or not folder_name(label)):
                continue
            file = urllib.parse.unquote(row["img"]["value"].rsplit("/", 1)[1])
            entry = {
                "qid": qid, "name": label, "folder": folder_name(label), "file": file,
                "occupation": occupation, "sitelinks": int(row["n"]["value"]),
            }
            # A person with two images: keep one, the same one every time.
            if qid not in entries or file < entries[qid]["file"]:
                entries[qid] = entry
        candidates[occupation] = sorted(
            entries.values(), key=lambda e: (-e["sitelinks"], e["qid"])
        )

    people: List[dict] = []
    seen_qids, seen_folders = set(), set()
    positions = {occupation: 0 for occupation in candidates}
    while len(people) < total and any(positions[o] < len(candidates[o]) for o in candidates):
        for occupation, entries in candidates.items():
            while positions[occupation] < len(entries) and len(people) < total:
                entry = entries[positions[occupation]]
                positions[occupation] += 1
                if entry["qid"] not in seen_qids and entry["folder"] not in seen_folders:
                    seen_qids.add(entry["qid"])
                    seen_folders.add(entry["folder"])
                    people.append(entry)
                    break
    return people


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate the public-figure pool's list of people.")
    parser.add_argument("--out", default=str(ROOT / "data" / "wikidata_people.json"))
    parser.add_argument("--total", type=int, default=DEFAULT_TOTAL)
    args = parser.parse_args(argv)

    rows = {}
    try:
        for occupation, qid in OCCUPATIONS.items():
            print(f"Querying {occupation} ...")
            rows[occupation] = fetch_occupation(qid)
    except QueryError as e:
        print(f"Error: {e}. The existing list was left unchanged.", file=sys.stderr)
        return 1

    people = select_people(rows, adult_cutoff_year(datetime.date.today().year), args.total)
    out = Path(args.out)
    part = out.with_name(out.name + ".part")
    part.write_text(json.dumps(people, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(part, out)
    print(f"Wrote {len(people)} people to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
