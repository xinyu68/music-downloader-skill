# 音乐源与身份认证

使用 `--sources` 时必须填写准确的 musicdl 客户端名称。

默认客户端为 `MiguMusicClient`、`NeteaseMusicClient`、`QQMusicClient`、`KuwoMusicClient` 和 `QianqianMusicClient`。用户指定平台时应缩小客户端范围，以减少等待时间和不必要的网络请求。

## Cookie 文件

Cookie 文件是保存在本地的 JSON 对象，以 musicdl 客户端名称作为键：

```json
{
  "NeteaseMusicClient": {
    "MUSIC_U": "替换为用户自己的 Cookie"
  },
  "QQMusicClient": {
    "uin": "替换为用户自己的 Cookie",
    "qm_keyst": "替换为用户自己的 Cookie"
  }
}
```

不得提交此文件，也不得在工具输出或对话中展示其中的值。只能通过 `--cookies-file` 传入文件路径。

提供用户 Cookie 后，网易云和 QQ 音乐适配器会优先使用需要登录的官方接口。未提供 Cookie 时，只有显式添加 `--allow-third-party` 才能尝试第三方解析服务。

## 复杂音乐源

Apple Music 和 TIDAL 可能返回结构化媒体流对象，而不是可以重复使用的 HTTP 地址。第一版候选清单工具会主动跳过这些项目。它们还需要针对账号的配置和外部媒体工具；在没有单独评审实现方案前，不得通过复制凭证或添加解密工具规避该限制。

YouTube 和部分格式转换服务可能在搜索阶段就下载内容，不要把它们加入大范围默认搜索。只有用户明确指定该来源并且拥有内容访问权限时才可使用。
