# RUNTIME STARTUP AND FIRST SCAN NOTIFICATION REPORT

## Kapsam

Yalnızca process başlangıcı ve process başına ilk başarılı Donanım Arşivi Forum taraması durum bildirimleri eklendi. Akakçe kapalı kalır; günlük, saatlik, periyodik veya zaman aralığına bağlı heartbeat eklenmedi.

## Uygulama

- `notifications.send_runtime_started: true` ve `notifications.send_first_successful_scan: true` varsayılanları eklendi.
- `RuntimeNotificationState` içinde `runtime_started_sent` ve `first_successful_scan_sent` process-local tutuluyor.
- Scheduler lock alındıktan sonra `runtime_started` event'i gönderiliyor.
- İlk başarılı Forum taramasının gerçek `topics_fetched`, `new_topics` ve `Europe/Istanbul` yerel zamanı ile `first_successful_scan` gönderiliyor.
- Event'ler mevcut repository, outbox ve dispatcher/delivery akışını kullanıyor; doğrudan Telegram Bot API çağrısı eklenmedi.
- Lifecycle ve Forum notification hataları source runtime'ını durdurmuyor; hata metinleri redacted logging'den geçiyor.

## Offline testler ve kalite

- `uv run pytest`: 55 passed
- `uv run ruff check .`: başarılı
- `uv run ruff format --check .`: başarılı
- `git diff --check`: başarılı
- Startup tekrarları, first-success tekrarları, ilk tarama failure→success, config kapatma, notification failure isolation ve heartbeat yokluğu test edildi.

## Canlı Windows Task Scheduler doğrulaması

- `DealWatcher` durdurulup güncel süreç yeniden başlatıldı.
- Aynı process kimliği için tam olarak bir `runtime_started` ve bir `first_successful_scan` event'i oluştu.
- Her iki Telegram delivery durumu `delivered` oldu.
- İlk taramadan sonra iki ek Forum turu görüldü; lifecycle event sayısı değişmedi.
- Son temiz canlı doğrulama sürecinde gerçek yeni fırsat oluşmadığı için lifecycle dışı Telegram mesajı oluşmadı.
- Görev durumu `Running`; `LastTaskResult=267009` çalışan görev durumudur.

## Not

İlk hedefli test çalıştırmasında mevcut `.env` database override'ı test izolasyonunda tespit edildi; bu nedenle ilk hatalı test koşusu canlı Telegram'a lifecycle denemeleri üretti. Testler explicit geçici database ve environment izolasyonuyla düzeltildi; sonraki temiz doğrulamada ek lifecycle tekrarı oluşmadı. Bu turda oluşturulan test lifecycle kayıtları temizlendi; gerçek görev process'ine ait son doğrulama çifti korundu. Secret veya chat ID rapora yazılmadı.

## Verdict

`STARTUP_AND_FIRST_SCAN_NOTIFICATIONS_READY`
