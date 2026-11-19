"""Read the seven client-maintained CSV files and build dashboard view data.

The CSVs are the source of truth; the dashboard never embeds static demo rows.
All calculations are refreshed on Streamlit rerun / page reload.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

CSV_COLUMNS: dict[str, tuple[str, ...]] = {
    "applications": ("application_id", "name", "os", "framework", "authorization_status"),
    "assessments": (
        "assessment_id", "application_id", "assessment_name", "status",
        "target_or_completion_date", "owner",
    ),
    "control_families": ("application_id", "family_id", "applicable_controls", "implemented_controls"),
    "ato_documents": ("document_id", "application_id", "document_name", "status"),
    "poams": (
        "poam_id", "application_id", "control_id", "finding", "severity",
        "status", "due_date", "github_issue_number", "owner",
    ),
    "github_activity": (
        "application_id", "issue_number", "poam_id", "issue_status",
        "pr_number", "pr_status", "validation_status",
    ),
    "linux_guides": ("control_id", "application_id", "guide_name", "status", "repository_path"),
}

FAMILY_LABELS = {
    "AC": "Access Control", "AU": "Audit", "CM": "Configuration",
    "IA": "Identity", "SC": "Communications", "SI": "Integrity",
}


class DatasetError(ValueError):
    """A clear, actionable error when the client CSV schema is invalid."""


def read_csv_records(data_dir: Path, name: str) -> list[dict[str, str]]:
    """Read a known UTF-8 CSV with a stable schema and trimmed fields."""
    if name not in CSV_COLUMNS:
        raise DatasetError(f"Unknown dataset: {name}")
    path = Path(data_dir) / f"{name}.csv"
    if not path.is_file():
        raise DatasetError(f"Missing required file: {path}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            columns = reader.fieldnames or []
            missing = set(CSV_COLUMNS[name]) - set(columns)
            if missing:
                raise DatasetError(
                    f"{path.name}: missing columns {', '.join(sorted(missing))}. "
                    "Keep the original column names when updating the CSV."
                )
            records = []
            for index, record in enumerate(reader, start=2):
                if None in record:
                    raise DatasetError(f"{path.name}: extra values at row {index}")
                cleaned = {key: (value or "").strip() for key, value in record.items()}
                if any(cleaned.values()):
                    records.append(cleaned)
            return records
    except UnicodeError as exc:
        raise DatasetError(f"{path.name}: save the file as UTF-8") from exc
    except csv.Error as exc:
        raise DatasetError(f"{path.name}: invalid CSV format ({exc})") from exc


def _nonnegative_integer(value: str, file_name: str, family: str, field: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise DatasetError(f"{file_name}: {family} has invalid {field}: {value!r}") from exc
    if number < 0:
        raise DatasetError(f"{file_name}: {family} {field} must be non-negative")
    return number


def _read_validation_commands(project_root: Path, repo_path: str) -> str:
    """Read only a safe relative guide path, not arbitrary filesystem paths."""
    base = (project_root / "linux" / "rhel9" / "remediation").resolve()
    candidate = (project_root / repo_path).resolve()
    if not candidate.is_relative_to(base) or candidate.suffix.lower() != ".md":
        return "Guide file path is outside the approved remediation directory."
    if not candidate.is_file():
        return "No validation commands found. Review the guide markdown path."
    content = candidate.read_text(encoding="utf-8")
    match = re.search(r"## Validation procedure\b(.*?)(?=\n## |\Z)", content, flags=re.S | re.I)
    if match:
        fenced = re.search(r"```(?:bash|sh|shell)?\s*\n(.*?)\n```", match.group(1), flags=re.S | re.I)
        if fenced:
            return fenced.group(1).strip()
    return "No read-only validation commands documented."


def _count_status(records: list[dict[str, str]], value: str, column: str = "status") -> int:
    return sum(record.get(column, "").casefold() == value.casefold() for record in records)


def build_dashboard(data_dir: Path, project_root: Path, app_id: str | None = None) -> dict:
    """Return data matching the original index.html sections, derived from CSV files."""
    data = {name: read_csv_records(data_dir, name) for name in CSV_COLUMNS}
    applications = data["applications"]
    if not applications:
        raise DatasetError("applications.csv: add at least one application")
    chosen = next(
        (app for app in applications if app["application_id"] == app_id),
        None,
    ) if app_id else applications[0]
    if chosen is None:
        raise DatasetError(f"Application {app_id!r} not present in applications.csv")
    app_key = chosen["application_id"]
    items = {
        name: [row for row in records if row.get("application_id") == app_key]
        for name, records in data.items()
        if name != "applications"
    }

    families: list[list] = []
    for row in items["control_families"]:
        family = row["family_id"]
        applicable = _nonnegative_integer(row["applicable_controls"], "control_families.csv", family, "applicable_controls")
        implemented = _nonnegative_integer(row["implemented_controls"], "control_families.csv", family, "implemented_controls")
        if implemented > applicable:
            raise DatasetError(f"control_families.csv: {family} has more implemented than applicable controls")
        families.append([family, FAMILY_LABELS.get(family, family), applicable, implemented])

    assessments = items["assessments"]
    docs = items["ato_documents"]
    poams = items["poams"]
    guides = items["linux_guides"]
    github = items["github_activity"]
    completed_assessments = _count_status(assessments, "Completed")
    approved_docs = _count_status(docs, "Approved")
    published_guides = _count_status(guides, "Published")
    open_poams = [row for row in poams if row["status"].casefold() not in {"closed", "resolved", "completed"}]
    applicable_count = sum(f[2] for f in families)
    implemented_count = sum(f[3] for f in families)

    counts = {
        "assessment_total": len(assessments),
        "assessment_completed": completed_assessments,
        "assessment_pending": len(assessments) - completed_assessments,
        "control_applicable": applicable_count,
        "control_implemented": implemented_count,
        "control_missing": applicable_count - implemented_count,
        "control_percent": round(100 * implemented_count / applicable_count) if applicable_count else 0,
        "docs_total": len(docs),
        "docs_approved": approved_docs,
        "docs_pending": len(docs) - approved_docs,
        "poams_open": len(open_poams),
        "risk_critical": _count_status(open_poams, "Critical", "severity"),
        "risk_high": _count_status(open_poams, "High", "severity"),
        "guides_total": len(guides),
        "guides_published": published_guides,
        "guides_pending": len(guides) - published_guides,
        "issues": len({x["issue_number"] for x in github if x["issue_number"]}),
        "prs": len({x["pr_number"] for x in github if x["pr_number"]}),
        "validated": sum(
            x["validation_status"].casefold() in {"validated", "approved", "completed"}
            for x in github
        ),
    }

    return {
        "meta": {
            "id": app_key,
            "name": chosen["name"],
            "os": chosen["os"],
            "authorization_status": chosen["authorization_status"],
            "demo": True,
        },
        "counts": counts,
        "assessments": [
            [r["assessment_name"], r["status"], r["target_or_completion_date"], r["owner"]]
            for r in assessments
        ],
        "families": families,
        "docs": [[r["document_name"], r["status"]] for r in docs],
        "poams": [
            [r["poam_id"], r["control_id"], r["finding"], r["severity"], r["status"],
             f"#{r['github_issue_number']}" if r["github_issue_number"] else "—"]
            for r in open_poams
        ],
        "guides": [
            [r["control_id"], r["guide_name"], r["status"],
             _read_validation_commands(project_root, r["repository_path"])]
            for r in guides
        ],
        "github": [
            [f"#{r['issue_number']}" if r["issue_number"] else "—", r["poam_id"],
             r["pr_status"], f"PR #{r['pr_number']}" if r["pr_number"] else "—",
             r["validation_status"]]
            for r in github
        ],
    }
