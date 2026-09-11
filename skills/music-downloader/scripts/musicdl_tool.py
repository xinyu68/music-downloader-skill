#!/usr/bin/env python3
"""面向 Codex 智能体的 musicdl 结构化命令行工具。"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 默认只选择常用的中国大陆音乐源，避免无目的地请求全部平台。
DEFAULT_SOURCES = (
    "MiguMusicClient",
    "NeteaseMusicClient",
    "QQMusicClient",
    "KuwoMusicClient",
    "QianqianMusicClient",
)
CATALOG_VERSION = 1


class ChineseArgumentParser(argparse.ArgumentParser):
    """把 argparse 的固定帮助标题转换为中文。"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # argparse 自带的帮助选项为英文，因此在所有主命令和子命令中统一替换。
        kwargs["add_help"] = False
        super().__init__(*args, **kwargs)
        self.add_argument("-h", "--help", action="help", help="显示帮助信息并退出")

    def format_help(self) -> str:
        return (
            super()
            .format_help()
            .replace("usage:", "用法：")
            .replace("positional arguments:", "位置参数：")
            .replace("options:", "选项：")
        )


def configure_stdio() -> None:
    """统一使用 UTF-8 输出，避免 Windows 控制台出现中文乱码。"""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def load_json(path: Path) -> Any:
    """以 UTF-8 编码读取 JSON 文件。"""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, value: Any) -> None:
    """先写临时文件再替换目标，避免中断后留下不完整清单。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temporary.replace(path)


def parse_sources(value: str | None) -> list[str]:
    """解析音乐源列表，并在保持顺序的同时去重。"""
    values = [item.strip() for item in (value or ",".join(DEFAULT_SOURCES)).split(",")]
    return list(dict.fromkeys(item for item in values if item))


def parse_selection(value: str, maximum: int) -> list[int]:
    """解析 `1,3-5` 形式的候选编号。"""
    selected: set[int] = set()
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start, end = int(start_text), int(end_text)
            if start > end:
                raise ValueError(f"编号范围不能倒序：{token}")
            selected.update(range(start, end + 1))
        else:
            selected.add(int(token))
    invalid = sorted(number for number in selected if number < 1 or number > maximum)
    if invalid:
        raise ValueError(f"所选编号超出 1..{maximum}：{invalid}")
    if not selected:
        raise ValueError("没有选择任何候选编号")
    return sorted(selected)


def safe_filename_component(value: Any, fallback: str) -> str:
    """清理文件名片段，并保留便于识别的中文、字母和数字。"""
    text = str(value or "").strip()
    if text.lower() in {"", "null", "none"}:
        text = fallback
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", text)
    text = re.sub(r"\s+", " ", text).strip(" .")
    return (text or fallback)[:80].rstrip(" .")


def build_unique_media_path(
    output_dir: Path,
    song_name: Any,
    singers: Any,
    identifier: Any,
    extension: Any,
    reserved_paths: set[str] | None = None,
) -> Path:
    """生成“歌曲名 - 歌手”文件名，并避让已有文件和本批次预留路径。"""
    reserved_paths = reserved_paths if reserved_paths is not None else set()
    title = safe_filename_component(song_name, "未知歌曲")
    artist = safe_filename_component(singers, str(identifier or "未知歌手"))
    ext = re.sub(r"[^A-Za-z0-9]", "", str(extension or "bin").lstrip(".")) or "bin"
    stem = f"{title} - {artist}"
    candidate = output_dir / f"{stem}.{ext}"
    index = 1
    while candidate.exists() or str(candidate).casefold() in reserved_paths:
        candidate = output_dir / f"{stem} ({index}).{ext}"
        index += 1
    reserved_paths.add(str(candidate).casefold())
    return candidate


def require_musicdl() -> tuple[Any, Any]:
    """延迟导入 musicdl，让帮助命令在未安装依赖时仍可使用。"""
    try:
        from musicdl import musicdl
        from musicdl.modules import SongInfo
    except ImportError as error:
        raise RuntimeError(
            "当前 Python 环境未安装 musicdl，请先运行 scripts/bootstrap.py"
        ) from error
    return musicdl, SongInfo


def make_client(sources: list[str], output_dir: Path) -> Any:
    """创建匿名访问、限定音乐源和输出目录的 musicdl 客户端。"""
    musicdl_module, _ = require_musicdl()
    output_dir.mkdir(parents=True, exist_ok=True)
    return musicdl_module.MusicClient(
        music_sources=sources,
        init_music_clients_cfg={source: {"work_dir": str(output_dir)} for source in sources},
    )


def json_safe(value: Any) -> Any:
    """把上游返回值递归转换为可序列化的 JSON 数据。"""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return str(value)


def safe_headers(value: Any) -> dict[str, Any]:
    """保留下载所需的普通请求头，同时过滤潜在凭证。"""
    if not isinstance(value, dict):
        return {}
    sensitive_fragments = ("authorization", "cookie", "token", "secret", "api-key", "apikey")
    return {
        str(key): json_safe(item)
        for key, item in value.items()
        if not any(fragment in str(key).lower() for fragment in sensitive_fragments)
    }


def song_to_record(song: Any, number: int) -> dict[str, Any] | None:
    """把普通 URL 类型的歌曲信息转换为可持久化候选记录。"""
    if not isinstance(song.download_url, str):
        return None
    fields = (
        "source", "root_source", "song_name", "singers", "album", "ext",
        "file_size_bytes", "file_size", "duration_s", "duration", "bitrate",
        "codec", "samplerate", "channels", "lyric", "cover_url", "download_url",
        "download_url_status", "chunk_size", "protocol", "identifier",
    )
    record = {field: json_safe(getattr(song, field, None)) for field in fields}
    record["default_download_headers"] = safe_headers(getattr(song, "default_download_headers", None))
    record["number"] = number
    return record


def flatten_results(results: Any) -> list[Any]:
    """把 musicdl 按音乐源分组的结果展开为单一列表。"""
    if isinstance(results, dict):
        return [song for songs in results.values() for song in (songs or [])]
    return list(results or [])


def create_catalog(kind: str, query: str, sources: list[str], songs: list[Any]) -> dict[str, Any]:
    """创建不包含 Cookie 和认证请求头的短期候选清单。"""
    items: list[dict[str, Any]] = []
    skipped = 0
    for song in songs:
        record = song_to_record(song, len(items) + 1)
        if record is None:
            skipped += 1
        else:
            items.append(record)
    return {
        "catalog_version": CATALOG_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "query": query,
        "sources": sources,
        "skipped_non_url_items": skipped,
        "items": items,
    }


def print_items(items: list[dict[str, Any]]) -> None:
    """输出便于用户选择的紧凑候选列表。"""
    if not items:
        print("没有找到可下载的结果")
        return
    for item in items:
        print(
            f"{item['number']:>3}. {item.get('song_name') or '-'} | "
            f"{item.get('singers') or '-'} | {item.get('album') or '-'} | "
            f"{item.get('ext') or '-'} | {item.get('file_size') or '-'} | "
            f"{item.get('source') or '-'}"
        )


def run_check(_: argparse.Namespace) -> int:
    """检查 Python 依赖以及可选的外部媒体工具。"""
    status: dict[str, Any] = {
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "ffmpeg": shutil.which("ffmpeg"),
        "N_m3u8DL-RE": shutil.which("N_m3u8DL-RE"),
        "mp4decrypt": shutil.which("mp4decrypt"),
        "musicdl": None,
    }
    try:
        import musicdl

        status["musicdl"] = getattr(musicdl, "__version__", "unknown")
    except ImportError:
        pass
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["musicdl"] else 2


def common_context(args: argparse.Namespace) -> tuple[list[str], Path]:
    """整理搜索和歌单命令共用的运行参数。"""
    sources = parse_sources(args.sources)
    output_dir = Path(args.output_dir).expanduser().resolve()
    return sources, output_dir


def run_search(args: argparse.Namespace) -> int:
    """搜索歌曲并写入候选清单。"""
    sources, output_dir = common_context(args)
    client = make_client(sources, output_dir)
    songs = flatten_results(client.search(keyword=args.query))
    catalog = create_catalog("search", args.query, sources, songs)
    catalog_path = Path(args.catalog).expanduser().resolve()
    save_json(catalog_path, catalog)
    print_items(catalog["items"])
    print(f"候选清单：{catalog_path}")
    return 0 if catalog["items"] else 1


def run_playlist(args: argparse.Namespace) -> int:
    """解析歌单并写入候选清单。"""
    sources, output_dir = common_context(args)
    client = make_client(sources, output_dir)
    songs = flatten_results(client.parseplaylist(args.url))
    catalog = create_catalog("playlist", args.url, sources, songs)
    catalog_path = Path(args.catalog).expanduser().resolve()
    save_json(catalog_path, catalog)
    print_items(catalog["items"])
    print(f"候选清单：{catalog_path}")
    return 0 if catalog["items"] else 1


def validate_catalog(data: Any) -> dict[str, Any]:
    """检查候选清单版本和必要结构。"""
    if not isinstance(data, dict) or data.get("catalog_version") != CATALOG_VERSION:
        raise ValueError("候选清单无效或版本不受支持")
    if not isinstance(data.get("items"), list):
        raise ValueError("候选清单缺少项目列表")
    return data


def run_download(args: argparse.Namespace) -> int:
    """重建所选歌曲信息并交给对应的 musicdl 客户端下载。"""
    catalog_path = Path(args.catalog).expanduser().resolve()
    catalog = validate_catalog(load_json(catalog_path))
    items = catalog["items"]
    selected_numbers = list(range(1, len(items) + 1)) if args.all else parse_selection(args.select, len(items))
    selected = [items[number - 1] for number in selected_numbers]
    sources = list(dict.fromkeys(str(item["source"]) for item in selected))
    output_dir = Path(args.output_dir).expanduser().resolve()
    client = make_client(sources, output_dir)
    _, SongInfo = require_musicdl()
    songs = []
    reserved_paths: set[str] = set()
    for item in selected:
        payload = {key: value for key, value in item.items() if key != "number"}
        payload["work_dir"] = str(output_dir)
        song = SongInfo.fromdict(payload)
        # musicdl 默认使用平台歌曲 ID 命名；这里改为便于用户识别的歌名和歌手。
        song._save_path = str(
            build_unique_media_path(
                output_dir,
                item.get("song_name"),
                item.get("singers"),
                item.get("identifier"),
                item.get("ext"),
                reserved_paths,
            )
        )
        songs.append(song)
    downloaded = client.download(songs)
    result = {
        "requested": len(songs),
        "downloaded": len(downloaded),
        "files": [str(Path(song.save_path).resolve()) for song in downloaded],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if len(downloaded) == len(songs) else 1


def run_inspect(args: argparse.Namespace) -> int:
    """读取本地音频的容器、时长、码率和标签信息。"""
    try:
        from mutagen import File as MutagenFile
        from tinytag import TinyTag
    except ImportError as error:
        raise RuntimeError("缺少音频检查依赖，请运行 bootstrap.py") from error
    path = Path(args.path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    audio = MutagenFile(path)
    tag = TinyTag.get(str(path))
    result = {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "container": audio.__class__.__name__ if audio else None,
        "duration_seconds": round(tag.duration, 3) if tag.duration else None,
        "bitrate_kbps": round(tag.bitrate, 3) if tag.bitrate else None,
        "sample_rate_hz": tag.samplerate,
        "channels": tag.channels,
        "title": tag.title,
        "artist": tag.artist,
        "album": tag.album,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if audio else 1


def run_sources(_: argparse.Namespace) -> int:
    """列出当前上游版本注册的全部音乐客户端。"""
    require_musicdl()
    from musicdl.modules import MusicClientBuilder

    for name in sorted(MusicClientBuilder.REGISTERED_MODULES):
        print(name)
    return 0


def add_network_options(parser: argparse.ArgumentParser) -> None:
    """为需要网络请求的子命令添加公共参数。"""
    parser.add_argument("--sources", help="以英文逗号分隔的 musicdl 客户端名称")
    parser.add_argument("--output-dir", default="music-downloads", help="音乐文件输出目录")


def build_parser() -> argparse.ArgumentParser:
    parser = ChineseArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="检查运行环境和外部工具")
    check.set_defaults(handler=run_check)

    sources = subparsers.add_parser("sources", help="列出支持的 musicdl 客户端")
    sources.set_defaults(handler=run_sources)

    search = subparsers.add_parser("search", help="搜索歌曲并写入候选清单")
    search.add_argument("query", help="歌曲名、歌手名或组合关键词")
    search.add_argument("--catalog", default="music-search-results.json", help="候选清单输出路径")
    add_network_options(search)
    search.set_defaults(handler=run_search)

    playlist = subparsers.add_parser("playlist", help="把歌单解析为候选清单")
    playlist.add_argument("url", help="音乐平台歌单地址")
    playlist.add_argument("--catalog", default="music-playlist-results.json", help="候选清单输出路径")
    add_network_options(playlist)
    playlist.set_defaults(handler=run_playlist)

    download = subparsers.add_parser("download", help="下载候选清单中的指定项目")
    download.add_argument("--catalog", required=True, help="搜索或歌单命令生成的候选清单")
    group = download.add_mutually_exclusive_group(required=True)
    group.add_argument("--select", help="候选编号或范围，例如 1,3-5")
    group.add_argument("--all", action="store_true", help="下载清单中的全部项目")
    download.add_argument("--output-dir", default="music-downloads", help="音乐文件输出目录")
    download.set_defaults(handler=run_download)

    inspect_parser = subparsers.add_parser("inspect", help="检查本地音频文件")
    inspect_parser.add_argument("path", help="需要检查的本地音频文件路径")
    inspect_parser.set_defaults(handler=run_inspect)
    return parser


def main() -> int:
    configure_stdio()
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
