# Uygulama planı

Her fazdan önce kararları doğrula; tamamlanınca `STATUS.md` ve `DECISIONS.md` güncellenir.

2026-08-03 uygulama notu: Donanım Arşivi forum takibi aktif üretim kapsamındadır. Akakçe parserları, migrationları ve offline fixture testleri korunmuş; canlı Akakçe bileşeni 403 nedeniyle deneysel ve varsayılan kapalı bırakılmıştır. Gerçek secret ve Task Scheduler kurulumu kullanıcı onayına bırakıldı.

Forum entegrasyonu ve Telegram test bildirimi doğrulandı. Runtime başlangıcı ve process başına ilk başarılı Forum taraması durum bildirimleri eklendi; heartbeat kapsam dışıdır. Sonraki geliştirme odağı Windows Task Scheduler ve public GitHub yayınıdır. Akakçe canlı doğrulaması kapsam dışıdır; fiyat takibi için resmi “Fiyatı Takip Edin” özelliği kullanılmalıdır.

| Faz | Amaç | Dosyalar | Kabul kriteri | Test | Risk | Bağımlılık | Geri alma |
|---|---|---|---|---|---|---|---|
| 1 | Temel ayarlar ve modeller | models/, config/ | YAML/env doğrulanır | config/model | şema drift'i | yok | şema sürümü |
| 2 | SQLite ve migration | storage/, migrations | idempotent boş DB | geçici SQLite | veri kaybı | 1 | yedek/ters migration |
| 3 | Bildirim ve dedup | notifiers/, services/ | tek teslim | mock adapter | tekrar/secret | 1-2 | kanalı kapat |
| 4 | Forum liste parserı | sources/forum.py, fixtures | tüm liste alanları | fixture parser | HTML drift | 1-2 | source kapat |
| 5 | Forum zenginleştirme | sources/forum_topic.py | fiyat/kupon/stok çıkarımı | çoklu fiyat fixture | yanlış çıkarım | 4 | tamamlandı; live fixture yok |
| 6 | Kategori/öncelik | services/classification.py | tüm kurallar | birim test | yanlış aciliyet | 4-5 | tamamlandı; düşük varsayılan |
| 7 | Akakçe ürün parserı | sources/akakce_product.py | teklif alanları | fixture parser | anti-bot/drift | 1-2 | deneysel; canlı dışı |
| 8 | RTX 5070 Ti parserı | sources/akakce_category.py | >=20 model, kesin filtre | karışık fixture | yanlış birleşme | 7 | deneysel; canlı dışı |
| 9 | Geçmiş/anomali | services/pricing.py | 3/5/10 ve 1/7/30 gün | zaman kontrollü | eksik tarih | 2,7-8 | alarmı kapat |
| 10 | Scheduler/Windows | scheduler.py, scripts/ | jitter/backoff/dry-run | sahte saat/ağ | aşırı sorgu | 3-9 | görev kapat |
| 11 | Test/fixture paketi | tests/ | offline regresyon | pytest | bayat fixture | 1-10 | sürümle |
| 12 | Dry-run | CLI, docs | DB/event/log, teslim yok | kontrollü çalışma | canlı istek | 1-11 | dry-run |
| 13 | Telegram testi | notifier ayarları | tek test mesajı | onaylı canlı test | yanlış alıcı | 12 | token/kanal kapat |
| 14 | Sürekli operasyon | scheduler, scripts | restart/backoff/log/backup | dayanıklılık | engel/kaynak | 13 | görev kapat |
