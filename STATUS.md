# Durum

**Aşama:** Donanım Arşivi forum takipçisi üretime hazır; Akakçe canlı scraping üretim kapsamı dışındadır (2026-08-03).

## Akakçe kapsam kararı

- Donanım Arşivi takibi aktif üretim özelliğidir.
- Akakçe parserı deneysel ve varsayılan olarak kapalıdır (`enabled: false`, `status: experimental`). Kod, migration ve offline fixture testleri silinmemiştir.
- Normal HTTP canlı doğrulamasında Akakçe HTTP 403 döndürdü; canlı erişim doğrulanamamıştır.
- CAPTCHA, proxy, cloudscraper, stealth, fingerprint değiştirme veya erişim kontrolü aşma uygulanmaz.
- Fiyat alarmı için Akakçe’nin resmi “Fiyatı Takip Edin” özelliği önerilir.
- Akakçe kapalıyken scheduler job oluşturmaz, erişim/source failure bildirimi üretmez; forum bağımsız çalışır.

## 2026-08-03 production blocker remediation

- Unknown shipping (`total_price=NULL`) ile ardışık Akakçe snapshot'ları artık karşılaştırılabilir fiyat havuzundan dışlanır; boş havuz `None` döndürür.
- Akakçe `PriceEvent` ve parser akışı yalnız deneysel/offline kapsamda korunur; varsayılan runtime bunları çalıştırmaz.
- Scheduler yalnız etkin kaynaklar için job oluşturur; forum bağımsız çalışır.
- `.env`/`--env-file` yüklemesi process environment'ı ezmeden eklendi; Windows UTF-8 çıktısı best-effort yapılandırılır.
- Telegram hata metinleri delivery kaydından önce redakte edilir; notifier timeout, sınırlı retry, 429 `Retry-After` ve 4096 karakter sınırını uygular.
- Gerçek Akakçe HTTP ön kontrolü 403 döndü; canlı erişim doğrulanamadı. Browser/proxy/CAPTCHA bypass yolu üretim kapsamından çıkarıldı.
- Donanım Arşivi sayfa 1 için tek normal HTTP smoke isteği HTTP 200 döndürdü; parser 15 konu ve parser hatası olmayan bir sonuç üretti. Ayrıntı doğrulama betiği yanlış alan adı nedeniyle yarıda kaldı; ikinci canlı istek yapılmadı.
- Telegram canlı test bildirimi bir kez gönderildi; chat ID maskeli gösterildi, Message ID 5 ve delivery=delivered sonucu alındı. Token çıktılanmadı.

## Tamamlanan

- Mevcut Forum parserı, baseline, dedup, SQLite ve eski testler korunarak çalışıyor.
- Kontrollü `httpx` istemcisi: timeout, retry, exponential backoff+jitter, `Retry-After`, minimum host aralığı, sabit User-Agent, response boyutu/içerik türü kontrolü ve kontrollü access/CAPTCHA failure.
- Akakçe tekil ürün parserı dört ürün config ID’siyle çalışıyor; çoklu teklif, Türkçe fiyat, kargo, stok ve taksit çıkarıyor.
- RTX 5070 Ti kategori parserı exact chipset ve negatif ürün filtreleriyle çalışıyor.
- Migration 3–4 ürün snapshot/state, fiyat event ve kategori state tablolarını ekliyor; migration idempotent.
- Fiyat geçmişi baseline, yüzde 3/5/10 eşikleri, dip fiyatları, stok dönüşü/çıkışı, hedef fiyat ve kategori yeni/en ucuz model event API’si sağlıyor.
- `once`, `run`, `test-notification` ve `backup-db` CLI komutları eklendi.
- Scheduler runtime, tek instance lock, jitter, başarısız iş backoff’u ve graceful shutdown kullanıyor.
- Rotating file/console logging ve secret redaction eklendi.
- Windows Task Scheduler scripti runtime/config preflight, `-Force`, logon/startup ve güvenli uninstall davranışıyla güncellendi.
- Akakçe ve HTTP fixture/test paketi eklendi.
- Windows Task Scheduler görevi kullanıcı idle durumundan çıkınca durmasın diye `StopOnIdleEnd=false` ve limitsiz execution time ile yeniden kaydedildi; Forum ilk sayfa polling aralığı 5 dakikaya çıkarıldı.

## Doğrulama

- `pytest`: 50 test başarılı.
- Ruff lint ve format: başarılı.
- Config validation: başarılı.
- Akakçe parser fixture testleri korunuyor; varsayılan config bu kaynağı çalıştırmıyor.
- Forum fixture once: offline akış işlendi.
- SQLite backup CLI: başarılı.
- Scheduler ve kaynak modülleri import testi: başarılı.

## Kullanıcıya bağlı

- Gerçek Telegram test mesajı gönderildi; normal forum bildirimleri için ayrıca kullanıcı onayı gerekir.
- Gerçek Windows Task Scheduler görevi oluşturulmadı.
- Canlı Akakçe doğrulaması 403 nedeniyle yapılamadı; Forum smoke sonucu HTTP 200 ve 15 konu olarak kaydedildi. Tüm canlı alan assertion'ları yanlış verifier alan adı nedeniyle tamamlanamadı.
- Gerçek `.env` secret değerleri ayarlanmadı.

## Kalan sınırlamalar

- Akakçe fixture’ları sentetik; DOM drift kontrollü parser failure olarak raporlanır. Canlı scraping üretim vaadi değildir.

## Sonraki odak

Donanım Arşivi forum entegrasyonu, Telegram bildirimi, Windows Task Scheduler ve public GitHub yayını.
- Runtime başlangıcı (`runtime_started`) ve process başına ilk başarılı Forum taraması (`first_successful_scan`) bildirimleri etkinleştirildi; günlük/saatlik heartbeat eklenmedi.
- Canlı Task Scheduler doğrulamasında aynı process için iki lifecycle Telegram delivery'si birer kez `delivered` oldu; iki ek Forum turunda tekrar oluşmadı.
- İkinci Forum sayfası pagination adaptörü henüz yoktur.
- Gelişmiş median anomaly ve cooldown politikası sonraki küçük iyileştirmedir.
