# Kaynak erişim politikası

Deal Watcher, herkese açık ve normal otomatik HTTP erişimine izin veren kaynaklar için tasarlanmıştır. Bazı fiyat karşılaştırma ve e-ticaret siteleri otomatik istemcilere HTTP 403, CAPTCHA veya anti-bot sayfası döndürebilir.

Proje CAPTCHA çözmeye çalışmaz. CAPTCHA bypass, stealth browser, proxy rotation, fingerprint spoofing, cookie toplama ve erişim kontrolünü zayıflatma kapsam dışıdır. Bir kaynak normal erişime izin vermiyorsa adapter disabled veya experimental kalır.

Akakçe’ye doğrudan otomatik HTTP erişimi kontrollü doğrulamada HTTP 403 döndürdü. Bu nedenle Akakçe production config’de kapalıdır. Offline parser fixture’ları araştırma ve regression testi için korunabilir. Açık API, feed veya açık izin bulunduğunda yeni entegrasyon değerlendirilebilir.

Kaynakların hizmet şartlarına, robots politikalarına, rate limit’lerine ve yerel hukuka uyun. Conservative polling, jitter ve backoff kullanın. Erişimi zorlamak için istek sıklığını artırmayın veya güvenlik önlemlerini zayıflatmayın.
