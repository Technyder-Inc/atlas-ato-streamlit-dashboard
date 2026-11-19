"""Data integrity and future client CSV refresh regression tests."""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest

from atlas.data import DatasetError, build_dashboard, read_csv_records

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "data"


@pytest.fixture()
def data_folder(tmp_path: Path) -> Path:
    shutil.copytree(FIXTURES, tmp_path / "data")
    return tmp_path / "data"


def test_reference_demo_numbers_are_computed_from_csv() -> None:
    payload = build_dashboard(FIXTURES, ROOT)
    assert payload["counts"] == {
        "assessment_total": 6,
        "assessment_completed": 4,
        "assessment_pending": 2,
        "control_applicable": 112,
        "control_implemented": 97,
        "control_missing": 15,
        "control_percent": 87,
        "docs_total": 9,
        "docs_approved": 6,
        "docs_pending": 3,
        "poams_open": 5,
        "risk_critical": 1,
        "risk_high": 2,
        "guides_total": 5,
        "guides_published": 2,
        "guides_pending": 3,
        "issues": 5,
        "prs": 5,
        "validated": 0,
    }


def test_all_seven_csv_files_exist_and_have_required_headers() -> None:
    from atlas.data import CSV_COLUMNS

    for name in CSV_COLUMNS:
        assert isinstance(read_csv_records(ROOT / "data", name), list)


def test_external_csv_updates_change_kpis_without_code_changes(data_folder: Path) -> None:
    path = data_folder / "assessments.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    rows[5]["status"] = "Completed"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    payload = build_dashboard(data_folder, ROOT)
    assert payload["counts"]["assessment_completed"] == 5
    assert payload["counts"]["assessment_pending"] == 1


def test_missing_required_column_has_actionable_error(data_folder: Path) -> None:
    path = data_folder / "poams.csv"
    original = path.read_text(encoding="utf-8")
    path.write_text(original.replace("severity,", "severity_wrong,"), encoding="utf-8")
    with pytest.raises(DatasetError, match="missing columns severity"):
        build_dashboard(data_folder, ROOT)


def test_malformed_csv_with_extra_cells_is_rejected(data_folder: Path) -> None:
    with (data_folder / "applications.csv").open("a", encoding="utf-8") as out:
        out.write("APP-002,Beta,RHEL 9,RMF,In progress,extra value\n")
    with pytest.raises(DatasetError, match="extra values"):
        read_csv_records(data_folder, "applications")


def test_implemented_cannot_exceed_applicable(data_folder: Path) -> None:
    path = data_folder / "control_families.csv"
    content = path.read_text(encoding="utf-8")
    path.write_text(content.replace("APP-001,AC,24,22", "APP-001,AC,24,25"), encoding="utf-8")
    with pytest.raises(DatasetError, match="more implemented"):
        build_dashboard(data_folder, ROOT)


def test_empty_controls_returns_zero_percent(data_folder: Path) -> None:
    (data_folder / "control_families.csv").write_text(
        "application_id,family_id,applicable_controls,implemented_controls\n",
        encoding="utf-8",
    )
    counts = build_dashboard(data_folder, ROOT)["counts"]
    assert (counts["control_percent"], counts["control_applicable"]) == (0, 0)


def test_incomplete_or_closed_poam_not_counted_as_open(data_folder: Path) -> None:
    path = data_folder / "poams.csv"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "Missing security patches,Critical,Open,", "Missing security patches,Critical,Closed,"
    ), encoding="utf-8")
    counts = build_dashboard(data_folder, ROOT)["counts"]
    assert counts["poams_open"] == 4
    assert counts["risk_critical"] == 0


def test_linux_guide_commands_come_from_real_markdown_files() -> None:
    guides = build_dashboard(FIXTURES, ROOT)["guides"]
    by_id = {guide[0]: guide for guide in guides}
    assert by_id["AC-2"][3] == "getent passwd\nsudo chage -l username"
    assert by_id["AU-12"][3] == "sudo systemctl status auditd\nsudo auditctl -l"
    assert by_id["SC-8"][3] == "update-crypto-policies --show"


def test_path_traversal_in_linux_guide_csv_is_blocked(data_folder: Path) -> None:
    path = data_folder / "linux_guides.csv"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "linux/rhel9/remediation/AC-2.md", "../../etc/passwd"
    ), encoding="utf-8")
    guides = build_dashboard(data_folder, ROOT)["guides"]
    assert "outside the approved remediation directory" in guides[0][3]


def test_multiple_applications_are_isolated(data_folder: Path) -> None:
    with (data_folder / "applications.csv").open("a", encoding="utf-8") as out:
        out.write("APP-002,Second Platform,RHEL 9,NIST 800-53,In progress\n")
    second = build_dashboard(data_folder, ROOT, "APP-002")
    assert second["meta"]["name"] == "Second Platform"
    assert second["counts"]["assessment_total"] == 0
    assert second["counts"]["docs_total"] == 0
    with pytest.raises(DatasetError, match="not present"):
        build_dashboard(data_folder, ROOT, "APP-003")
