# Windows, Linux ve macOS kurulumu

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
