# Deal Watcher — İndirim ve Fırsat Takip Sistemi

Deal Watcher, herkese açık forum fırsatlarını yerel olarak izleyen ve uygun olayları Telegram’a bildiren hafif bir Python aracıdır.

İngilizce ana belge: [README.md](README.md)

## Ne işe yarar?

Aktif üretim kaynağı Donanım Arşivi Sıcak Fırsatlar forumudur. Araç forum listesini kontrollü HTTP ile tarar, konuları kategorilere ayırır, SQLite üzerinde baseline ve tekilleştirme durumunu saklar ve yeni/uygun fırsatları Telegram’a gönderir. Otomatik satın alma, sepet, ödeme, stok rezervasyonu veya CAPTCHA/erişim kontrolü aşma yoktur.

## Forum takibi nasıl çalışır?

Varsayılan forum URL’si `https://forum.donanimarsivi.com/forumlar/Sicakfirsatlar/` adresidir. İlk sayfa yaklaşık üç dakikada bir, 10–45 saniye jitter ile taranır. HTTP istemcisi timeout, sınırlı retry, backoff, rate-limit ve response kontrolü uygular.

İlk başarılı taramada mevcut konular baseline olarak kaydedilir. Böylece eski 15 konu topluca Telegram’a gönderilmez. Sonraki taramalarda kalıcı konu kimlikleri ve event/delivery kayıtları kullanılır; yalnız yeni veya uygun durum değişiklikleri bildirilir.

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

Acil sinyaller: `fiyat_hatasi`, `son_stok`, `bir_veya_iki_stok`, `sinirli_stok`, `tekrar_stokta`, `guclu_kupon`, `sepette_indirim`, `olagan_disi_dusuk_fiyat`. Negatif kurallar, ekran kartı standı veya SSD kutusu gibi aksesuarların ana ürün sanılmasını önler.

## Telegram bildirimleri

Mevcut dispatcher/outbox/delivery akışı kullanılır. Yeni bir `deal-watcher run` süreci bir kez `runtime_started`, ilk başarılı Forum taramasından sonra bir kez `first_successful_scan` üretir. Günlük, saatlik veya her taramada heartbeat yoktur. Telegram hataları kaynak taramasını durdurmaz.

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

## Windows’ta otomatik başlatma

`install_windows_task.ps1`, önce mevcut kullanıcı için `Interactive` ve `Limited` yetkili bir görev oluşturur. Varsayılan tetikleyici `AtLogOn`’dır; bu seçim kullanıcı oturumu açıldığında çalışmayı ve gereksiz SYSTEM yetkisi istememeyi sağlar. Windows erişim politikası kayıt işlemini reddederse script tek kontrollü UAC self-elevation denemesi yapar.

Örnek:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\scripts\install_windows_task.ps1" -ProjectRoot "C:\Projects\deal-watcher"
Get-ScheduledTask -TaskName DealWatcher
Get-ScheduledTaskInfo -TaskName DealWatcher
```

`LastTaskResult=267009` veya `0x41301`, görevin hâlen çalıştığı anlamına gelir; hata değildir. Ayrıntılar için [Türkçe Windows kurulum rehberine](docs/windows-deployment.tr.md) bakın.

## Akakçe neden kapalı?

Kontrollü doğrulamada doğrudan otomatik HTTP erişimi HTTP 403 döndürdü. Akakçe parserları ve offline fixture’lar korunur ancak `akakce.enabled: false` ve `status: experimental` varsayılandır. CAPTCHA çözme, proxy rotation, stealth browser, fingerprint spoofing veya erişim kontrolü aşma denenmez. Fiyat alarmı için Akakçe’nin resmi “Fiyatı Takip Edin” özelliği önerilir.

## Kurulum ve test

```powershell
git clone https://github.com/Darkem0/deal-watcher.git
cd deal-watcher
uv sync --locked
Copy-Item .env.example .env
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Testler offline ve deterministic’tir; canlı forum, Telegram ve Task Scheduler testi CI’da çalışmaz. Kaldırma için `scripts/uninstall_windows_task.ps1 -TaskName DealWatcher` kullanılır. SQLite, log, `.env` ve token Git’e gönderilmez.

## Sorumlu kullanım

Yalnız izin verilen ve normal HTTP erişimine açık kaynakları, makul sıklıkta ve hizmet şartları/robots politikaları ile yerel hukuka uygun biçimde kullanın. Ayrıntılar: [kaynak erişim politikası](docs/source-access-policy.tr.md).
