# Vibe Coding ile Deal Watcher Geliştirme

Vibe coding, insanın amacı, sınırları ve kabul ölçütlerini tarif ettiği; AI coding agent’ın inceleme, uygulama, test ve dokümantasyon işlerinde yardımcı olduğu bir geliştirme yaklaşımıdır. Mühendislik sorumluluğunun yerini almaz.

## Roller ve akış

Kapsam, izinler, secret’lar, hukuki sınırlar, canlı işlemler, inceleme ve release kararı insandadır. Agent; depoyu inceleyebilir, plan çıkarabilir, sınırlı değişiklik uygulayabilir, yerel kontrolleri çalıştırabilir ve kanıt sunabilir. Güvenli akış:

```text
plan → implementation → audit → live verification → release
```

Bu projede ilk implementation, bağımsız audit, scheduler/dispatcher hatalarının düzeltilmesi, yetkili Telegram doğrulaması, Windows Task Scheduler self-elevation/limited-user çözümü, runtime başlangıç ve ilk başarılı tarama bildirimleri, baseline/dedup testleri, Git secret kontrolü ve public release hazırlığı bu sıralı akışta ele alındı.

## Neden kısa prompt yetmez?

“Uygulamayı yap” ifadesi kaynak izinlerini, hata davranışını, veri saklamayı, secret sınırlarını, test koşullarını ve deployment politikasını belirtmez. İyi prompt; bağlamı, izin verilen/ yasak eylemleri, kabul ölçütlerini, deterministik testleri, canlı doğrulama limitini ve Git kurallarını açıklar.

## İnsan ve agent sorumluluğu

İnsan gerçek çıktıları, alıcıyı, dosya kapsamını ve release sayfasını kontrol etmelidir. AI tarafından üretilen kodun sahipliği ve işletim sorumluluğu projeyi yayımlayan kişidedir; “AI tamamen kendi başına yaptı” iddiası doğru bir süreç açıklaması değildir.

## Secret ve canlı erişim

`.env` veya güvenli depo kullanın; token, chat ID, cookie, authorization header ve kişisel verileri prompt, log, fixture, commit veya rapora koymayın. Telegram gönderimi, Task Scheduler kurulumu, dış yayın ve canlı kaynak erişimi açık izin kapılarıdır. CAPTCHA, proxy rotation, stealth, fingerprint spoofing veya erişim kontrolü bypass edilmez.

## Kabul ölçütü ve audit

Event tipi, tam mesaj, sayılar, exit code, task principal ve delivery durumu gibi gözlenebilir sonuçlar yazın. Parser’lar fixture ile test edilmeli; canlı test CI’a bağlanmamalıdır. Public release öncesinde bağımsız audit, diff/history/package/secret taraması ve insan incelemesi yapılmalıdır.

Kopyalanabilir prompt şablonları için [prompt-library.tr.md](prompt-library.tr.md) dosyasına bakın.
