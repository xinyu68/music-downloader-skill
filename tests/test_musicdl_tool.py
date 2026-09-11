from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "music-downloader" / "scripts" / "musicdl_tool.py"
SPEC = importlib.util.spec_from_file_location("musicdl_tool", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class MusicDlToolTests(unittest.TestCase):
    def test_parse_selection(self) -> None:
        self.assertEqual(MODULE.parse_selection("1,3-5,3", 5), [1, 3, 4, 5])

    def test_reject_invalid_selection(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.parse_selection("0,2", 3)

    def test_catalog_round_trip(self) -> None:
        value = {"catalog_version": 1, "items": [{"number": 1}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            MODULE.save_json(path, value)
            self.assertEqual(MODULE.load_json(path), value)


if __name__ == "__main__":
    unittest.main()
