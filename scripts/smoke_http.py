"""Wait for a headless Streamlit instance and check its health endpoint."""

from __future__ import annotations

import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

URL = "http://localhost:8501/_stcore/health"


def main() -> int:
    for _ in range(30):
        try:
            with urlopen(URL, timeout=2) as response:  # noqa: S310
                if response.status == 200:
                    print("Streamlit health check: OK")
                    return 0
        except (URLError, TimeoutError):
            pass
        time.sleep(1)
    print(f"Streamlit failed health check: {URL}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
