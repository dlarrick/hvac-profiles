"""Unit tests for scripts/build_site.py."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_site as bs  # noqa: E402


class BuildSiteTests(unittest.TestCase):
    def test_build_site_generates_compact_index_and_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "_site"
            count = bs.build_site(out_dir)
            self.assertGreaterEqual(count, 5)

            self.assertTrue((out_dir / "index.html").is_file())
            index_path = out_dir / "v1" / "index.json"
            self.assertTrue(index_path.is_file())

            index_data = json.loads(index_path.read_text(encoding="utf-8"))
            self.assertEqual(index_data["version"], 1)
            self.assertEqual(index_data["url_template"], "producers/{id}.json")
            self.assertEqual(
                index_data["fields"], ["id", "make", "series", "model", "type", "fuel"]
            )
            self.assertEqual(len(index_data["rows"]), count)

            rows_by_id = {row[0]: row for row in index_data["rows"]}
            # Propane and natural_gas both normalize to "gas"
            self.assertEqual(rows_by_id["bradford_white/bmfthw"][5], "gas")
            self.assertEqual(rows_by_id["burnham/alta"][5], "gas")
            # Heat pumps normalize to "electric"
            self.assertEqual(rows_by_id["mitsubishi/mxz_xcxxnahz2"][5], "electric")

            # Every indexed profile must exist under v1/producers/
            for profile_id in rows_by_id:
                profile_file = out_dir / "v1" / "producers" / f"{profile_id}.json"
                self.assertTrue(profile_file.is_file(), f"Missing {profile_file}")
                # Verify published JSON is valid
                json.loads(profile_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
