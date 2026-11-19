"""Export the same HTML used inside Streamlit to dist/index.html for visual QA."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.data import build_dashboard  # noqa: E402
from atlas.renderer import render_dashboard  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path(os.environ.get("ATLAS_DATA_DIR", ROOT / "data")))
    parser.add_argument("--out", type=Path, default=ROOT / "dist" / "index.html")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_dashboard(build_dashboard(args.data_dir, ROOT)), encoding="utf-8")
    print(f"HTML preview created: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
