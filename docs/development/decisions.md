# Mimari kararlar

## D16 — Kontrollü HTTP ve source failure

Tüm canlı kaynaklar `ControlledHttpClient` üzerinden çalışır. Retry yalnız geçici status kodları içindir; 401/403, CAPTCHA/challenge ve yanlış içerik türü kontrollü source failure olarak kaydedilir. Cookie, Authorization ve secret değerleri loglanmaz.

## D17 — Akakçe tekliflerinde bilinmeyen kargo korunur

Ücretsiz kargo `0`, ücretli kargo ayrıştırılmış tutar, bilinmeyen kargo `null` olarak saklanır. Bilinmeyen kargo sessizce ücretsiz varsayılmaz.

## D18 — Üretim hazırlığı kullanıcı onayından ayrıdır

`once --dry-run`, fixture doğrulaması ve backup güvenli otomasyon kapsamındadır. Gerçek Telegram gönderimi, gerçek Task Scheduler kurulumu ve canlı kaynak doğrulaması kullanıcı action/deployment kapısıdır.

## D19 — Akakçe deneysel ve varsayılan kapalı

Akakçe parserları, migrationları ve offline fixture testleri korunur; ancak `akakce.enabled: false` ve `status: experimental` varsayılandır. Kapalıyken scheduler job oluşturmaz, canlı erişim denemez ve source failure bildirimi üretmez. CLI açıkça etkinleştirilmemiş `--source akakce` çağrısında anlaşılır `source disabled` sonucu verir.

## D20 — Canlı Akakçe scraping kapsam dışı

Normal HTTP doğrulamasındaki 403 nedeniyle Akakçe canlı scraping üretim kapsamından çıkarılmıştır. Proxy, CAPTCHA çözme, cloudscraper, stealth, fingerprint değiştirme ve erişim kontrolü aşma kullanılmaz. Kullanıcı fiyat alarmı için Akakçe’nin resmi “Fiyatı Takip Edin” özelliğini kullanır. Playwright yalnız deneysel extra içinde tutulabilir; üretim bağımlılığı değildir.

## D21 — Process-local lifecycle bildirimleri

Her `deal-watcher run` süreci, mevcut outbox/dispatcher/delivery zinciriyle bir kez `runtime_started` ve ilk başarılı Forum taramasından sonra bir kez `first_successful_scan` üretir. State yalnız process instance alanlarında tutulur; günlük, saatlik veya kalıcı heartbeat state'i eklenmez. Notification/delivery hatası Forum source run'ını başarısız saymaz.

## D1 — Yerel katmanlı Python
Python 3.12 ve `src/` yerleşimi kullanılacak; kaynak, servis, depolama ve bildirim katmanları ayrıdır.

## D2 — SQLite sistem kaynağıdır
Gözlemler, baseline, olaylar ve bildirim teslimleri SQLite'ta; kullanıcı ayarları YAML'da tutulur.

## D3 — Saygılı erişim
Forum kaynağı için kontrollü HTTP kullanılır. Akakçe canlı scraping üretim akışına bağlı değildir; offline parser regresyonları fixture’larla sürdürülür.

## D4 — Baseline ve tekilleştirme
İlk başarılı tarama bildirim üretmez. Kalıcı olay anahtarı ve teslim kaydı tekrarları engeller.

## D5 — Offline parser testleri
Canlı sayfalar test edilmez; fixture'lar kaydedilmiş veya sentetik HTML'dir.

## D6 — Şüpheli fiyatlar silinmez
Anomali olarak işaretlenip saklanır. Hedef fiyat null ise ilk başarılı fiyat başlangıçtır.

## D7 — Yapılandırma semantik olarak doğrulanır
YAML yüklemek başarı sayılmaz. Ürün ID, URL, source type, pozitif aralık, sıralı eşik, category policy ve forum kategori/öncelik kapsamı Pydantic ile doğrulanır. İskeletteki tanımsız `cevre_birimi` önceliği, takip kapsamını koruyarak mevcut ayrıntılı çevre birimi kategorilerine açıldı; önceliksiz `hava_sogutma` da normal gruba alındı.

## D8 — Domain, parser ve SQLite satırı ayrıdır
Domain modelleri dataclass/enum sözleşmeleridir; kaynak seçicileri yalnız source adapter'ında, SQL yalnız storage/repository katmanındadır. Böylece HTML veya şema drift'i servis kararlarına yayılmaz.

## D9 — İki aşamalı kalıcı tekilleştirme
Mantıksal olay `notification_events.event_key`, kanal teslimi `(event_id, channel)` unique anahtarıyla korunur. Başarısız teslim yeniden denenebilir; yalnız `delivered` durumu tekrar gönderimi engeller. Olaylar notifier çağrısından önce ayrı transaction'da commit edilir.

## D10 — Kaynak durumu ve zaman standardı
SQLite kalıcı kaynak durumudur; foreign key her bağlantıda açılır. Veritabanı zamanları UTC ISO-8601, kullanıcı gösterimi IANA `Europe/Istanbul` saat dilimidir. Windows'ta zoneinfo tutarlılığı için `tzdata` açık bağımlılıktır.

## D11 — Windows geliştirme, platform-bağımsız çekirdek
Çekirdek `pathlib.Path`, SQLite, YAML ve ortak notifier protokolü kullanır; sabit Windows yolu içermez. OS ayrımları Windows/macOS notifier ve deployment adapter'larında tutulur. Kullanıcı kapsamındaki `uv` Python 3.12 tercih edilir.

## D12 — Tek aktif host ilkesi
Platform-bağımsız advisory instance lock aynı hostta ikinci örneği engeller. Farklı hostların ayrı SQLite dosyaları kalıcı dedup durumunu paylaşmaz; Windows ve Mac'i eşzamanlı çalıştırmamak operasyon sözleşmesidir. Scheduler hazır olmadan Task Scheduler/launchd kurulum scriptleri bilerek kurulum yapmaz.

## D13 — Konu detayları JSON olarak ek migration ile saklanır
Forum liste satırı ile konu detayının yaşam döngüsü ayrıdır. Detay parserı `ForumTopicDetail` üretir; repository bu alanı `forum_topics.detail_json` içinde migration 2 ile saklar. Böylece migration 1 satır sözleşmesi bozulmaz ve HTML seçicileri servis katmanına sızmaz.

## D14 — Kategori kararında negatif kurallar önceliklidir
Başlık, prefix ve ilk mesaj birlikte sınıflandırılır; hazır sistem, aksesuar/kablo/kutu ve kayış gibi bağlamlar tekil ürün kategorisini bastırır. Birincil kategori yanında ikincil kategoriler saklanır; hedef ürün veya güçlü stok/kupon sinyali en yüksek ilgili önceliği yükseltir.

## D15 — Gerçek DOM şekli fixture'ı kişisel/dinamik veri içermez
Donanım Arşivi'ne 2026-08-03 tarihinde kontrollü tek istekle erişim sağlandı. Dinamik CSRF, avatar, cookie ve kullanıcı üretimli tam sayfa saklanmadı; yalnız redakte edilmiş XenForo liste DOM şekli fixture'a dönüştürüldü. Bu fixture gerçek-şekil kontrolüdür, tam canlı doğrulama iddiası değildir.

## D23 — Portable sharing without personal runtime state (2026-10-12)

Public main remains the release baseline; Mac production code matches it after newline normalization. Personal .env, SQLite, logs, venv and root LaunchDaemon deployment are excluded. Setup creates .env exclusively and does not overwrite existing credentials. Linux/macOS autostart uses user services and the real CLI runtime; Windows retains pythonw. CI adds macOS but does not imply a live service/Telegram test. Jitter is sourced from validated YAML instead of a duplicated literal. No source adapters are removed or expanded.

## D24 — Beginner launchers and guided setup (2026-10-12)

OS-specific start files share the existing runtime. uv installation is an explicit first-run prompt, never an administrative installation. Guided Telegram setup reads getUpdates after the user's /start step, completes missing local credentials and preserves existing settings. Download ZIPs contain the full project and one appropriate root entrypoint; a GitHub preview link cannot execute an app. User docs distinguish approximate owner CPU observations from measured offline Linux metrics. Root paperwork is moved, not discarded. CI smoke mode only validates configuration and makes no website or Telegram calls.
