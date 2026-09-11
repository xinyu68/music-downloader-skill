# Providers and authentication

Use exact musicdl client names with `--sources`.

The default clients are `MiguMusicClient`, `NeteaseMusicClient`, `QQMusicClient`, `KuwoMusicClient`, and `QianqianMusicClient`. Narrow the list whenever the user names a platform; this reduces latency and unnecessary network requests.

## Cookie file

The cookie file is a local JSON object keyed by musicdl client name:

```json
{
  "NeteaseMusicClient": {
    "MUSIC_U": "replace-with-the-user-cookie"
  },
  "QQMusicClient": {
    "uin": "replace-with-the-user-cookie",
    "qm_keyst": "replace-with-the-user-cookie"
  }
}
```

Do not commit this file. Do not show its values in tool output or conversation. Pass its path only through `--cookies-file`.

User cookies cause the NetEase and QQ adapters to prefer official authenticated endpoints. Without them, those adapters can try third-party resolvers only when `--allow-third-party` is present.

## Complex providers

Apple Music and TIDAL may return structured stream objects rather than a reusable HTTP URL. The catalog wrapper intentionally skips those items in its first version. They also require account-specific setup and external media tools. Do not work around this limitation by copying credentials or adding decryption tools without a separately reviewed implementation.

YouTube and some conversion services may download content during the search phase. Do not include them in a broad default search; use them only when the user explicitly names that source and the content is authorized.
