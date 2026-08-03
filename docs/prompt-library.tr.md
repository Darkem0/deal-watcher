# Prompt kütüphanesi

Bu şablonlar sınırları açık görevler içindir. Köşeli parantezli alanları doldurun; yasak eylemleri kaldırmayın. Ayrıntılı İngilizce şablonlar için [prompt-library.md](prompt-library.md) dosyasına bakın.

Her prompt şu iskeleti kullanmalıdır:

```text
Context: Mevcut depo, davranış ve ilgili dosyalar.
Goal: Tek ve ölçülebilir hedef.
Allowed actions: Dosya inceleme, sınırlı düzenleme, offline kontroller.
Forbidden actions: Secret, anti-bot bypass, satın alma, izinsiz dış mesaj.
Acceptance criteria: Gözlenebilir kabul ölçütleri.
Tests: Deterministik test komutları.
Live verification limits: Yok veya tam yetkili tek işlem.
Git rules: Yalnız kapsam dosyalarını stage et; açık izin yoksa push etme.
Expected report: Değişiklik, kanıt, başarısızlık, risk, verdict.
```

## Görev başlıkları

1. Initial project planning — fazlar, bağımlılıklar, riskler ve geri alma.
2. Architecture design — adapter, parser, domain, storage ve notification sınırları.
3. Source adapter implementation — kontrollü HTTP, rate limit ve disabled fallback.
4. HTML parser implementation — kaydedilmiş/sentetik fixture ve drift hatası.
5. Baseline and deduplication — ilk tarama sessizliği ve event/channel tekilleştirme.
6. Telegram integration — dispatcher kullanımı, redaction ve dry-run.
7. Windows Task Scheduler setup — Interactive/Limited, AtLogOn, UAC ve 267009.
8. Security audit — secret, path, artifact ve erişim politikası taraması.
9. Independent production audit — iddiaları kod/config/kanıtla karşılaştırma.
10. Bug-fix prompt — en küçük düzeltme ve regression testi.
11. Test coverage improvement — failure/retry/disabled/baseline senaryoları.
12. Documentation generation — kodla doğrulanmış, nötr path kullanan doküman.
13. GitHub release preparation — README, CI, template, changelog ve audit.
14. Adding a new public source — normal erişim, izin, bakım ve rate-limit go/no-go.
15. Disabling a source that returns 403/CAPTCHA — bypass yapmadan config/scheduler kapatma.
16. Secret leakage inspection — working tree ve Git geçmişi taraması.
17. Regression test prompt — eski hatayı yakalayan deterministik test.
18. Live verification prompt — açıkça sınırlandırılmış tek canlı işlem ve kanıt.

Her görevde insan; kapsamı, credential’ı, canlı eylemi ve release kararını kontrol eder. AI agent’ın yanlış varsayımlarını azaltmak için önce gerçek dosyaları okutun, bilinmeyenleri etiketletin ve acceptance criteria yazın.
