# Geliştirici belgeleri

[← Kullanıcı ana sayfası](../../README.md)

- [Plan](plan.md)
- [Durum](status.md)
- [Mimari kararlar](decisions.md)
- [Değişiklik geçmişi](changelog.md)
- [Mimari](../architecture.md)
- [Katkı kuralları](../../.github/CONTRIBUTING.md)
- [Güvenlik](../../.github/SECURITY.md)

```sh
uv sync --locked --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build
```

Kurulum yardımcısı ağ/sır işlemlerini kullanıcı etkileşimine bağlar. CI fixture testlerini ve ZIP başlatıcısının `--check` modunu çalıştırır; canlı forumu taramaz veya Telegram'a mesaj göndermez. Paketleri üretmek için `uv run python scripts/build_release.py --output-dir dist/releases` kullan.
