"""Validate client-maintained CSVs locally and in CI."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atlas.data import DatasetError, build_dashboard  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path(os.environ.get("ATLAS_DATA_DIR", ROOT / "data")))
    args = parser.parse_args()
    try:
        dashboard = build_dashboard(args.data_dir, ROOT)
    except (DatasetError, OSError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {dashboard['meta']['id']} / {dashboard['meta']['name']}")
    for key, value in dashboard["counts"].items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
