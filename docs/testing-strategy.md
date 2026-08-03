# Test stratejisi

pytest testlerinin tamamı offline ve işletim sisteminden bağımsızdır. Parser testleri `tests/fixtures/` altındaki sentetik veya redakte edilmiş UTF-8 HTML'i kullanır; canlı siteye istek atmaz. `forum_real_shape.html`, 2026-08-03 tarihinde gözlenen XenForo liste DOM şeklinin dinamik/kişisel alanlardan arındırılmış küçük örneğidir; tam canlı fixture değildir. Türkçe başlıklar, UTC→Europe/Istanbul dönüşümü, IANA `tzdata`, SQLite migration/idempotency/foreign key, baseline, kalıcı olay/teslim tekilleştirmesi ve host instance lock test edilir.

Akakçe ürün fixture’ları çoklu satıcı, ücretsiz/ücretli kargo, stok durumu, Türkçe fiyat biçimleri ve kritik selector failure senaryolarını kapsar. Kategori fixture’ı RTX 5070 Ti exact filtreleri, RTX 5070/laptop/aksesuar reddini ve model normalizasyonunu kapsar. Fiyat servisi baseline, yüzde 3/5/10 eşikleri, stok dönüşü ve dedup davranışını test eder. HTTP client MockTransport ile retry, User-Agent, 403 ve yanlış content-type kontrol edilir.

Türkçe fiyat ayrıştırıcı açık TL/TRY/₺ tutarlarını kabul eder; 16 GB, 2 TB, 850W ve 180 Hz gibi donanım değerlerini fiyat saymaz. Gelecekte OS entegrasyon testleri `@pytest.mark.platform` ile ayrılmalı ve varsayılan unit paketinden bağımsız çalıştırılmalıdır. Canlı kaynak regresyonu yerine gözden geçirilmiş/kaynak sürümü kayıtlı fixture kullanılmalıdır.

`pyproject.toml` pytest-cov terminal raporunu varsayılan olarak açar. Coverage eşiği yapay biçimde zorlanmaz; yeni parser ve servis modüllerinin kritik yolları fixture testleriyle ölçülür.
