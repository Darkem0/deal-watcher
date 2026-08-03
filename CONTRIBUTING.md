# Katkı rehberi

- Python 3.12 ve uv kullanın.
- Canlı sitelere bağlı kırılgan test eklemeyin; parser testlerinde redakte veya
  sentetik fixture kullanın.
- Secret, .env, SQLite, log ve cache dosyalarını commit etmeyin.
- CAPTCHA, proxy veya erişim kontrolü aşma kodu eklemeyin.
- Değişikliklerden sonra şu kontrolleri çalıştırın:

uv sync --locked --extra dev
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
git diff --check
