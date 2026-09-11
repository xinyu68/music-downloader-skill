---
name: music-downloader
description: "基于 musicdl 搜索、选择、下载和检查音乐文件，适用于用户希望查找或下载歌曲、专辑、歌单，保存歌词或封面，或者检查已下载音频的个人非商业场景。不用于绕过 DRM、付费、订阅、地区或账号访问限制。"
---

# 音乐下载

使用本技能自带脚本，不要重新实现各音乐平台的请求。构造命令前，先把当前技能目录解析为 `SKILL_DIR`。

## 运行环境

当隔离运行环境不存在，或者 `check` 显示无法导入 `musicdl` 时，运行 `python "$SKILL_DIR/scripts/bootstrap.py"`。该脚本会把锁定版本的上游依赖安装到 `$SKILL_DIR/.runtime`，并输出运行环境中的 Python 路径。

使用输出的 Python 执行 `scripts/musicdl_tool.py`。Windows 上通常为 `$SKILL_DIR/.runtime/Scripts/python.exe`，macOS 和 Linux 上通常为 `$SKILL_DIR/.runtime/bin/python`。

首先检查环境：

```text
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py check
```

## 工作流程

1. 用户要求下载歌曲时，先运行 `search` 并展示带编号的候选项。存在多个合理结果时，不要擅自选择
2. 用户确认结果后，使用候选清单和所选编号运行 `download`
3. 收到歌单链接时，先运行 `playlist` 生成清单并报告曲目数量，确认下载范围后再下载
4. 最后报告输出文件的绝对路径以及下载失败的项目

命令示例：

```text
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py search "歌曲名或歌手名" --catalog search.json --output-dir downloads
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py download --catalog search.json --select 1 --output-dir downloads
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py playlist "歌单地址" --catalog playlist.json --output-dir downloads
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py inspect "downloads/song.flac"
```

使用 `--sources` 缩小搜索范围。优先使用用户指定的平台，否则使用默认的中国大陆音乐源。选择音乐源或配置 Cookie 时，阅读 [音乐源与身份认证](references/providers.md)。

## 身份认证和第三方解析

官方接口需要登录时，使用用户自己的 Cookie。Cookie 只能通过 `--cookies-file` 指定的本地 JSON 文件传入；不得输出 Cookie 值、把它写在命令中、提交到仓库或放入候选清单。

没有用户 Cookie 时，网易云和 QQ 音乐可能调用第三方解析接口。添加 `--allow-third-party` 前要向用户说明这一点；如果用户已在当前任务中明确同意使用第三方解析，则不必重复确认。不得暗示第三方解析服务会赋予用户合法访问权限。

处理需要登录、付费、加密或受限的内容前，阅读 [安全与使用边界](references/safety.md)。

## 下载规则

- 保留已有文件，除非用户明确要求，否则不得覆盖
- 候选清单和下载文件应保存在用户选择的目录中
- 媒体地址可能过期，因此候选清单只适合短期使用；地址失效时重新搜索
- 对扩展名、码率、时长或标称无损音质存疑时，使用 `inspect` 检查
- 不得仅根据 FLAC 扩展名或文件大小断言音频是真无损
- 不得为了绕过 DRM 或访问限制而安装或调用解密工具
