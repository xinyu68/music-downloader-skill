# Codex 音乐下载技能

这是一个基于 [musicdl](https://github.com/CharlesPikachu/musicdl) 的 Codex 技能，可用于个人非商业场景下的音乐搜索、选择、下载和音频信息检查。

## 让智能体一句话安装

直接对 Codex 说：

> 从 https://github.com/xinyu68/music-downloader-skill/tree/main/skills/music-downloader 安装这个技能

Codex 会通过标准技能安装器识别该 GitHub 路径，并将其安装为 `music-downloader`。安装完成后，下一轮对话即可使用。

## 使用命令安装

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo xinyu68/music-downloader-skill --path skills/music-downloader
```

安装完成后，可以对 Codex 说：

> 用 music-downloader 搜索一首歌，列出结果让我选择后下载

首次使用时，该技能会在自己的目录内创建隔离的 Python 运行环境，并安装锁定版本的 `musicdl` 依赖，不会污染系统 Python 环境。

## 主要功能

- 搜索一个或多个音乐平台并生成统一的候选列表
- 按编号选择并下载歌曲
- 解析歌单并生成曲目清单
- 检查音频格式、文件大小、时长、码率、采样率和声道数
- 支持通过本地 JSON 文件提供用户自己的 Cookie
- 支持保存歌词、封面和基础音频标签
- 已有文件默认不覆盖
- 第三方解析服务必须显式允许后才会调用

## 使用范围

本项目仅面向个人非商业用途，不包含任何音乐文件、平台账号凭证，也没有复制 `musicdl` 的源代码。

本项目不授权绕过 DRM、付费、订阅、地区限制或账号访问控制。请仅下载公有领域、开放许可、自己拥有或已获得合法访问权限的音频内容。

上游 `musicdl` 采用 [PolyForm Noncommercial License 1.0.0](https://github.com/CharlesPikachu/musicdl/blob/master/LICENSE)，使用时需要同时遵守其许可证和相关音乐平台的服务条款。
