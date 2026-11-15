"""Unit tests for scripts/validate_profiles.py."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_profiles as vp  # noqa: E402

VALID_HP = {
    "make": "Acme",
    "series": "ColdHeat",
    "model": "AC-24",
    "producer_type": "inverter_heat_pump",
    "min_operational_temp_f": -13.0,
    "heating_performance": {
        "full_load_cop": {"47": 3.2, "17": 2.1, "-13": 1.75},
        "part_load_cop": {"47": 4.0, "17": 2.7},
        "capacity_percentage": {"47": 100.0, "17": 85.0, "-13": 70.0},
    },
}

VALID_BOILER = {
    "make": "Acme",
    "model": "B-100",
    "producer_type": "modulating_boiler",
    "fuel_type": "natural_gas",
    "turndown_ratio": 10.0,
    "rated_afue": 0.95,
}


class ValidateProfilesTests(unittest.TestCase):
    def _run_with_profile(
        self, payload: dict, rel_path: str = "acme/test_unit.json"
    ) -> int:
        with tempfile.TemporaryDirectory() as tmp:
            producers_dir = Path(tmp) / "producers"
            target = producers_dir / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(payload), encoding="utf-8")
            with mock.patch.object(vp, "PRODUCERS_DIR", producers_dir):
                return vp.main()

    def test_repo_profiles_pass(self) -> None:
        self.assertEqual(vp.main(), 0)

    def test_valid_heat_pump_and_boiler_pass(self) -> None:
        self.assertEqual(self._run_with_profile(VALID_HP), 0)
        self.assertEqual(self._run_with_profile(VALID_BOILER), 0)

    def test_rejects_extraneous_legacy_fields(self) -> None:
        for key, val in (
            ("refrigerant", "R410A"),
            ("max_ports", 3),
            ("nominal_heating_btu", 24000),
        ):
            hp = copy.deepcopy(VALID_HP)
            hp[key] = val
            self.assertEqual(self._run_with_profile(hp), 1, f"Should reject {key}")

        boiler = copy.deepcopy(VALID_BOILER)
        boiler["primary_flow_gpm"] = 12.0
        self.assertEqual(self._run_with_profile(boiler), 1)

    def test_rejects_wrong_base_afue(self) -> None:
        for bad_afue in (95, 0.095, 1.05):
            boiler = copy.deepcopy(VALID_BOILER)
            boiler["rated_afue"] = bad_afue
            self.assertEqual(
                self._run_with_profile(boiler), 1, f"Should reject AFUE={bad_afue}"
            )

    def test_rejects_impossible_cop(self) -> None:
        for bad_cop in (0.3, 12.0):
            hp = copy.deepcopy(VALID_HP)
            hp["heating_performance"]["full_load_cop"]["47"] = bad_cop
            self.assertEqual(
                self._run_with_profile(hp), 1, f"Should reject COP={bad_cop}"
            )

    def test_rejects_one_based_capacity_percentage(self) -> None:
        hp = copy.deepcopy(VALID_HP)
        hp["heating_performance"]["capacity_percentage"] = {
            "47": 1.0,
            "17": 0.85,
            "-13": 0.70,
        }
        self.assertEqual(self._run_with_profile(hp), 1)

    def test_rejects_swapped_cop_curves(self) -> None:
        hp = copy.deepcopy(VALID_HP)
        hp["heating_performance"]["full_load_cop"]["47"] = 4.0
        hp["heating_performance"]["part_load_cop"]["47"] = 3.2
        self.assertEqual(self._run_with_profile(hp), 1)

    def test_rejects_celsius_curve_keys(self) -> None:
        hp = copy.deepcopy(VALID_HP)
        hp["heating_performance"]["full_load_cop"] = {"7": 3.2, "-8": 2.1, "-25": 1.7}
        hp["heating_performance"]["part_load_cop"] = {"7": 4.0, "-8": 2.7}
        hp["heating_performance"]["capacity_percentage"] = {
            "7": 100.0,
            "-8": 85.0,
            "-25": 70.0,
        }
        hp["min_operational_temp_f"] = -30.0
        self.assertEqual(self._run_with_profile(hp), 1)

    def test_rejects_temp_below_min_operational_temp(self) -> None:
        hp = copy.deepcopy(VALID_HP)
        hp["min_operational_temp_f"] = -5.0
        self.assertEqual(self._run_with_profile(hp), 1)

    def test_rejects_duplicate_numeric_keys(self) -> None:
        hp = copy.deepcopy(VALID_HP)
        hp["heating_performance"]["full_load_cop"]["47.0"] = 3.2
        self.assertEqual(self._run_with_profile(hp), 1)

    def test_rejects_bad_nesting_or_slug(self) -> None:
        self.assertEqual(
            self._run_with_profile(VALID_BOILER, rel_path="bad_top_level.json"), 1
        )
        self.assertEqual(
            self._run_with_profile(VALID_BOILER, rel_path="Acme/BadCase.json"), 1
        )


if __name__ == "__main__":
    unittest.main()
