# Deal Watcher'ın farkı ve senin değişikliklerin

## Kendi bilgisayarında çalışan takipçi

Deal Watcher, Donanım Arşivi forumundaki fırsat konularını okuyup Telegram'a bildiren bağımsız bir Python uygulamasıdır. BotFather'dan alınan token dışında bulut hesabı, Qdrant, AIST, macOS bağlantısı veya AI modeli istemez. Linux, Windows ve macOS çekirdeği aynı; yalnız otomatik başlatma sistemi farklıdır.

Bu sürüm Mac'te çalıştırılmış botun kaynak yedeğiyle GitHub `831a006` sürümü karşılaştırılarak hazırlandı. Satır sonları normalleştirildiğinde uygulama kaynakları aynı çıktı. Mac'e özel root LaunchDaemon ve kişisel çalışma durumu public pakete taşınmadı. GitHub'daki Windows `pythonw.exe` düzeltmesi korundu; eski Mac kopyasındaki konsollu Windows başlatıcıya geri dönülmedi. Kişisel token, Chat ID, SQLite, log ve Python ortamı yayımlanmıyor.

## Mevcut özelleştirmelerin ne sağlıyor?

- **Türkçe sınıflandırma:** Türkçe/ASCII biçimler, kategori öncelikleri ve stok/kupon sinyalleri. Ekran kartı standı, SSD kutusu gibi aksesuarların asıl ürün kategorisi sanılmasını azaltan negatif kurallar.
- **Sessiz başlangıç:** İlk başarılı tarama mevcut konuları kaydeder; eski fırsatları topluca göndermez.
- **Kalıcı kayıt:** SQLite'ta konu, kaynak çalışması, olay ve kanal teslimi tutulur. Yeniden başlatma eski kayıtları kaybettirmez; olay ve başarılı teslim için ayrı unique anahtarlar vardır.
- **Çalışma durumu:** Süreç başlarken ve ilk başarılı taramada birer durum bildirimi; her turda heartbeat yok. Bildirim hatası forum taramasını başarısız saydırmaz.
- **Zamanlama:** Beş dakikalık tarama, jitter ve kaynak hatalarında sınırlı geri çekilme. Aynı bilgisayarda ikinci süreç instance lock ile engellenir.
- **Windows sürekliliği:** Oturum açılınca başlayan görev, idle bitince durdurmama ve pencere açmayan `pythonw.exe` kullanımı.
- **Kaynak sınırı:** Akakçe parserları testlerde korunur; canlı kaynak varsayılan kapalıdır. Otomatik satın alma ve erişim kontrolünü aşma yoktur.

Bunlar çalışma sürümünün özellikleridir; hepsi bu yayın sırasında yeni yazılmış gibi sunulmaz. Yeni paylaşım sürümünün ekleri aşağıdadır.

## Bu yayında eklenen ve sadeleştirilenler

1. Windows, Linux ve macOS için aynı `uv sync` ve `deal-watcher-setup` akışı. Token gizli girişle yerel `.env` dosyasına kaydedilir; mevcut dosya ezilmez.
2. Chat ID için yalnız Telegram `getUpdates` okuyan komut; gerçek test mesajı ayrı `--send` adımıdır.
3. Linux systemd kullanıcı servisi ve macOS kullanıcı LaunchAgent'ı için ortak, küçük servis yönetim yardımcısı. Eski macOS şablonu çalıştırılabilir CLI yerine yalnız scheduler modülünü açıyordu; `-m deal_watcher.cli run` olarak düzeltildi. XML/path kodlaması ve log klasörü hazırlığı eklendi.
4. CLI'daki sabit jitter kaldırıldı; gerçek zamanlayıcı artık YAML'daki `(10, 45)` değerini kullanır. Böylece belge ve uygulama aynı aralığı izler.
5. Platform varsayılanı `auto`, Linux yapılandırma değeri ve macOS CI matrisi eklendi.
6. Giriş belgesi kısaltıldı; kurulum, ayrıntılı kategori referansı ve proje karşılaştırması ayrı okunabilir dosyalara alındı. Tekrarlanan changelog başlığı birleştirildi.

Kaynak/storage/notifier ayrımı korundu. Büyük CLI dosyasını baştan yazmak veya deneysel Akakçe parserlarını silmek bu yayına alınmadı; çalışan baseline/tekilleştirme akışına gereksiz risk eklememek için kapsam kurulum ve somut düzeltmelerle sınırlandı.

## Referans projelerle somut karşılaştırma

Aşağıdaki tablo 12 Ekim 2026 tarihinde erişilen kaynak kodlarına dayanır; diğer projelerin daha sonra değişmesi mümkündür. Daha iyi olduğu iddiası değil, kullanım ve mimari farkıdır.

| Konu | Deal Watcher | fiyat-bot | donanim-arsiv |
| --- | --- | --- | --- |
| Ana yaklaşım | Yerel modüler forum takipçisi | Fiyat ve forum takip scriptleri | Forum anahtar kelime takipçisi |
| Çalıştırma | Sürekli yerel scheduler; kullanıcı servisi | Ayrı Python giriş scriptleri | GitHub Actions veya yerel script |
| Kalıcı durum | SQLite kaynak/konu/olay/teslim tabloları | JSON fiyat/görülen kayıtları | JSON görülen konular; Actions'ta `state` dalı |
| Bildirim | Telegram; opsiyonel Windows toast | Telegram | WhatsApp CallMeBot; opsiyonel Telegram |
| Forum kapsamı | İlk sayfa; kategori/acil sinyal değerlendirmesi | Forum başlık eşleşmeleri | İlk iki sayfa; anahtar kelime, RSS yedeği |
| Kurulum | Üç OS için uv ve yerel yardımcı | Python bağımlılıkları/script yapılandırması | Actions secrets veya yerel ortam değişkenleri |

**fiyat-bot:** `main.py`, `forum_takip.py` ve `notifier.py` fiyat kontrolü, forum eşleşmesi ve Telegram gönderimi için ayrılmış scriptlerdir. JSON yükleme/kaydetme işlevleri içerir. Deal Watcher bu fikri kendi SQLite olay/teslim sözleşmesi, CLI ve kullanıcı servisleriyle uygular. [İncelenen commit](https://github.com/TanrikuluEmre/fiyat-bot/tree/b316b0d2efde926e22c17cd844c77f9ed45cda32).

**donanim-arsiv:** Belgelenen akış iki forum sayfası, anahtar kelime eşleşmesi, sessiz ilk tarama, tur başına bildirim sınırı ve JSON durumudur. Actions durumunu ayrı `state` dalında tutar; WhatsApp ve isteğe bağlı Telegram kullanır. Sessiz başlangıç veya Türkçe normalizasyon yalnız Deal Watcher'a özgü özellikler değildir. Deal Watcher'ın farkı yerel sürekli süreç, SQLite olay/teslim modeli ve kategori önceliklendirmesidir; ikinci sayfa/RSS desteği şu an daha sınırlıdır. [İncelenen commit](https://github.com/0Alduin0/donanim-arsiv/tree/238bc2c6589527aed071efac8c43836f8a32121b).

Referanslar ve mevcut attribution: [ACKNOWLEDGEMENTS.md](../ACKNOWLEDGEMENTS.md). Diğer depoların kodu bu yayına kopyalanmadı; onların lisanslarının Deal Watcher'ın MIT lisansı olduğu varsayılmaz.

## Arkadaşlarınla nasıl paylaşmalısın?

Depo veya release bağlantısını gönder. Her arkadaş kendi botunu oluşturup kurulum rehberindeki üç ortak komutu çalıştırır. Senin token'ın, Chat ID'n, veritabanın ve logların paylaşılmaz. Aynı bot token'ıyla farklı veritabanları paralel çalışırsa aynı fırsat tekrar gönderilebilir.

Sınırlar açık: ilk sayfa, `digest` etiketinin kuyruk olmaması, kapalı Akakçe ve forum HTML değişiklikleri. CI offline testleri işletim sistemlerinde doğrular; canlı Telegram teslimi ve servis açılışı kullanıcının kendi bilgisayarındaki ayrı kontroldür.
