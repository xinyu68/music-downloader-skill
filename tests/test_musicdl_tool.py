from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
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

    def test_default_sources_include_gdstudio(self) -> None:
        self.assertIn("GDStudioMusicClient", MODULE.DEFAULT_SOURCES)
        self.assertEqual(
            MODULE.SOURCE_DISPLAY_NAMES["GDStudioMusicClient"],
            "GD 音乐台",
        )

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

    def test_print_items_includes_selection_details_without_url(self) -> None:
        items = [
            {
                "number": 1,
                "song_name": "那天下雨了",
                "singers": "周杰伦",
                "album": "示例专辑",
                "ext": "flac",
                "file_size": "46.22 MB",
                "duration": "00:03:43",
                "bitrate": "1411 kbps",
                "source": "KuwoMusicClient",
                "download_url": "https://example.invalid/signed-audio",
            }
        ]
        output = io.StringIO()
        with redirect_stdout(output):
            MODULE.print_items(items)

        rendered = output.getvalue()
        self.assertIn("格式：FLAC", rendered)
        self.assertIn("大小：46.22 MB", rendered)
        self.assertIn("时长：00:03:43", rendered)
        self.assertIn("码率：1411 kbps", rendered)
        self.assertIn("来源：酷我音乐", rendered)
        self.assertIn("请输入要下载的编号", rendered)
        self.assertNotIn("signed-audio", rendered)

    def test_print_items_shows_gdstudio_root_source(self) -> None:
        items = [
            {
                "number": 1,
                "song_name": "稻香",
                "singers": "周杰伦",
                "album": "魔杰座",
                "ext": "flac",
                "file_size": "24.81 MB",
                "duration": "00:03:43",
                "source": "GDStudioMusicClient",
                "root_source": "netease",
            }
        ]
        output = io.StringIO()
        with redirect_stdout(output):
            MODULE.print_items(items)

        self.assertIn("来源：GD 音乐台（网易云音乐）", output.getvalue())

    def test_shortlist_renumbers_sparse_candidates(self) -> None:
        catalog = {
            "catalog_version": 1,
            "kind": "search",
            "query": "邓紫棋 海阔天空",
            "sources": ["KuwoMusicClient", "QQMusicClient", "MiguMusicClient"],
            "items": [
                {
                    "number": number,
                    "identifier": f"song-{number}",
                    "source": "MiguMusicClient",
                }
                for number in range(1, 18)
            ],
        }

        shortlist = MODULE.create_shortlist(catalog, [1, 7, 12, 17])

        self.assertEqual(
            [item["number"] for item in shortlist["items"]],
            [1, 2, 3, 4],
        )
        self.assertEqual(
            [item["original_number"] for item in shortlist["items"]],
            [1, 7, 12, 17],
        )
        self.assertEqual(shortlist["items"][2]["identifier"], "song-12")

    def test_nested_shortlist_preserves_original_number(self) -> None:
        catalog = {
            "catalog_version": 1,
            "kind": "shortlist",
            "items": [
                {"number": 1, "original_number": 12, "source": "MiguMusicClient"},
                {"number": 2, "original_number": 17, "source": "NeteaseMusicClient"},
            ],
        }

        shortlist = MODULE.create_shortlist(catalog, [2])

        self.assertEqual(shortlist["items"][0]["number"], 1)
        self.assertEqual(shortlist["items"][0]["original_number"], 17)

    def test_run_shortlist_writes_contiguous_catalog(self) -> None:
        catalog = {
            "catalog_version": 1,
            "kind": "search",
            "query": "测试歌曲",
            "items": [
                {"number": number, "source": "MiguMusicClient"}
                for number in range(1, 5)
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            catalog_path = Path(directory) / "search.json"
            shortlist_path = Path(directory) / "shortlist.json"
            MODULE.save_json(catalog_path, catalog)
            args = SimpleNamespace(
                catalog=str(catalog_path),
                select="2,4",
                output=str(shortlist_path),
            )
            with redirect_stdout(io.StringIO()):
                exit_code = MODULE.run_shortlist(args)
            saved = MODULE.load_json(shortlist_path)

        self.assertEqual(exit_code, 0)
        self.assertEqual([item["number"] for item in saved["items"]], [1, 2])
        self.assertEqual(
            [item["original_number"] for item in saved["items"]], [2, 4]
        )


if __name__ == "__main__":
    unittest.main()
