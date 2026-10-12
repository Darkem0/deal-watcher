# Deal Watcher ajan talimatları

Her işe başlamadan önce `docs/development/plan.md`, `docs/development/status.md`, `docs/development/decisions.md` ve ilgili dokümanları okuyun.

- Verilen gerçek URL'leri sebepsiz değiştirmeyin; mevcut dosyaları izinsiz silmeyin.
- Büyük değişiklikten önce mimariyi inceleyin. Kod modüler, type-hint'li ve Windows uyumlu olmalıdır.
- Her implementasyon fazından sonra ilgili testleri çalıştırın; başarısız testleri ve eksikleri gizlemeyin.
- `docs/development/status.md` gerçek durumu, `docs/development/decisions.md` yeni kararları yansıtmalıdır.
- Secret'ları hard-code etmeyin veya Git'e koymayın; `.env`/güvenli depo kullanın.
- Canlı siteye bağlı kırılgan test yazmayın; parser testlerinde kaydedilmiş/sentetik HTML fixture kullanın.
- CAPTCHA veya erişim kontrolünü aşmayın; otomatik satın alma, sepet veya ödeme eklemeyin.
- Bildirim tekrarlarını ve ilk başarılı taramanın baseline davranışını engellemeyin.
- Belirsizlikte güvenli ve geri alınabilir yaklaşımı seçin.
