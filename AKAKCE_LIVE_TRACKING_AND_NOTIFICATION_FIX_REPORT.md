# Akakçe kapsamdan çıkarma raporu

Akakçe canlı scraping üretim kapsamından çıkarıldı. Parserlar, migrationlar ve offline fixture testleri korunuyor; varsayılan yapılandırmada kaynak `enabled: false`, `status: experimental`.

- Normal HTTP canlı doğrulaması HTTP 403 (`access_denied`) ile sonuçlandı.
- Proxy, CAPTCHA çözme, cloudscraper, stealth, fingerprint değiştirme ve erişim kontrolü aşma uygulanmaz.
- Akakçe kapalıyken scheduler job oluşturmaz, erişim hatası veya source failure bildirimi üretmez.
- `once --source akakce` açıkça etkinleştirilmemişse stack trace olmadan `source disabled` sonucu verir.
- Playwright varsayılan kurulumdan çıkarılmış, yalnız `experimental` extra içinde tutulmuştur.
- Kullanıcı fiyat alarmı için Akakçe’nin resmi “Fiyatı Takip Edin” özelliği önerilir.

Aktif üretim özelliği Donanım Arşivi forum takibidir. Sonraki geliştirme odağı forum entegrasyonu, Telegram bildirimi, Windows Task Scheduler ve public GitHub yayınıdır.

## Verdict

FORUM_TRACKER_READY_FOR_DEPLOYMENT
