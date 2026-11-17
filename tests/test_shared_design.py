"""The page's theme follows the shared design system (DESIGN.md) and loads nothing from the network.

These read .streamlit/config.toml and app.py's target colours directly, so they run without
Streamlit installed.
"""
import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CONFIG = REPO_ROOT / ".streamlit" / "config.toml"
LABEL_COLOURS = {"Same person": "#1a7f37", "Alter Ego": "#d4a72c", "Not You": "#8c959f"}


def _config():
    with open(CONFIG, "rb") as f:
        return tomllib.load(f)


def _target_colours():
    """app.py's target colours, read from its source so Streamlit need not be importable."""
    source = (REPO_ROOT / "app.py").read_text(encoding="utf-8")
    block = re.search(r"_TARGET_COLORS = \{.*?\"range\": \[(.*?)\]\}", source, re.S).group(1)
    return re.findall(r'"(#[0-9a-f]{6})"', block)


def test_label_colours_are_the_shared_ones():
    theme = _config()["theme"]
    # Streamlit's green, orange and gray tokens colour the cards' labels.
    assert (theme["greenColor"], theme["orangeColor"], theme["grayColor"]) == tuple(LABEL_COLOURS.values())
    # The target's dots and rings use the same three, in the same order.
    assert _target_colours() == list(LABEL_COLOURS.values())


def test_theme_is_the_scoresheet():
    theme = _config()["theme"]
    assert theme["base"] == "light"
    assert theme["primaryColor"] == "#1d3c78"
    assert theme["backgroundColor"] == "#eef3f8"
    assert theme["textColor"] == "#1f2328"
    assert theme["baseRadius"] == "none"
    assert theme["font"].startswith("Barlow,")
    assert theme["headingFont"].startswith("Barlow Condensed,")


def test_fonts_are_served_by_the_page_itself():
    config = _config()
    assert config["server"]["address"] == "localhost"
    assert config["server"]["enableStaticServing"] is True
    faces = config["theme"]["fontFaces"]
    assert {(f["family"], f["weight"]) for f in faces} >= {("Barlow", 400), ("Barlow Condensed", 700)}
    for face in faces:
        assert face["url"].startswith("app/static/fonts/"), face["url"]
        assert (REPO_ROOT / "static" / "fonts" / face["url"].rsplit("/", 1)[1]).is_file()
    # No font, stylesheet or image from another host anywhere in the theme.
    assert "http" not in CONFIG.read_text(encoding="utf-8").split("[theme]", 1)[1]


def test_logo_files_ship_with_the_app():
    mark = (REPO_ROOT / "static" / "logo-mark.svg").read_text(encoding="utf-8")
    # The mark is the target in miniature: both rings and the centre cross, in the shared colours.
    for colour in ("#d4a72c", "#1a7f37", "#1d3c78"):
        assert colour in mark
    assert "http" not in mark.replace("http://www.w3.org/2000/svg", "")
    assert (REPO_ROOT / "static" / "logo-lockup.png").stat().st_size > 1000


def test_no_deploy_toolbar():
    # The page is a local tool: Streamlit's Deploy button and developer menu stay hidden.
    assert _config()["client"]["toolbarMode"] == "viewer"
