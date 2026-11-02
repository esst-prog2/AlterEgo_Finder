"""Tests for refresh_wikidata_list.py's selection logic (no network)."""

import json
from pathlib import Path

import refresh_wikidata_list as rw


def _row(qid, name, sitelinks=50, birth="1980", file="Some%20Photo.jpg"):
    return {
        "p": {"value": f"http://www.wikidata.org/entity/{qid}"},
        "pLabel": {"value": name},
        "img": {"value": f"http://commons.wikimedia.org/wiki/Special:FilePath/{file}"},
        "n": {"value": str(sitelinks)},
        "birth": {"value": f"{birth}-01-01T00:00:00Z"},
    }


def test_round_robin_across_occupations_by_fame():
    rows = {
        "actor": [_row("Q1", "A One", 90), _row("Q2", "A Two", 80)],
        "singer": [_row("Q3", "S One", 50), _row("Q4", "S Two", 40)],
    }

    people = rw.select_people(rows, cutoff_year=2008, total=3)

    assert [p["name"] for p in people] == ["A One", "S One", "A Two"]
    assert [p["occupation"] for p in people] == ["actor", "singer", "actor"]


def test_people_without_english_label_are_dropped():
    people = rw.select_people({"actor": [_row("Q1", "Q1"), _row("Q2", "Real Name")]}, 2008, 10)
    assert [p["name"] for p in people] == ["Real Name"]


def test_minors_are_dropped_even_with_a_second_birth_row():
    rows = {"actor": [
        _row("Q1", "Too Young", birth="2010"),
        _row("Q2", "Adult", birth="2008"),
        # Wikidata can list two birth dates; the later one decides.
        _row("Q3", "Disputed", birth="1990"),
        _row("Q3", "Disputed", birth="2012"),
    ]}
    assert [p["name"] for p in rw.select_people(rows, 2008, 10)] == ["Adult"]


def test_duplicates_across_occupations_are_removed():
    rows = {"actor": [_row("Q1", "Both Jobs", 90)], "singer": [_row("Q1", "Both Jobs", 90)]}
    assert len(rw.select_people(rows, 2008, 10)) == 1


def test_same_folder_for_two_people_keeps_the_more_famous():
    rows = {"actor": [_row("Q1", "John Smith", 90), _row("Q2", "John Smith", 40)]}
    assert [p["qid"] for p in rw.select_people(rows, 2008, 10)] == ["Q1"]


def test_folder_names_are_plain_ascii_and_safe():
    # cv2.imread and imwrite silently fail on non-ASCII paths on Windows, which
    # would drop such people from the pool (found on 2026-11-02).
    assert rw.folder_name("Pelé") == "Pele"
    assert rw.folder_name("Kimi Räikkönen") == "Kimi_Raikkonen"
    assert rw.folder_name("Ødegaard Łukáš") == "Odegaard_Lukas"
    assert rw.folder_name("Martin Luther King Jr.") == "Martin_Luther_King_Jr"
    assert rw.folder_name('A: B/C\\D*E?F"G<H>I|J') == "A_BCDEFGHIJ"


def test_people_whose_name_has_no_ascii_form_are_dropped():
    rows = {"actor": [_row("Q1", "山田"), _row("Q2", "Real")]}
    assert [p["qid"] for p in rw.select_people(rows, 2008, 10)] == ["Q2"]


def test_entry_holds_decoded_file_name():
    (person,) = rw.select_people({"actor": [_row("Q1", "Name", file="My%20Photo%20%282020%29.jpg")]}, 2008, 1)
    assert person["file"] == "My Photo (2020).jpg"
    assert person["folder"] == "Name"
    assert set(person) == {"qid", "name", "folder", "file", "occupation", "sitelinks"}


def test_selection_is_deterministic_whatever_the_row_order():
    rows = [_row(f"Q{i}", f"Name {i}", 50) for i in range(5)]
    a = rw.select_people({"actor": rows}, 2008, 5)
    b = rw.select_people({"actor": list(reversed(rows))}, 2008, 5)
    assert a == b


def test_failed_query_leaves_the_list_unchanged(tmp_path, monkeypatch, capsys):
    out = tmp_path / "people.json"
    out.write_text("[1, 2]")

    def failing(occupation_qid):
        raise rw.QueryError("HTTP 502")

    monkeypatch.setattr(rw, "fetch_occupation", failing)

    assert rw.main(["--out", str(out)]) == 1

    assert out.read_text() == "[1, 2]"
    assert "502" in capsys.readouterr().err


def test_main_writes_the_list(tmp_path, monkeypatch):
    out = tmp_path / "people.json"
    monkeypatch.setattr(rw, "fetch_occupation", lambda occupation_qid: [_row(occupation_qid + "x", f"N {occupation_qid}")])

    assert rw.main(["--out", str(out), "--total", "3"]) == 0

    assert len(json.loads(out.read_text(encoding="utf-8"))) == 3


def test_excluded_people_are_dropped():
    excluded = next(iter(rw.EXCLUDED_QIDS))
    rows = {"politician": [_row(excluded, "Excluded Person", 99), _row("Q999999", "Someone Else", 50)]}
    assert [p["qid"] for p in rw.select_people(rows, 2008, 10)] == ["Q999999"]


def test_exclusion_list_covers_the_agreed_people():
    # Pol Pot, Idi Amin, Saddam Hussein, Gaddafi, al-Assad, Kim Jong-un, Mugabe,
    # Suharto, Lukashenka, Putin (decided 2026-11-02), by Wikidata identifier.
    assert {"Q39464", "Q48231", "Q1316", "Q19878", "Q44329", "Q56226", "Q10707",
            "Q44819", "Q2866", "Q7747"} <= rw.EXCLUDED_QIDS


def test_committed_list_has_none_of_the_excluded():
    people = json.loads((Path(__file__).parent.parent / "data" / "wikidata_people.json").read_text(encoding="utf-8"))
    assert not {p["qid"] for p in people} & rw.EXCLUDED_QIDS
    assert len(people) >= 500


def test_politicians_are_not_selected_as_an_occupation():
    assert "politician" not in rw.OCCUPATIONS
    assert len(rw.OCCUPATIONS) >= 4


def test_query_excludes_people_with_a_political_occupation_elsewhere():
    # Wikidata tags Fidel Castro and Kim Jong-il as film actors too, so leaving out
    # the politician category alone would not keep politicians out (2026-11-02).
    query = rw._query("Q10800557")
    assert "FILTER NOT EXISTS" in query
    assert "wd:Q82955" in query  # politician


def test_adult_cutoff_allows_for_birthdays_still_to_come():
    # Born December 2008 is still 17 in November 2026.
    assert rw.adult_cutoff_year(2026) == 2007
