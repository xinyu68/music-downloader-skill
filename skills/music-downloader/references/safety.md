# Safety and usage boundaries

This skill is intended for personal, noncommercial handling of public-domain, openly licensed, user-owned, or otherwise authorized audio.

`musicdl` is licensed under PolyForm Noncommercial 1.0.0. Keep its installation as an external dependency and preserve the upstream license terms. Do not represent this skill as granting rights to music obtained through a provider.

## Access controls

- Use only account permissions the user already has.
- Do not bypass subscriptions, payment, DRM, regional restrictions, rate limits, or provider access controls.
- Do not install Widevine keys, content decryption modules, account pools, leaked credentials, or wrapper servers to gain access.
- If a provider returns only a preview for an unauthenticated account, report that limitation.

## Third-party resolvers

Third-party resolvers receive at least the song identifier and the caller's network metadata. Their server-side account, cache, and licensing behavior cannot be verified from musicdl. Explain this uncertainty before using `--allow-third-party` and stop if the user does not accept it.

## Local data

- Store cookies outside the skill and repository.
- Never echo cookie content, authorization headers, access tokens, or signed media URLs.
- Catalogs contain short-lived media URLs. Keep them local, do not commit them, and remove them when no longer needed.
- Preserve existing audio files by relying on musicdl's unique-name behavior.
