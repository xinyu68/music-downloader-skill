#!/usr/bin/env python3
"""Structured command-line wrapper around musicdl for Codex agents."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_SOURCES = (
    "MiguMusicClient",
    "NeteaseMusicClient",
    "QQMusicClient",
    "KuwoMusicClient",
    "QianqianMusicClient",
)
THIRD_PARTY_FALLBACK_SOURCES = {"NeteaseMusicClient", "QQMusicClient"}
CATALOG_VERSION = 1


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temporary.replace(path)


def parse_sources(value: str | None) -> list[str]:
    values = [item.strip() for item in (value or ",".join(DEFAULT_SOURCES)).split(",")]
    return list(dict.fromkeys(item for item in values if item))


def parse_selection(value: str, maximum: int) -> list[int]:
    selected: set[int] = set()
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start, end = int(start_text), int(end_text)
            if start > end:
                raise ValueError(f"Invalid descending range: {token}")
            selected.update(range(start, end + 1))
        else:
            selected.add(int(token))
    invalid = sorted(number for number in selected if number < 1 or number > maximum)
    if invalid:
        raise ValueError(f"Selection outside 1..{maximum}: {invalid}")
    if not selected:
        raise ValueError("No result numbers selected")
    return sorted(selected)


def load_cookie_map(path_text: str | None) -> dict[str, dict[str, str]]:
    if not path_text:
        return {}
    path = Path(path_text).expanduser().resolve()
    data = load_json(path)
    if not isinstance(data, dict):
        raise ValueError("Cookie file must contain a JSON object")
    result: dict[str, dict[str, str]] = {}
    for source, cookies in data.items():
        if not isinstance(source, str) or not isinstance(cookies, dict):
            raise ValueError("Cookie file must map source names to cookie objects")
        if not all(isinstance(key, str) and isinstance(value, str) for key, value in cookies.items()):
            raise ValueError(f"Cookies for {source} must contain string keys and values")
        result[source] = cookies
    return result


def require_musicdl() -> tuple[Any, Any]:
    try:
        from musicdl import musicdl
        from musicdl.modules import SongInfo
    except ImportError as error:
        raise RuntimeError(
            "musicdl is not installed in this Python runtime; run scripts/bootstrap.py first"
        ) from error
    return musicdl, SongInfo


def guard_third_party(sources: Iterable[str], cookie_map: dict[str, dict[str, str]], allowed: bool) -> None:
    unauthenticated = sorted(
        source for source in sources if source in THIRD_PARTY_FALLBACK_SOURCES and not cookie_map.get(source)
    )
    if unauthenticated and not allowed:
        joined = ", ".join(unauthenticated)
        raise RuntimeError(
            f"{joined} may contact third-party resolver APIs without user cookies. "
            "Provide --cookies-file or explicitly add --allow-third-party."
        )


def client_config(sources: list[str], output_dir: Path, cookie_map: dict[str, dict[str, str]]) -> dict[str, dict[str, Any]]:
    config: dict[str, dict[str, Any]] = {}
    for source in sources:
        source_config: dict[str, Any] = {"work_dir": str(output_dir)}
        if cookies := cookie_map.get(source):
            source_config.update(
                default_search_cookies=dict(cookies),
                default_download_cookies=dict(cookies),
                default_parse_cookies=dict(cookies),
            )
        config[source] = source_config
    return config


def make_client(sources: list[str], output_dir: Path, cookie_map: dict[str, dict[str, str]]) -> Any:
    musicdl_module, _ = require_musicdl()
    output_dir.mkdir(parents=True, exist_ok=True)
    return musicdl_module.MusicClient(
        music_sources=sources,
        init_music_clients_cfg=client_config(sources, output_dir, cookie_map),
    )


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return str(value)


def safe_headers(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    sensitive_fragments = ("authorization", "cookie", "token", "secret", "api-key", "apikey")
    return {
        str(key): json_safe(item)
        for key, item in value.items()
        if not any(fragment in str(key).lower() for fragment in sensitive_fragments)
    }


def song_to_record(song: Any, number: int) -> dict[str, Any] | None:
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
    if isinstance(results, dict):
        return [song for songs in results.values() for song in (songs or [])]
    return list(results or [])


def create_catalog(kind: str, query: str, sources: list[str], songs: list[Any]) -> dict[str, Any]:
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
    if not items:
        print("No downloadable results found")
        return
    for item in items:
        print(
            f"{item['number']:>3}. {item.get('song_name') or '-'} | "
            f"{item.get('singers') or '-'} | {item.get('album') or '-'} | "
            f"{item.get('ext') or '-'} | {item.get('file_size') or '-'} | "
            f"{item.get('source') or '-'}"
        )


def run_check(_: argparse.Namespace) -> int:
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


def common_context(args: argparse.Namespace) -> tuple[list[str], Path, dict[str, dict[str, str]]]:
    sources = parse_sources(args.sources)
    output_dir = Path(args.output_dir).expanduser().resolve()
    cookie_map = load_cookie_map(args.cookies_file)
    guard_third_party(sources, cookie_map, args.allow_third_party)
    return sources, output_dir, cookie_map


def run_search(args: argparse.Namespace) -> int:
    sources, output_dir, cookie_map = common_context(args)
    client = make_client(sources, output_dir, cookie_map)
    songs = flatten_results(client.search(keyword=args.query))
    catalog = create_catalog("search", args.query, sources, songs)
    catalog_path = Path(args.catalog).expanduser().resolve()
    save_json(catalog_path, catalog)
    print_items(catalog["items"])
    print(f"Catalog: {catalog_path}")
    return 0 if catalog["items"] else 1


def run_playlist(args: argparse.Namespace) -> int:
    sources, output_dir, cookie_map = common_context(args)
    client = make_client(sources, output_dir, cookie_map)
    songs = flatten_results(client.parseplaylist(args.url))
    catalog = create_catalog("playlist", args.url, sources, songs)
    catalog_path = Path(args.catalog).expanduser().resolve()
    save_json(catalog_path, catalog)
    print_items(catalog["items"])
    print(f"Catalog: {catalog_path}")
    return 0 if catalog["items"] else 1


def validate_catalog(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("catalog_version") != CATALOG_VERSION:
        raise ValueError("Unsupported or invalid catalog")
    if not isinstance(data.get("items"), list):
        raise ValueError("Catalog has no item list")
    return data


def run_download(args: argparse.Namespace) -> int:
    catalog_path = Path(args.catalog).expanduser().resolve()
    catalog = validate_catalog(load_json(catalog_path))
    items = catalog["items"]
    selected_numbers = list(range(1, len(items) + 1)) if args.all else parse_selection(args.select, len(items))
    selected = [items[number - 1] for number in selected_numbers]
    sources = list(dict.fromkeys(str(item["source"]) for item in selected))
    output_dir = Path(args.output_dir).expanduser().resolve()
    cookie_map = load_cookie_map(args.cookies_file)
    guard_third_party(sources, cookie_map, args.allow_third_party)
    client = make_client(sources, output_dir, cookie_map)
    _, SongInfo = require_musicdl()
    songs = []
    for item in selected:
        payload = {key: value for key, value in item.items() if key != "number"}
        payload["work_dir"] = str(output_dir)
        payload["default_download_cookies"] = cookie_map.get(str(item["source"]), {})
        songs.append(SongInfo.fromdict(payload))
    downloaded = client.download(songs)
    result = {
        "requested": len(songs),
        "downloaded": len(downloaded),
        "files": [str(Path(song.save_path).resolve()) for song in downloaded],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if len(downloaded) == len(songs) else 1


def run_inspect(args: argparse.Namespace) -> int:
    try:
        from mutagen import File as MutagenFile
        from tinytag import TinyTag
    except ImportError as error:
        raise RuntimeError("Audio inspection dependencies are missing; run bootstrap.py") from error
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
    require_musicdl()
    from musicdl.modules import MusicClientBuilder

    for name in sorted(MusicClientBuilder.REGISTERED_MODULES):
        print(name)
    return 0


def add_network_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--sources", help="Comma-separated musicdl client names")
    parser.add_argument("--output-dir", default="music-downloads", help="Directory for music files")
    parser.add_argument("--cookies-file", help="Local JSON file mapping client names to cookies")
    parser.add_argument(
        "--allow-third-party",
        action="store_true",
        help="Allow third-party resolvers when an official user cookie is unavailable",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Check runtime and external tools")
    check.set_defaults(handler=run_check)

    sources = subparsers.add_parser("sources", help="List supported musicdl clients")
    sources.set_defaults(handler=run_sources)

    search = subparsers.add_parser("search", help="Search and write a result catalog")
    search.add_argument("query")
    search.add_argument("--catalog", default="music-search-results.json")
    add_network_options(search)
    search.set_defaults(handler=run_search)

    playlist = subparsers.add_parser("playlist", help="Parse a playlist into a catalog")
    playlist.add_argument("url")
    playlist.add_argument("--catalog", default="music-playlist-results.json")
    add_network_options(playlist)
    playlist.set_defaults(handler=run_playlist)

    download = subparsers.add_parser("download", help="Download selected catalog entries")
    download.add_argument("--catalog", required=True)
    group = download.add_mutually_exclusive_group(required=True)
    group.add_argument("--select", help="Numbers and ranges, for example 1,3-5")
    group.add_argument("--all", action="store_true")
    download.add_argument("--output-dir", default="music-downloads")
    download.add_argument("--cookies-file")
    download.add_argument("--allow-third-party", action="store_true")
    download.set_defaults(handler=run_download)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect an audio file")
    inspect_parser.add_argument("path")
    inspect_parser.set_defaults(handler=run_inspect)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
