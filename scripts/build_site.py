#!/usr/bin/env python3
"""Build the static GitHub Pages site with /v1/index.json (table JSON) and profiles."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

REPO_ROOT = Path(__file__).resolve().parent.parent
PRODUCERS_DIR = REPO_ROOT / "producers"

INDEX_FIELDS = ["id", "make", "series", "model", "type", "fuel"]


def _normalize_fuel(data: dict) -> str:
    """Map equipment fuel_type into a coarse index category."""
    if data.get("producer_type") == "inverter_heat_pump":
        return "electric"
    fuel = str(data.get("fuel_type", "")).lower()
    if fuel in ("natural_gas", "propane"):
        return "gas"
    return fuel


def build_site(output_dir: Path) -> int:
    v1_dir = output_dir / "v1"
    v1_producers_dir = v1_dir / "producers"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    v1_producers_dir.mkdir(parents=True, exist_ok=True)

    rows: list[list[str]] = []
    for src_path in sorted(PRODUCERS_DIR.rglob("*.json")):
        rel_path = src_path.relative_to(PRODUCERS_DIR)
        profile_id = rel_path.with_suffix("").as_posix()

        data = json.loads(src_path.read_text(encoding="utf-8"))
        rows.append(
            [
                profile_id,
                str(data.get("make", "")),
                str(data.get("series", "")),
                str(data.get("model", "")),
                str(data.get("producer_type", "")),
                _normalize_fuel(data),
            ]
        )

        dst_path = v1_producers_dir / rel_path
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        # Write minified JSON for published profiles
        dst_path.write_text(
            json.dumps(data, separators=(",", ":"), ensure_ascii=False),
            encoding="utf-8",
        )

    index_payload = {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fields": INDEX_FIELDS,
        "rows": rows,
    }
    (v1_dir / "index.json").write_text(
        json.dumps(index_payload, separators=(",", ":"), ensure_ascii=False),
        encoding="utf-8",
    )

    (output_dir / "index.html").write_text(
        """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>HVAC Profiles</title></head>
<body>
  <h1>HVAC Profiles</h1>
  <p>Machine-readable equipment profile index: <a href="v1/index.json">v1/index.json</a></p>
  <p>Source &amp; License (CC BY-SA 4.0): <a href="https://github.com/dlarrick/hvac-profiles">github.com/dlarrick/hvac-profiles</a></p>
</body>
</html>
""",
        encoding="utf-8",
    )
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "_site",
        help="Output directory for generated static site (default: _site)",
    )
    args = parser.parse_args()
    count = build_site(args.output)
    print(f"Built site at {args.output} with {count} profile(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
