---
name: music-downloader
description: "基于 musicdl 匿名搜索、列出候选、按编号下载和检查音乐文件，适用于用户希望下载歌曲、专辑或歌单的个人非商业场景。不用于绕过 DRM、付费、订阅、地区或账号访问限制。"
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

1. 用户要求下载歌曲时先运行 `search`，从结果中保留歌名和歌手匹配且具有可下载地址的候选
2. 找到多个合理候选时，必须展示编号、歌名、歌手、专辑、格式、大小、时长、码率和来源，不得代替用户选择，也不得展示媒体直链
3. 明确提示用户回复 `1`、`2` 等编号；收到编号后使用同一份候选清单运行 `download`。编号无效时重新提示，媒体地址过期时重新搜索
4. 只有一个合理候选时可以直接下载；包含不同歌手、现场版、伴奏、翻唱或重混等情况时，即使格式相同也要让用户选择
5. 收到歌单链接时，先运行 `playlist` 生成清单并报告曲目数量，确认下载范围后再下载
6. 下载后对所选文件运行 `inspect`，最后报告工具返回的真实文件名、绝对路径以及下载失败的项目

展示候选时只陈述可验证信息。不要把平台返回的结果称为“正版”，也不要仅凭格式或文件大小使用“无损”“音质最好”等结论；可以解释具体差异，但最终选择权属于用户。

命令示例：

```text
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py search "歌曲名或歌手名" --catalog search.json --output-dir downloads
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py download --catalog search.json --select 1 --output-dir downloads
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py playlist "歌单地址" --catalog playlist.json --output-dir downloads
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py inspect "downloads/song.flac"
```

使用 `--sources` 缩小搜索范围。优先使用用户指定的平台，否则查询全部默认中国大陆音乐源。选择音乐源时，阅读 [音乐源与匿名解析](references/providers.md)。

## 匿名访问和第三方解析

本技能不读取浏览器 Cookie、不接受账号凭证，也不提供登录模式。网易云、QQ 音乐和酷我音乐适配器在匿名模式下可能调用 `musicdl` 内置的第三方解析服务；这是本技能的默认行为，不要为此单独中断下载流程要求用户确认。

首次报告结果时，简短说明曾查询匿名音乐源且可能使用第三方解析。不得暗示第三方解析服务会赋予用户合法访问权限，也不得输出带签名的媒体地址。

处理需要登录、付费、加密或受限的内容前，阅读 [安全与使用边界](references/safety.md)。

## 下载规则

- 保留已有文件，除非用户明确要求，否则不得覆盖
- 下载文件默认命名为“歌曲名 - 歌手.扩展名”；发生重名时追加编号
- 候选清单和下载文件应保存在用户选择的目录中
- 媒体地址可能过期，因此候选清单只适合短期使用；地址失效时重新搜索
- 对扩展名、码率、时长或标称无损音质存疑时，使用 `inspect` 检查
- 不得仅根据 FLAC 扩展名或文件大小断言音频是真无损
- 向用户提供文件链接时，链接文字和目标都应来自 `download` 返回的实际路径，不要自行拼接或改写文件名
- 不得为了绕过 DRM 或访问限制而安装或调用解密工具
