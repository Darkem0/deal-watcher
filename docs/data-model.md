# Veri modeli

Migration 1 şu tabloları kurar: `sources`, `product_targets`, `forum_topics`, `product_listings`, `price_observations`, `stock_observations`, `source_fetch_runs`, `baseline_states`, `notification_events`, `notification_deliveries`, `parser_errors`, `schema_migrations`.

`forum_topics` kaynak+topic ID ve kaynak+canonical URL için unique sözleşmesine sahiptir; başlık/cevap/görüntülenme güncellemeleri aynı satırda kalır. `notification_events.event_key` aynı mantıksal olayın yeniden üretilmesini, `notification_deliveries(event_id, channel)` aynı kanal tesliminin tekrarını kalıcı olarak engeller. İlk başarılı tarama `baseline_states` satırını kurar. Foreign key her SQLite bağlantısında etkinleştirilir.

Para değerleri kuruş cinsinden tamsayı, zamanlar UTC ISO-8601 metni olarak saklanır. Domain modelleri SQLite satır biçimine bağlı değildir. Şema Akakçe deneysel parser/service akışının offline sonuçlarını da saklayabilir; bu, canlı üretim erişimi anlamına gelmez.
