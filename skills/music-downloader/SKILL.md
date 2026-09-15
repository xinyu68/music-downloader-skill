---
name: music-downloader
description: "基于 musicdl 匿名搜索、列出候选、按编号下载和检查音乐或有声内容，适用于用户希望下载歌曲、音乐专辑、歌单、有声书或评书的个人非商业场景。不用于绕过 DRM、付费、订阅、地区或账号访问限制。"
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

1. 用户要求下载歌曲时先运行 `search`，从结果中找出歌名和歌手匹配且具有可下载地址的原始编号
2. 找到多个合理候选时，必须将这些原始编号传给 `shortlist` 生成新的短名单。只展示 `shortlist` 输出的连续编号、歌名、歌手、专辑、格式、大小、时长、码率和来源，不得在对话中自行重新编号，也不得展示媒体直链
3. 明确提示用户回复 `1`、`2` 等短名单编号；收到编号后必须使用短名单文件运行 `download`，不得再把编号应用到原始搜索清单。编号无效时重新提示，媒体地址过期时重新搜索并重建短名单
4. 只有一个合理候选时可以直接下载；包含不同歌手、现场版、伴奏、翻唱或重混等情况时，即使格式相同也要让用户选择
5. 收到歌单链接时，先运行 `playlist` 生成清单并报告曲目数量，确认下载范围后再下载
6. 下载后对所选文件运行 `inspect`，最后报告工具返回的真实文件名、绝对路径以及下载失败的项目

### 有声书和评书

识别到有声书、小说、评书或类似分集音频请求时，不运行普通 `search`，而是运行 `audiobook`。该命令默认查询喜马拉雅、懒人听书、荔枝和蜻蜓 FM，不把这些源加入普通歌曲搜索。

1. 运行 `audiobook` 并从结果中筛选书名、作者或主播匹配的合集
2. 有多个合理合集时，使用 `shortlist` 生成连续编号短名单，让用户先选择书籍或专辑
3. 用户选定后，使用该有声书清单运行 `chapters`；只展开用户选中的合集，不得直接下载合集对象
4. 展示章节的连续编号、章节名、所属有声书、主播、格式、大小和时长，让用户选择单个编号、编号范围或全部章节
5. 用户明确范围后，使用章节清单运行 `download`；下载整部作品前必须报告可下载章节数量和合计大小，并获得用户明确选择

有声平台可能在搜索时逐集检查匿名下载地址，因此搜索时间通常比歌曲更长。只能展示和下载匿名可访问的完整章节；对试听片段、付费章节或疑似不完整内容如实说明，不得绕过限制。

展示候选时只陈述可验证信息。不要把平台返回的结果称为“正版”，也不要仅凭格式或文件大小使用“无损”“音质最好”等结论；可以解释具体差异，但最终选择权属于用户。

命令示例：

```text
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py search "歌曲名或歌手名" --catalog search.json --output-dir downloads
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py audiobook "有声书名或主播名" --catalog books.json --output-dir downloads
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py shortlist --catalog search.json --select 1,7,12,17 --output shortlist.json
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py chapters --catalog books-shortlist.json --select 1 --output chapters.json
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py download --catalog shortlist.json --select 1 --output-dir downloads
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py download --catalog chapters.json --select 1,3-5 --output-dir downloads
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py playlist "歌单地址" --catalog playlist.json --output-dir downloads
<运行环境-python> <SKILL_DIR>/scripts/musicdl_tool.py inspect "downloads/song.flac"
```

使用 `--sources` 缩小搜索范围。优先使用用户指定的平台，否则查询全部默认源，包括 GD 音乐台聚合源。选择音乐源时，阅读 [音乐源与匿名解析](references/providers.md)。

## 匿名访问和第三方解析

本技能不读取浏览器 Cookie、不接受账号凭证，也不提供登录模式。GD 音乐台是默认启用的第三方聚合源；网易云、QQ 音乐和酷我音乐适配器在匿名模式下也可能调用 `musicdl` 内置的第三方解析服务。这是本技能的默认行为，不要为此单独中断下载流程要求用户确认。

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
