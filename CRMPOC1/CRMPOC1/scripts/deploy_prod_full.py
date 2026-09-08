"""Backward-compatible production deploy (no menu — production only)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from deploy import build_ui, deploy_production, load_config  # noqa: E402


def main() -> int:
    config = load_config()
    build_ui()
    deploy_production(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
