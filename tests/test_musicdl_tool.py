from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "skills" / "music-downloader" / "scripts" / "musicdl_tool.py"
SPEC = importlib.util.spec_from_file_location("musicdl_tool", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class MusicDlToolTests(unittest.TestCase):
    """验证候选编号和清单读写等不依赖网络的核心行为。"""

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

    def test_build_readable_media_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = MODULE.build_unique_media_path(
                Path(directory), "那天下雨了", "周杰伦", "550531860", ".flac"
            )
            self.assertEqual(path.name, "那天下雨了 - 周杰伦.flac")

    def test_media_path_does_not_overwrite_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            existing = output_dir / "歌曲 - 歌手.mp3"
            existing.touch()
            path = MODULE.build_unique_media_path(
                output_dir, "歌曲", "歌手", "123", "mp3"
            )
            self.assertEqual(path.name, "歌曲 - 歌手 (1).mp3")

    def test_media_paths_are_unique_within_same_batch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            reserved_paths: set[str] = set()
            first = MODULE.build_unique_media_path(
                Path(directory), "歌曲", "歌手", "123", "mp3", reserved_paths
            )
            second = MODULE.build_unique_media_path(
                Path(directory), "歌曲", "歌手", "456", "mp3", reserved_paths
            )
            self.assertEqual(first.name, "歌曲 - 歌手.mp3")
            self.assertEqual(second.name, "歌曲 - 歌手 (1).mp3")

    def test_filename_replaces_invalid_characters(self) -> None:
        path = MODULE.build_unique_media_path(
            Path("downloads"), '歌:曲?名', '歌/手*名', "123", "flac"
        )
        self.assertEqual(path.name, "歌_曲_名 - 歌_手_名.flac")

    def test_client_uses_anonymous_source_configuration(self) -> None:
        class FakeMusicDlModule:
            @staticmethod
            def MusicClient(**kwargs):
                return kwargs

        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(
                MODULE, "require_musicdl", return_value=(FakeMusicDlModule, None)
            ):
                result = MODULE.make_client(
                    ["NeteaseMusicClient", "QQMusicClient"], Path(directory)
                )

        self.assertEqual(
            set(result["init_music_clients_cfg"]),
            {"NeteaseMusicClient", "QQMusicClient"},
        )
        for config in result["init_music_clients_cfg"].values():
            self.assertEqual(set(config), {"work_dir"})


if __name__ == "__main__":
    unittest.main()
