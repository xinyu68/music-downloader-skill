---
name: music-downloader
description: Search, select, download, and inspect music files for personal noncommercial use through musicdl. Use when the user asks to find or download a song, album, or playlist, choose an audio quality, save lyrics or cover art, or inspect a downloaded audio file. Do not use to bypass DRM, payment, subscription, regional, or account access controls.
---

# Music Downloader

Use the bundled scripts instead of recreating platform requests. Resolve this skill directory as `SKILL_DIR` before constructing commands.

## Runtime

Run `python "$SKILL_DIR/scripts/bootstrap.py"` when the isolated runtime is missing or `check` reports that `musicdl` cannot be imported. The bootstrap installs the pinned upstream dependency into `$SKILL_DIR/.runtime` and prints the runtime Python path.

Use the printed Python executable for `scripts/musicdl_tool.py`. On Windows it is normally `$SKILL_DIR/.runtime/Scripts/python.exe`; on macOS and Linux it is normally `$SKILL_DIR/.runtime/bin/python`.

Start with:

```text
<runtime-python> <SKILL_DIR>/scripts/musicdl_tool.py check
```

## Workflow

1. For a song request, run `search` and show the numbered candidates. Do not silently pick among multiple plausible matches.
2. After the user identifies a result, run `download` with the catalog and selected number.
3. For a playlist URL, run `playlist` to create a catalog, report the track count, and download only after the requested scope is clear.
4. Report the absolute output paths and any failed items.

Example commands:

```text
<runtime-python> <SKILL_DIR>/scripts/musicdl_tool.py search "song or artist" --catalog search.json --output-dir downloads
<runtime-python> <SKILL_DIR>/scripts/musicdl_tool.py download --catalog search.json --select 1 --output-dir downloads
<runtime-python> <SKILL_DIR>/scripts/musicdl_tool.py playlist "playlist URL" --catalog playlist.json --output-dir downloads
<runtime-python> <SKILL_DIR>/scripts/musicdl_tool.py inspect "downloads/song.flac"
```

Pass `--sources` to keep searches narrow. Prefer the source named by the user; otherwise use the default Mainland China sources. Read [references/providers.md](references/providers.md) when choosing sources or configuring cookies.

## Authentication and third-party resolvers

Use the user's own cookies when an official endpoint requires authentication. Accept cookies only through a local JSON file passed with `--cookies-file`; never print cookie values, place them in commands, commit them, or include them in the result catalog.

Without user cookies, NetEase and QQ may use third-party resolver APIs. Explain this before adding `--allow-third-party`. A prior explicit instruction to use third-party resolution is sufficient for the current task. Never imply that a resolver grants legitimate access rights.

Read [references/safety.md](references/safety.md) before handling authenticated, paid, encrypted, or restricted content.

## Download behavior

- Preserve existing files; do not overwrite them unless the user explicitly asks.
- Keep catalogs and output inside the user-selected directory.
- Treat a catalog as short-lived because media URLs can expire; rerun the search when a download URL has expired.
- Use `inspect` when the extension, bitrate, duration, or claimed lossless quality is in doubt.
- Do not claim that FLAC is truly lossless based only on its extension or file size.
- Do not install or invoke decryption tooling to bypass DRM or access controls.
