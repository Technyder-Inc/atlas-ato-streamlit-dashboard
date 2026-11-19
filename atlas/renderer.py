"""Render the original Atlas index.html design with safely injected CSV data."""

from __future__ import annotations

import json
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "templates" / "dashboard.html"


def render_dashboard(payload: dict) -> str:
    """Produce standalone, fully interactive HTML with the sample's CSS unchanged."""
    # Avoid </script> breakout even when an administrator edits CSV text.
    safe_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    safe_json = (
        safe_json.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    template = TEMPLATE.read_text(encoding="utf-8")
    if "__ATLAS_PAYLOAD__" not in template:
        raise RuntimeError("Dashboard template missing data placeholder")
    return template.replace("__ATLAS_PAYLOAD__", safe_json)
