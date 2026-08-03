# Fixture sözleşmesi

Unit testler canlı sitelere istek göndermez. `tests/fixtures/` altında iki tür offline veri bulunur:

- Donanım Arşivi liste ve konu detayları: sentetik veya kişisel/dinamik alanlardan arındırılmış XenForo şekli.
- Akakçe deneysel parserı: ürün teklif kartları ve RTX 5070 Ti kategori kartları. Her ürün config ID’siyle eşleşen `akakce/<id>.html` dosyası kullanılır; canlı siteye istek atılmaz.

Akakçe ürün fixture’ı `h1` ürün adı ve en az bir `.offer`/fiyat alanı içerir. Satıcı, kargo, stok ve taksit alanları varsa ayrı teklif olarak saklanır. Kargo bilinmiyorsa `shipping_price=null` kalır; ücretsiz kargo `0` değeridir.

Kategori fixture’ı `.p-c` veya eşdeğer ürün kartları içerir. Parser yalnız gerçek `RTX 5070 Ti` kartlarını kabul eder; RTX 5070, laptop, hazır sistem ve aksesuarları reddeder.

Fixture seçicileri kritik yapıyı bulamazsa parser sessizce boş sonuç dönmez, kontrollü `ParserChangedError` üretir. Canlı HTML depoya eklenmeden önce kişisel, cookie, token ve dinamik kullanıcı alanları çıkarılmalıdır.
