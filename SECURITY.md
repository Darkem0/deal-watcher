# Security policy

## Supported scope

Deal Watcher monitors public listings and emits notifications. It does not purchase products, add items to a cart, reserve stock, solve CAPTCHAs, rotate proxies, spoof fingerprints, collect cookies, or weaken access controls.

Akakçe live access is not verified and is disabled by default after controlled direct HTTP access returned HTTP 403.

## Reporting a vulnerability

Report security issues through a private channel to the repository owner. Do not open a public issue containing secrets, personal data, private logs, or an exploitable proof of concept before coordinated review.

Include:

- affected version or commit;
- operating system and Python version;
- a concise reproduction using synthetic or redacted data;
- expected and actual behavior;
- impact assessment;
- suggested mitigation, when available.

Never include:

- Telegram bot tokens or chat IDs;
- `.env` contents;
- cookies, Authorization headers, or session data;
- SQLite databases or unredacted log files;
- personal information copied from a forum page.

## Secret exposure

If a Telegram token is exposed, revoke or rotate it with BotFather before continuing. Removing a secret from the latest file is not enough when it has entered Git history; treat it as compromised and rewrite history only after coordinating with repository users.

## Responsible source access

Source adapters must follow [`docs/source-access-policy.md`](docs/source-access-policy.md). A 403, CAPTCHA, or anti-bot response is a stop condition, not an invitation to bypass the protection.

---

# Güvenlik politikası — Türkçe özet

Deal Watcher yalnızca herkese açık fırsatları izler ve bildirim üretir. CAPTCHA, proxy rotation, stealth, fingerprint değiştirme, cookie toplama veya erişim kontrolü aşma uygulanmaz. Otomatik satın alma, sepet, ödeme ve stok rezervasyonu yoktur.

Güvenlik sorunlarını public issue içine secret veya kişisel veri koymadan proje sahibine özel kanaldan bildirin. Token, chat ID, `.env`, SQLite veritabanı, cookie, Authorization header ve redakte edilmemiş log paylaşmayın. Telegram tokenı açığa çıktıysa BotFather üzerinden hemen yenileyin.
