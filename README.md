# Codex 音乐下载技能

这是一个基于 [musicdl](https://github.com/CharlesPikachu/musicdl) 的 Codex 技能，可用于个人非商业场景下的匿名搜索、候选选择、下载和音频信息检查。

## 让智能体一句话安装

直接对 Codex 说：

> 从 https://github.com/xinyu68/music-downloader-skill/tree/main/skills/music-downloader 安装这个技能

Codex 会通过标准技能安装器识别该 GitHub 路径，并将其安装为 `music-downloader`。安装完成后，下一轮对话即可使用。

## 使用命令安装

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo xinyu68/music-downloader-skill --path skills/music-downloader
```

安装完成后，可以对 Codex 说：

> 帮我下载周杰伦的那天下雨了

找到多个合理结果时，技能会先让用户选择，不会直接下载：

```text
1. 那天下雨了 | 歌手：周杰伦 | 格式：FLAC | 大小：46.22 MB | 时长：00:03:43 | 来源：酷我音乐
2. 那天下雨了 | 歌手：周杰伦 | 格式：MP3  | 大小：8.52 MB  | 时长：00:03:43 | 来源：咪咕音乐

请输入要下载的编号，例如 1 或 2。
```

用户回复 `1` 或 `2` 后，技能使用同一份候选清单下载对应文件。

首次使用时，该技能会在自己的目录内创建隔离的 Python 运行环境，并安装锁定版本的 `musicdl` 依赖，不会污染系统 Python 环境。

## 更新技能

已安装的技能不会随 GitHub 仓库自动更新。需要更新时，直接对 Codex 说：

> 将已安装的 music-downloader 更新为 https://github.com/xinyu68/music-downloader-skill/tree/main/skills/music-downloader 的最新版本

标准安装器为了保护已有文件，不会覆盖同名技能，因此手动更新时需要删除旧目录后重新安装：

```powershell
$SkillPath = Join-Path $env:USERPROFILE '.codex\skills\music-downloader'
if (Test-Path -LiteralPath $SkillPath) {
    Remove-Item -LiteralPath $SkillPath -Recurse -Force
}
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo xinyu68/music-downloader-skill --path skills/music-downloader
```

更新会重新创建首次运行所需的隔离环境。更新完成后，在下一轮对话中使用新版本。

## 主要功能

- 默认匿名查询多个音乐平台并生成统一候选列表
- 多个可下载结果会列出编号、格式、大小、时长、码率和来源，用户回复编号后下载
- 下载文件默认使用“歌曲名 - 歌手.扩展名”，重名时自动追加编号
- 解析歌单并生成曲目清单
- 检查音频格式、文件大小、时长、码率、采样率和声道数
- 支持保存歌词、封面和基础音频标签
- 已有文件默认不覆盖
- 不读取浏览器 Cookie，也不接收账号密码或访问令牌
- 网易云、QQ 音乐和酷我音乐在匿名模式下可能使用 `musicdl` 内置的第三方解析服务

## 使用范围

本项目仅面向个人非商业用途，不包含任何音乐文件或平台账号凭证。

本项目不授权绕过 DRM、付费、订阅、地区限制或账号访问控制。请仅下载公有领域、开放许可、自己拥有或已获得合法访问权限的音频内容。

匿名第三方解析服务可能收到歌曲标识和调用方的网络元数据，其可用性、账号来源和授权方式无法由本项目验证。如果不接受第三方服务，应明确要求仅查询咪咕或千千音乐。

上游 `musicdl` 采用 [PolyForm Noncommercial License 1.0.0](https://github.com/CharlesPikachu/musicdl/blob/master/LICENSE)，使用时需要同时遵守其许可证和相关音乐平台的服务条款。
