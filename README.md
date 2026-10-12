# Deal Watcher — Telegram fırsat takipçisi

[![CI](https://github.com/Darkem0/deal-watcher/actions/workflows/ci.yml/badge.svg)](https://github.com/Darkem0/deal-watcher/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](pyproject.toml)
[![MIT](https://img.shields.io/badge/Lisans-MIT-green)](LICENSE)

Donanım Arşivi Sıcak Fırsatlar forumunu kendi bilgisayarında takip eder; yeni ve uygun değişiklikleri Telegram'a gönderir. **Windows, Linux ve macOS için ortak kurulum**, yerel SQLite kayıtları ve kendi bot token'ın kullanılır. Mac, Qdrant, AIST veya bir yapay zekâ modeli gerekmez.

[English](README.en.md) · [Adım adım kurulum](KURULUM.md) · [Diğer projelerden farkı](docs/proje-farklari.tr.md)

## Hızlı başlangıç

Önce [uv](https://docs.astral.sh/uv/getting-started/installation/) ve Git kur. Üç sistemde de aynı komutları kullan:

```sh
git clone https://github.com/Darkem0/deal-watcher.git
cd deal-watcher
uv sync --locked
uv run deal-watcher-setup
```

Telegram'da **@BotFather** üzerinden kendi botunu oluştur ve botuna `/start` gönder. Kurulum yardımcısına token ve Chat ID gir; token ekranda görünmez, yalnız `.env` dosyasına kaydedilir. Chat ID'yi bilmiyorsan boş bırakıp şunu çalıştır:

```sh
uv run deal-watcher-setup --find-chat
```

Bulunan ID'yi `.env` içindeki `TELEGRAM_CHAT_ID=` satırına ekle. Ardından:

```sh
uv run deal-watcher-setup --check
uv run deal-watcher test-notification --send
uv run deal-watcher run
```

`--check` offline kontroldür. `--send` bir gerçek Telegram test mesajı gönderir. `run` sürekli takip eder; durdurmak için **Ctrl+C**. Terminal kapanırsa veya bilgisayar uyursa takip durur. İstersen [otomatik başlatmayı kur](KURULUM.md#otomatik-başlatma).

## Bildirim mantığı

- İlk başarılı tarama mevcut konuları kaydeder; eski fırsatları topluca göndermez.
- Sonraki taramalar yeni konular ve seçilmiş durum değişiklikleri için bildirim üretir.
- SQLite'taki olay ve teslim anahtarları aynı bildirimin tekrarını engeller; yeniden başlatınca kayıtlar korunur.
- Türkçe/ASCII yazımlar, ürün kategorileri ve acil stok/kupon sinyalleri değerlendirilir. Aksesuarların ana ürün sanılmasını azaltan negatif kurallar vardır.
- Başlangıç ve ilk başarılı tarama durum mesajı gelebilir; bunlar fırsat bildirimi değildir.

## Ayarlar ve sınırlar

| Dosya | Ne için? |
| --- | --- |
| `.env` | Sana ait Telegram token ve Chat ID |
| `config/forum.yaml` | Forum adresi, tarama aralığı, kategoriler, öncelikler |
| `config/settings.yaml` | Ağ, veritabanı, log ve bildirim ayarları |
| `config/products.yaml` | Deneysel Akakçe hedefleri; varsayılan kapalı |

Forumun **ilk sayfası** varsayılan olarak beş dakikada bir, ek 10–45 saniye gecikmeyle taranır. İkinci sayfa ayarı dosyada bulunsa da adaptör şu an ikinci sayfayı taramaz. `digest` yalnız öncelik etiketidir; toplu gönderim kuyruğu değildir. Akakçe normal erişimde 403 verdiği için varsayılan kapalıdır. CAPTCHA aşma ve otomatik satın alma yoktur.

Her arkadaşın kendi token'ını, Chat ID'sini ve veritabanını kullanmalı. Aynı botu bağımsız veritabanlarıyla iki bilgisayarda çalıştırmak çift bildirim üretebilir. Bilgisayar açık ve internete bağlı olmalı; GitHub deposu senin yerine botu çalıştırmaz. Bu sürüm **ön sürümdür**; forum HTML'i değişince parser güncellemesi gerekebilir.

## Geliştirme ve katkı

```sh
uv sync --locked --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Testler kayıtlı/sentetik HTML ile çalışır; CI'da canlı site veya Telegram'a mesaj gönderilmez. [Mimari](docs/architecture.md), [katkı](CONTRIBUTING.md), [güvenlik](SECURITY.md), [kaynak erişim politikası](docs/source-access-policy.tr.md) ve [referans projeler](ACKNOWLEDGEMENTS.md). [MIT lisansı](LICENSE).
