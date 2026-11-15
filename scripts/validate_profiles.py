#!/usr/bin/env python3
"""Validate all producer profile JSON files against schema/v1/producer.schema.json."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent
PRODUCERS_DIR = REPO_ROOT / "producers"
SCHEMA_PATH = REPO_ROOT / "schema" / "v1" / "producer.schema.json"

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _parse_curve(
    rel_path: Path, name: str, raw: dict[str, float], errors: list[str]
) -> dict[float, float]:
    """Parse curve keys to floats, checking for numeric duplicates and °F range."""
    parsed: dict[float, float] = {}
    for k, v in raw.items():
        temp_f = float(k)
        if temp_f in parsed:
            errors.append(
                f"{rel_path}: {name} has duplicate numeric temperature key {temp_f}"
            )
        if temp_f < -50.0 or temp_f > 80.0:
            errors.append(
                f"{rel_path}: {name} temperature {temp_f}°F is outside expected [-50, 80]°F range"
            )
        parsed[temp_f] = float(v)

    if parsed and max(parsed) < 30.0:
        errors.append(
            f"{rel_path}: {name} max temperature ({max(parsed)}°F) is below 30°F "
            "(did you accidentally enter °C instead of °F?)"
        )
    return parsed


def _check_physics(rel_path: Path, data: dict) -> list[str]:
    """Run domain-specific sanity checks beyond JSON Schema."""
    errors: list[str] = []
    if data.get("producer_type") == "inverter_heat_pump":
        perf = data["heating_performance"]
        full_cop = _parse_curve(
            rel_path, "full_load_cop", perf["full_load_cop"], errors
        )
        cap_pct = _parse_curve(
            rel_path, "capacity_percentage", perf["capacity_percentage"], errors
        )
        part_cop = (
            _parse_curve(rel_path, "part_load_cop", perf["part_load_cop"], errors)
            if "part_load_cop" in perf
            else {}
        )

        # Ensure capacity_percentage is 100-based (not 0..1)
        if cap_pct and max(cap_pct.values()) < 50.0:
            errors.append(
                f"{rel_path}: capacity_percentage max ({max(cap_pct.values())}) is < 50; "
                "must be 100-based (e.g. 100.0 at 47°F, not 1.0)"
            )

        # Catch swapped full_load_cop / part_load_cop
        for temp_f in sorted(set(full_cop) & set(part_cop)):
            if part_cop[temp_f] < full_cop[temp_f]:
                errors.append(
                    f"{rel_path}: part_load_cop ({part_cop[temp_f]}) < full_load_cop "
                    f"({full_cop[temp_f]}) at {temp_f}°F (curves may be swapped)"
                )

        min_op = data.get("min_operational_temp_f")
        if min_op is not None:
            for name, curve in (
                ("full_load_cop", full_cop),
                ("part_load_cop", part_cop),
                ("capacity_percentage", cap_pct),
            ):
                if curve and min(curve) < min_op:
                    errors.append(
                        f"{rel_path}: {name} has temp {min(curve)}°F "
                        f"below min_operational_temp_f ({min_op}°F)"
                    )
    return errors


def main() -> int:
    if not SCHEMA_PATH.exists():
        print(f"ERROR: Schema not found at {SCHEMA_PATH}", file=sys.stderr)
        return 1

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    profile_files = sorted(PRODUCERS_DIR.rglob("*.json"))
    if not profile_files:
        print(
            f"ERROR: No profile JSON files found under {PRODUCERS_DIR}", file=sys.stderr
        )
        return 1

    errors: list[str] = []
    for path in profile_files:
        rel_path = path.relative_to(PRODUCERS_DIR)
        parts = rel_path.parts
        if len(parts) != 2:
            errors.append(
                f"{rel_path}: must be nested exactly 2 levels under producers/ "
                "(<manufacturer>/<model>.json)"
            )
            continue

        make_slug, model_file = parts
        model_slug = model_file[:-5]
        if not SLUG_RE.match(make_slug) or not SLUG_RE.match(model_slug):
            errors.append(
                f"{rel_path}: directory and filename slugs must match ^[a-z0-9][a-z0-9_-]*$"
            )

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            errors.append(f"{rel_path}: invalid JSON ({err})")
            continue

        schema_errs = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        if schema_errs:
            for err in schema_errs:
                loc = ".".join(str(p) for p in err.path) or "<root>"
                errors.append(f"{rel_path} [{loc}]: {err.message}")
            continue

        errors.extend(_check_physics(rel_path, data))

    if errors:
        print(f"Validation FAILED ({len(errors)} error(s)):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"Validated {len(profile_files)} producer profile(s) successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
