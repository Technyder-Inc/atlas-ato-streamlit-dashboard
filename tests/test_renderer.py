"""Visual contract and HTML injection guards for the reference design."""

from __future__ import annotations

from pathlib import Path

from atlas.data import build_dashboard
from atlas.renderer import render_dashboard

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "data"


def test_all_seven_tabs_and_interactive_linux_detail_exist() -> None:
    html = render_dashboard(build_dashboard(FIXTURES, ROOT))
    for title in [
        "Executive Overview", "Assessments", "NIST Controls", "ATO Documents",
        "POA&M / Risk", "GitHub Delivery", "Linux Guides",
    ]:
        assert title in html
    assert "data-guide" in html
    assert "showGuide(b.dataset.guide)" in html
    assert "data.guides.find(x=>x[0]===selected)" in html
    assert "No records available" in html


def test_palette_and_css_match_original_sample() -> None:
    original = (ROOT / "site" / "reference.html").read_text(encoding="utf-8")
    generated = render_dashboard(build_dashboard(FIXTURES, ROOT))
    original_css = original.split("<style>", 1)[1].split("</style>", 1)[0]
    generated_css = generated.split("<style>", 1)[1].split("</style>", 1)[0]
    assert original_css == generated_css
    assert "linear-gradient(115deg,#112d5d,#2459ac 60%,#6735ad)" in generated_css
    assert "background:white" in generated_css
    assert "#f1f5fc" in generated_css


def test_no_static_csv_values_embedded_in_template() -> None:
    template = (ROOT / "atlas" / "templates" / "dashboard.html").read_text(encoding="utf-8")
    assert "__ATLAS_PAYLOAD__" in template
    assert "Stale user accounts" not in template
    assert "Security Assessment Team" not in template


def test_html_escapes_untrusted_csv_values_and_script_breakouts() -> None:
    payload = build_dashboard(FIXTURES, ROOT)
    payload["meta"]["name"] = '</script><script>alert("x")</script>'
    payload["assessments"][0][0] = '<img src=x onerror=alert(1)>'
    rendered = render_dashboard(payload)
    assert "</script><script>alert" not in rendered
    assert "<img src=x" not in rendered
    assert "\\u003cimg" in rendered


def test_computed_kpis_and_zero_safe_helpers() -> None:
    html = render_dashboard(build_dashboard(FIXTURES, ROOT))
    assert '"assessment_completed":4' in html
    assert '"docs_approved":6' in html
    assert "b > 0 ? Math.round(100*a/b) : 0" in html
    assert "Math.max(0,Math.min(100,Number(p)||0))" in html


def test_chart_labels_are_separate_from_colored_bars() -> None:
    html = render_dashboard(build_dashboard(FIXTURES, ROOT))
    assert "${bar(pct(f),colors[i % colors.length])}<b>${pct(f)}%</b>" in html
