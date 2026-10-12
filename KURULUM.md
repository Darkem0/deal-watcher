# Deal Watcher: proje, kullanım ve kurulum

## Ne işe yarar?

Deal Watcher, Donanım Arşivi Sıcak Fırsatlar forumunu kendi bilgisayarında takip edip yeni fırsatları ve uygun konu değişikliklerini Telegram'a gönderen bir Python uygulamasıdır. Forum sayfasını sürekli elle kontrol etmek yerine, bilgisayarın açık ve çevrimiçiyken takip sürecini çalıştırırsın; bildirimler telefonundaki veya bilgisayarındaki Telegram'a gelir.

Windows, Linux ve macOS'ta aynı çekirdek kullanılır. AIST, Qdrant, GPU, yapay zekâ modeli veya ayrı bir sunucu gerekmez. Bu bir sohbet asistanı değildir; takip bilgisayardaki uygulamadan başlatılır, Telegram bildirim kanalıdır.

## Şu ana kadar neler geliştirildi?

- Forum konularını okuyan parser ve Türkçe/ASCII yazımları değerlendiren ürün sınıflandırması.
- Stok, kupon ve indirim sinyalleri için öncelikler; aksesuarları asıl üründen ayırmaya yardımcı negatif kurallar.
- İlk başarılı taramada mevcut konuları sessizce kaydetme; sonraki yeni/uygun olayları bildirme.
- SQLite'ta konu, olay ve bildirim teslim kayıtları; yeniden başlatmalarda korunabilen tekilleştirme.
- Ağ zaman aşımı, sınırlı tekrar deneme, hata sonrası geri çekilme ve ayarlanabilir tarama gecikmesi.
- Telegram gönderimi, gizli token girişi ve Chat ID bulmaya yardımcı kurulum komutu.
- Windows Task Scheduler, Linux kullanıcı systemd servisi ve macOS LaunchAgent desteği.
- Windows, Ubuntu ve macOS'ta geçen 76 offline test, lint ve paket oluşturma kontrolleri.

Üretim yolunda forumun yalnız ilk liste sayfası izlenir. Varsayılan tarama beş dakika ve ek 10–45 saniye gecikmedir. `digest` bir öncelik etiketidir; gecikmeli toplu bildirim kuyruğu değildir. Akakçe parserları deneysel olarak korunur, canlı takip varsayılan kapalıdır. [Diğer projelerle karşılaştırma](docs/proje-farklari.tr.md).

## Kullanım ve Telegram entegrasyonu

Her kullanıcı kendi BotFather botunu, token'ını ve Chat ID'sini kullanır. Token yerel `.env` dosyasında kalır; forum ayarları `config/forum.yaml`, ağ/bildirim/depolama ayarları `config/settings.yaml` içindedir. Varsayılan kanal Telegram'dır. Mevcut bir botun token'ını da kullanabilirsin; Chat ID bulurken aynı token ile çalışan webhook veya başka getUpdates istemcisi olmamalıdır.

Kurulumdan sonra `uv run deal-watcher run` ile takip başlar, Ctrl+C ile durur. İlk taramada eski konuların topluca gelmemesi normaldir. Başlangıç ve ilk başarılı tarama durum mesajları gelebilir. Otomatik başlatma terminali açık tutma ihtiyacını kaldırır; bilgisayarın kapanması, uyuması veya internetinin kesilmesi yine takibi durdurur.

Bağımsız veritabanlarıyla aynı botu iki bilgisayarda çalıştırmak çift bildirim üretebilir. Token, `.env`, SQLite ve log dosyalarını paylaşma; diğer kullanıcılara depo/sürüm bağlantısını gönder. Gerçek Telegram teslimini ve otomatik servis açılışını kendi bilgisayarında kontrol et; offline CI bunların canlı doğrulaması değildir.

## Ne kadar kaynak tüketir?

12 Ekim 2026'da Linux/Python 3.12 üzerinde yalnız çalışma bağımlılıklarıyla bir ölçüm yapıldı: sentetik HTML ile bir forum taraması, ardından scheduler beklemesi; yaklaşık 12 saniye sonra düzgün kapatma. Canlı forum isteği veya Telegram gönderimi yapılmadı.

| Kaynak | Ölçüm / davranış |
| --- | --- |
| RAM | Bu kısa testte tepe resident bellek **44,09 MiB** |
| CPU | Yaklaşık **12,01 saniyede toplam 0,30 saniye CPU süresi**; başlangıç ve örnek tarama dahil |
| Bağımlılıklar | Geliştirme araçları hariç Python ortamı yaklaşık **32 MiB**; Python yorumlayıcısı ve uv indirme önbelleği buna dahil değil |
| Veritabanı | Küçük test veritabanı **144 KiB**; gerçek kayıt sayısıyla büyür |
| Loglar | Ana uygulama logu 5 MB ve üç yedekle yaklaşık 20 MB'a kadar döndürülür; macOS stdout/stderr logları bu sınıra dahil değildir |
| Ağ | Varsayılan aralıkta saatte yaklaşık 12 veya daha az liste taraması; konu detayları ve bildirimler ek istekler oluşturabilir |

Bu değerler minimum sistem gereksinimi veya uzun dönem gerçek kullanım ortalaması değildir. Canlı sayfa büyüklüğü, kayıt sayısı, hata tekrarları ve işletim sistemi tüketimi değiştirebilir. Windows/macOS için ayrı kaynak ölçümü yapılmadı. GPU kullanılmaz; taramalar arasındaki scheduler döngüsü bekleyerek çalışır. Sabit bir MB/saat ağ tüketimi ölçülmedi.

## Adım adım kurulum

Aşağıdaki akış üç işletim sistemi için aynıdır; ilk kez kullanıyorsan sırayla ilerle.

## 1. uv ve Git

[Git](https://git-scm.com/downloads) ve [uv'nin resmî kurulumunu](https://docs.astral.sh/uv/getting-started/installation/) kullan. `uv` Python 3.12'yi ve proje bağımlılıklarını yönetir; Python'u ayrıca elle kurman gerekmez. Kurulumdan sonra terminali yeniden aç.

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Linux / macOS terminal:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Bu komutlar resmî uv yükleyicisini indirip çalıştırır; alternatif paket yöneticileri yukarıdaki resmî belgede bulunur.

## 2. Projeyi indir

Üç sistemde de:

```sh
git clone https://github.com/Darkem0/deal-watcher.git
cd deal-watcher
uv sync --locked
uv run deal-watcher-setup
```

Git kullanmak istemezsen GitHub'daki **Code → Download ZIP** ile indirip aç; terminali `pyproject.toml` dosyasının olduğu klasörde çalıştır. `.venv` başka bir sistemden kopyalanmaz; her bilgisayarda `uv sync --locked` kullanılır.

## 3. Kendi Telegram botunu bağla

1. Telegram'da [@BotFather](https://t.me/BotFather) ile `/newbot` komutunu kullan. [Resmî Telegram rehberi](https://core.telegram.org/bots/tutorial).
2. Verilen token'ı kurulum yardımcısındaki gizli girişe yapıştır. Hiç kimseye gönderme; GitHub'a koyma.
3. Oluşturduğun botun sohbetini açıp `/start` gönder. Bot kendiliğinden ilk özel mesajı başlatamaz.
4. Chat ID'yi biliyorsan gir. Bilmiyorsan boş bırak; `.env` token ile oluşturulur. Sonra:

```sh
uv run deal-watcher-setup --find-chat
```

Bu komut Telegram'ın `getUpdates` metodunu çağırır; mesaj göndermez ve güncellemeleri offset ile tüketmez. Bulduğu sayısal ID'yi `.env` dosyasındaki `TELEGRAM_CHAT_ID=` alanına yaz. Grup kullanıyorsan botu gruba ekleyip grupta bir komut gönder; grup ID'si negatif olabilir. ID bulunamıyorsa botuna yeniden `/start` gönder. Aynı token ile webhook veya başka bir getUpdates istemcisi çalıştırma.

`.env` örneği (değerleri kendi bilgilerinle doldur):

```dotenv
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Yardımcı mevcut `.env` dosyasını değiştirmez. Değerleri düzeltmek için dosyayı yerel bir metin editörüyle aç. Unix sistemlerinde yeni dosya yalnız sahibinin okuyabileceği izinlerle oluşturulur; Windows erişimi kullanıcı hesabının dosya izinlerine bağlıdır.

## 4. Kontrol et ve çalıştır

```sh
uv run deal-watcher-setup --check
uv run deal-watcher test-notification --send
uv run deal-watcher run
```

İlk komut ağ çağrısı yapmadan YAML ve bildirim biçimini kontrol eder. İkinci komut bir gerçek Telegram mesajı gönderir. Üçüncü komut sürekli forum takibini başlatır.

İlk başarılı tarama eski konuları sessizce kaydeder. Sonraki yeni/uygun olaylar bildirilir. Başlangıç ve ilk başarılı tarama durum mesajı gelebilir. **Ctrl+C** ile durdur. `.env`, `data/` ve `logs/` kişiseldir; arkadaşlarına kaynak kodu bağlantısını ver, bu dosyaları gönderme.

## Otomatik başlatma

Önce yukarıdaki test mesajını doğrula ve terminalde çalışan `run` örneğini Ctrl+C ile kapat. Aşağıdaki kurulum komutları servisi hemen başlatır; başlangıç bildirimi gönderilebilir. Yönetici/root servisi yerine mevcut kullanıcı oturumunda çalışırlar. Oturum kapalı, bilgisayar uyuyor veya internet kesikse bildirim bekleme.

### Windows

Proje klasöründeki PowerShell'de:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_windows_task.ps1 -ProjectRoot "$PWD"
Get-ScheduledTask -TaskName DealWatcher
```

Oturum açınca başlar; `pythonw.exe` ile konsol penceresi açmaz. `0x41301` / `267009` sürekli görev çalışıyor anlamındadır. Yönetici izni gerekirse mevcut script kontrollü UAC isteği açar. Kaldır:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\uninstall_windows_task.ps1
```

### Linux (systemd kullanıcı oturumu)

```sh
sh scripts/install_linux_systemd.sh
systemctl --user status deal-watcher.service
journalctl --user -u deal-watcher.service -n 30
```

`systemctl --user` destekleyen bir oturum gerekir; systemd olmayan dağıtımlarda terminalde `uv run deal-watcher run` kullan. Kaldır:

```sh
sh scripts/uninstall_linux_systemd.sh
```

### macOS

```sh
sh scripts/install_macos_launchd.sh
launchctl print gui/$(id -u)/com.dealwatcher.agent
```

Kullanıcı LaunchAgent'ı olarak oturum açınca başlar. Loglar `logs/launchd.out.log`, `logs/launchd.err.log` ve `logs/deal-watcher.log` içinde. Kaldır:

```sh
sh scripts/uninstall_macos_launchd.sh
```

Kaldırma komutları kaynak, token, veritabanı ve loglarını silmez. Servis dosyası varsa kurulum onu ezmez; güncellemek için önce kaldırıp tekrar kur.

## Güncelleme ve sorun giderme

Botu durdur; `data/` ve `.env` dosyalarını güvenli bir yerde yedekle. Sonra Git kurulumu için `git pull --ff-only` ve `uv sync --locked` çalıştırıp yeniden başlat.

- **Token eksik / mesaj gelmiyor:** `.env`, `/start`, Chat ID ve internet bağlantısını kontrol et; gerçek testi `--send` ile yap.
- **İlk taramada fırsat gelmiyor:** baseline davranışı normaldir; yeni konuları bekle.
- **another instance:** diğer terminal veya otomatik servis örneğini durdur. Aynı veritabanıyla iki süreç başlatma.
- **HTTP 403 / forum değişti:** erişimi zorlamadan logları incele; hata kaydını kişisel verilerden temizleyerek issue aç.
- **Bilgisayar kapalıyken bildirim gelmiyor:** bot yerelde çalışır; GitHub Actions bu projede yalnız test yapar.
- **Akakçe çalışmıyor:** varsayılan olarak deneysel ve kapalıdır; forum takibi için gerekli değildir.

Sorun bildirirken işletim sistemi, komut ve redakte edilmiş hata metnini paylaş; token, Chat ID, `.env` veya SQLite yükleme.
