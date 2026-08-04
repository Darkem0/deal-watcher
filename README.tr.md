# Deal Watcher — İndirim ve Fırsat Takip Sistemi

Deal Watcher, herkese açık forum fırsatlarını yerel olarak izleyen ve uygun olayları Telegram’a bildiren hafif bir Python aracıdır.

İngilizce ana belge: [README.md](README.md)

[![CI](https://github.com/Darkem0/deal-watcher/actions/workflows/ci.yml/badge.svg)](https://github.com/Darkem0/deal-watcher/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Lisans: MIT](https://img.shields.io/badge/lisans-MIT-green.svg)](LICENSE)

## Ne işe yarar?

Aktif üretim kaynağı Donanım Arşivi Sıcak Fırsatlar forumudur. Araç forum listesini kontrollü HTTP ile tarar, konuları kategorilere ayırır, SQLite üzerinde baseline ve tekilleştirme durumunu saklar ve yeni/uygun fırsatları Telegram’a gönderir. Otomatik satın alma, sepet, ödeme, stok rezervasyonu veya CAPTCHA/erişim kontrolü aşma yoktur.

## Forum takibi nasıl çalışır?

Varsayılan forum URL’si `https://forum.donanimarsivi.com/forumlar/Sicakfirsatlar/` adresidir. İlk sayfa yaklaşık beş dakikada bir, `config/forum.yaml` içinde tanımlanan 10–45 saniye jitter ile taranır. HTTP istemcisi timeout, sınırlı retry, backoff, rate-limit ve response kontrolü uygular.

İlk başarılı taramada o anda görülen mevcut konular baseline olarak kaydedilir. Konu sayısı forum sayfasının güncel içeriğine göre değişebilir; sabit bir “15 konu” limiti yoktur. Baseline konuları topluca Telegram’a gönderilmez. Sonraki taramalarda kalıcı konu kimlikleri ile event/delivery kayıtları kullanılır; yalnız yeni veya uygun durum değişiklikleri bildirilir.

## Kategoriler

| Öncelik | Kod | İnsan tarafından okunabilir karşılık |
| --- | --- | --- |
| Acil | `gpu` | Ekran kartı |
| Acil | `cpu` | İşlemci |
| Acil | `motherboard` | Anakart |
| Acil | `cpu_cooler` | İşlemci soğutucu ve termal ürünler |
| Normal | `cooling_and_fans` | Soğutma ve fan |
| Normal | `memory` | RAM ve bellek |
| Normal | `storage` | SSD, NVMe, HDD ve depolama |
| Normal | `power_supply` | Güç kaynağı |
| Normal | `pc_case` | Bilgisayar kasası |
| Normal | `monitor` | Monitör |
| Normal | `laptop` | Dizüstü bilgisayar |
| Normal | `complete_system` | Hazır/tam sistem |
| Normal | `peripherals` | Klavye, fare, webcam ve çevre birimleri |
| Normal | `networking` | Ağ ekipmanı |
| Normal | `phone_tablet_watch` | Telefon, tablet ve akıllı saat |
| Normal | `audio` | Kulaklık, mikrofon ve hoparlör |
| Normal | `supplement` | Takviye ürünleri |
| Normal | `bank_campaign` | Banka kampanyaları |
| Normal | `grocery` | Market ve ev ürünleri |
| Özet/diğer | `other` | Sınıflandırılamayan veya düşük öncelikli konu |

Acil sinyal kodları: `fiyat_hatasi`, `son_stok`, `bir_veya_iki_stok`, `sinirli_stok`, `tekrar_stokta`, `guclu_kupon`, `sepette_indirim`, `olagan_disi_dusuk_fiyat`. Sınıflandırıcı Türkçe karakterli ve ASCII yazım biçimlerini birlikte değerlendirir. Negatif kurallar, ekran kartı standı veya SSD kutusu gibi aksesuarların ana ürün sanılmasını önler.

`digest` şu anda bir öncelik etiketidir; ayrı bir gecikmeli toplu bildirim kuyruğu henüz yoktur. Uygun olaylar oluşturuldukları anda etkin kanallara gönderilir.

## Telegram bildirimleri

Mevcut dispatcher/delivery akışı kullanılır. Yeni bir `deal-watcher run` süreci bir kez `runtime_started`, ilk başarılı forum taramasından sonra bir kez `first_successful_scan` üretir. Günlük, saatlik veya her taramada heartbeat yoktur. Telegram hataları kaynak taramasını durdurmaz.

Forumun ilk sayfası yaklaşık beş dakikada bir, 10–45 saniye jitter ile taranır. Mevcut event ve delivery kayıtları korunduğu için aynı fırsat tekrar gönderilmez.

`.env.example` dosyasını `.env` olarak kopyalayın ve gerçek değerleri yalnız yerel dosyaya yazın:

```powershell
Copy-Item .env.example .env
uv run deal-watcher validate-config
uv run deal-watcher test-notification --dry-run
```

Gerçek bildirim yalnızca açıkça istenirse gönderilir:

```powershell
uv run deal-watcher test-notification --send
```

## İsteğe bağlı Windows bildirimleri

Varsayılan kanal Telegram’dır. Windows toast bildirimi kullanmak için opsiyonel bağımlılığı kurup `config/settings.yaml` içindeki `notifications.channels` listesine `windows_toast` ekleyin:

```powershell
uv sync --locked --extra notifications
```

## Windows’ta otomatik başlatma

`install_windows_task.ps1`, önce mevcut kullanıcı için `Interactive` ve `Limited` yetkili bir görev oluşturur. Varsayılan tetikleyici `AtLogOn`’dır; kullanıcı Windows oturumunu açtığında izleme süreci otomatik başlar. Windows erişim politikası kayıt işlemini reddederse script tek kontrollü UAC self-elevation denemesi yapar.

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\scripts\install_windows_task.ps1" -ProjectRoot "C:\Projects\deal-watcher"
Get-ScheduledTask -TaskName DealWatcher
Get-ScheduledTaskInfo -TaskName DealWatcher
```

`LastTaskResult=267009` veya `0x41301`, sürekli çalışan görevin hâlen açık olduğu anlamına gelir; hata değildir. Ayrıntılar için [Türkçe Windows kurulum rehberine](docs/windows-deployment.tr.md) bakın.

## Akakçe neden kapalı?

Kontrollü doğrulamada doğrudan otomatik HTTP erişimi HTTP 403 döndürdü. Akakçe parserları ve offline fixture’lar korunur ancak `akakce.enabled: false` ve `status: experimental` varsayılandır. CAPTCHA çözme, proxy rotation, stealth browser, fingerprint spoofing veya erişim kontrolü aşma denenmez. Fiyat alarmı için Akakçe’nin resmi “Fiyatı Takip Edin” özelliği önerilir.

## Kurulum ve test

```powershell
git clone https://github.com/Darkem0/deal-watcher.git
cd deal-watcher
uv sync --locked
Copy-Item .env.example .env
uv run deal-watcher validate-config
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Testler offline ve deterministiktir; canlı forum, Telegram ve Task Scheduler testi CI’da çalışmaz. Kaldırma için `scripts/uninstall_windows_task.ps1 -TaskName DealWatcher` kullanılır. SQLite, log, `.env` ve token Git’e gönderilmez.

## Vibe Coding ile geliştirme

Proje; insan yönlendirmesi, AI coding agent uygulaması, test, bağımsız denetim, sınırlı canlı doğrulama ve yayın adımlarıyla iteratif olarak geliştirildi. AI agent tek başına ürün sahibi veya karar verici değildir; kapsam, izin, credential, canlı işlemler ve yayın kararı insana aittir.

- [Vibe Coding ile Deal Watcher Geliştirme](docs/vibe-coding-guide.tr.md)
- [Türkçe prompt kütüphanesi](docs/prompt-library.tr.md)
- [İngilizce Vibe Coding rehberi](docs/vibe-coding-guide.md)
- [İngilizce prompt kütüphanesi](docs/prompt-library.md)

## Bilinen sınırlamalar

- Üretim forum adaptörü şu anda ilk liste sayfasına odaklanır.
- Forum HTML yapısı değişirse parser fixture’ları güncellenmelidir.
- `digest` ayrı bir toplu bildirim zamanlayıcısı değildir.
- Telegram ve Windows Task Scheduler yerel kullanıcı kurulumu gerektirir.
- Bu sürüm alpha’dır; kesintisiz çalışma garantisi verilmez.
- Akakçe canlı erişimi doğrulanmamıştır ve varsayılan üretim yolunda değildir.

## Sorumlu kullanım

Yalnız izin verilen ve normal HTTP erişimine açık kaynakları, makul sıklıkta ve hizmet şartları/robots politikaları ile yerel hukuka uygun biçimde kullanın. Ayrıntılar: [kaynak erişim politikası](docs/source-access-policy.tr.md).

## Katkı ve lisans

Katkı kuralları için [CONTRIBUTING.md](CONTRIBUTING.md), güvenlik bildirimi için [SECURITY.md](SECURITY.md), ilham alınan projeler için [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md) dosyalarına bakın. Proje [MIT Lisansı](LICENSE) ile yayımlanır.
