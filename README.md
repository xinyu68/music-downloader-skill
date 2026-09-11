# Music Downloader Skill for Codex

A Codex skill that searches, selects, downloads, and inspects music for personal noncommercial use through [musicdl](https://github.com/CharlesPikachu/musicdl).

## Install by asking an agent

Tell Codex:

> 从 https://github.com/xinyu68/music-downloader-skill/tree/main/skills/music-downloader 安装这个 skill

The standard skill installer recognizes that GitHub path and installs it as `music-downloader`. It becomes available on the next turn.

## Direct install

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo xinyu68/music-downloader-skill --path skills/music-downloader
```

After installation, ask:

> 用 music-downloader 搜索一首歌，列出结果让我选择后下载

The first use creates an isolated Python runtime inside the installed skill and installs the pinned `musicdl` dependency.

## Scope

This project does not contain music, platform credentials, or copied musicdl source code. It does not authorize bypassing DRM, payment, subscription, regional, or account access controls. The upstream dependency uses the [PolyForm Noncommercial License 1.0.0](https://github.com/CharlesPikachu/musicdl/blob/master/LICENSE).
