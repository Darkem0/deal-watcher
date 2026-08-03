# Operasyon

## Ortam ve doğrulama

Windows PowerShell:

```powershell
uv venv --python 3.12 .venv
uv sync --extra dev
.\.venv\Scripts\python.exe -m deal_watcher.cli validate-config
.\.venv\Scripts\python.exe -m pytest -q
uv run deal-watcher once --source all --dry-run
uv run deal-watcher backup-db --destination data\backup.sqlite3
```

Apple Silicon macOS (ileride Mac mini üzerinde):

```sh
uv venv --python 3.12 .venv
uv sync --extra dev
.venv/bin/python -m deal_watcher.cli validate-config
.venv/bin/python -m pytest -q
```

Veritabanı, log ve lock yolları `config/settings.yaml`; yapılandırma dizini CLI `--config-dir` ile belirlenir. Hepsi `pathlib.Path` olarak işlenir. Secret'lar yalnız `.env` veya güvenli depodadır. Loglar `logs/deal-watcher.log` altında RotatingFileHandler ile sınırlanır.

## Akakçe deneysel araçları

Windows:

```powershell
uv sync --extra experimental
.\.venv\Scripts\python.exe -m playwright install chromium
```

Apple Silicon macOS:

```sh
uv sync --extra experimental
.venv/bin/python -m playwright install chromium
```

Playwright varsayılan kuruluma dahil değildir ve Akakçe canlı scraping’i üretim kapsamına almaz. CAPTCHA, proxy veya erişim kontrolü aşılmaz. Akakçe için resmi “Fiyatı Takip Edin” özelliği önerilir.

## Operasyon sınırları

Donanım Arşivi forum ilk sayfa yaklaşık 3 ve ikinci sayfa 15 dakika jitter hedefleriyle çalışır. Akakçe varsayılan olarak kapalıdır; kapalıyken job ve source failure oluşturmaz. HTTP katmanı timeout, sınırlı retry, exponential backoff, `Retry-After`, minimum istek aralığı ve response boyutu kontrolü uygular. 401/403, CAPTCHA/challenge ve rate-limit aşılmaz. Aynı anda Windows ve Mac üzerinde ayrı veritabanlarıyla çalıştırmak çift bildirim üretebilir; kalıcı operasyonda tek aktif host kullanılmalıdır.
