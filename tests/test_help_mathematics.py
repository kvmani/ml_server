"""Guards for the offline mathematics rendering used by the scientific help pages."""

from pathlib import Path

import pytest

from ml_server.tool_help import TOOL_HELP


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "src" / "ml_server" / "static" / "vendor" / "mathjax"


def test_mathjax_bundle_is_vendored_for_offline_use() -> None:
    """The intranet has no CDN access, so the bundle must ship with the portal."""
    bundle = VENDOR / "tex-chtml-full.js"
    assert bundle.is_file()
    # The "full" component embeds every TeX extension, so nothing is fetched lazily.
    assert bundle.stat().st_size > 500_000
    assert (VENDOR / "LICENSE").is_file()


def test_mathjax_web_fonts_are_vendored() -> None:
    fonts = sorted((VENDOR / "output" / "chtml" / "fonts" / "woff-v2").glob("*.woff"))
    assert len(fonts) >= 15
    names = {font.name for font in fonts}
    assert "MathJax_Math-Italic.woff" in names
    assert "MathJax_Size4-Regular.woff" in names


def test_mathjax_configuration_never_points_at_a_cdn() -> None:
    config = (ROOT / "src" / "ml_server" / "static" / "js" / "mathjax-config.js").read_text(
        encoding="utf-8"
    )
    # No remote origin of any kind may appear in an executable position.
    code = "\n".join(
        line for line in config.splitlines() if not line.lstrip().startswith(("*", "/*", "//"))
    )
    assert "http://" not in code
    assert "https://" not in code
    # The font path is deliberately left to MathJax so it resolves relative to
    # the vendored bundle rather than to a hardcoded mount prefix.
    assert "fontURL" not in code


@pytest.mark.parametrize("tool_id", sorted(TOOL_HELP))
def test_every_equation_carries_latex_and_a_spoken_form(tool_id: str) -> None:
    equations = TOOL_HELP[tool_id]["equations"]
    assert equations, f"{tool_id} has no equations"
    for equation in equations:
        assert equation["name"]
        assert equation["tex"].strip(), f"{tool_id}: {equation['name']} has no LaTeX"
        # A spoken form keeps the content accessible to screen readers and
        # readable if the bundle is ever unavailable.
        assert equation["plain"].strip()
        assert equation["meaning"].strip()
        # ASCII-art maths is what made the old help pages look unprofessional.
        assert "sqrt(" not in equation["tex"]
        assert "^(" not in equation["tex"]


@pytest.mark.parametrize("tool_id", sorted(TOOL_HELP))
def test_help_page_typesets_through_the_local_bundle(client, tool_id: str) -> None:
    response = client.get(f"/tools/{tool_id}/help")
    assert response.status_code == 200
    body = response.data.decode("utf-8")
    assert "/static/vendor/mathjax/tex-chtml-full.js" in body
    assert "/static/js/mathjax-config.js" in body
    assert "cdn.jsdelivr.net" not in body
    # Display maths is delimited for MathJax and marked for processing.
    assert body.count('class="equation mathjax"') == len(TOOL_HELP[tool_id]["equations"])
    assert "\\[" in body


def test_vendored_bundle_is_actually_served(client) -> None:
    response = client.get("/static/vendor/mathjax/tex-chtml-full.js")
    assert response.status_code == 200

    font = client.get(
        "/static/vendor/mathjax/output/chtml/fonts/woff-v2/MathJax_Math-Italic.woff"
    )
    assert font.status_code == 200


def test_vendored_assets_are_not_git_ignored() -> None:
    """A generic ``output/`` ignore rule once hid MathJax's entire font directory.

    The files existed on the developer's disk, so every filesystem-level check
    passed while a fresh clone would have shipped without web fonts.
    """
    import subprocess

    tracked = subprocess.run(
        ["git", "ls-files", "src/ml_server/static/vendor/mathjax"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()

    assert any(name.endswith("tex-chtml-full.js") for name in tracked)
    assert sum(1 for name in tracked if name.endswith(".woff")) >= 15
