# 🪟 Windows: izinler ve sık sorunlar

[← Ana sayfa](../README.md) · [Telegram bağlantısı](telegram-kurulum.md)

## Normal açılış

1. `deal-watcher-windows-v0.3.0-alpha.zip` dosyasını indir.
2. ZIP'e sağ tık → **Tümünü ayıkla**. Çıkan `deal-watcher` klasörünü aç.
3. **`Baslat-Windows.cmd`** dosyasına çift tıkla.
4. `uv` kurulumu sorulursa onay ver; bağımlılıklar indirildikten sonra Telegram yardımcısı başlar.

Yönetici olarak çalıştırman normal kurulum için gerekmez. Dosya uzantılarını göremiyorsan Dosya Gezgini'nde **Görünüm → Göster → Dosya adı uzantıları** seçeneğini aç; başlatıcı `.cmd` ile biter.

## “Windows bilgisayarınızı korudu” veya indirilmiş dosya engeli

Dosyayı yalnız bu deponun release bağlantısından indirdiğini kontrol et. Windows sürümüne göre dosya özelliklerinde **Engellemeyi kaldır** veya SmartScreen ekranında **Ek bilgi** seçeneği bulunabilir. Yalnız kaynağını doğruladığın bu dosya için sunulan çalıştırma seçeneğini kullan. Güvenlik ayarlarını sistem genelinde kapatma. Kurum bilgisayarında politika engelliyorsa yöneticinle görüş.

## PowerShell scripti çalışmıyor

`.cmd` başlatıcı kendi PowerShell çağrısını `-ExecutionPolicy Bypass` ile **yalnız o süreç için** yapar; kalıcı makine ayarını değiştirmez. Kurumsal kısıtlama bunu da engelleyebilir. `Set-ExecutionPolicy Unrestricted` gibi genel değişiklikler gerekli değildir.

## Pencere açılıp kapanıyor / dosya bulunamadı

- Tek başına `.cmd` dosyasını indirme: `scripts`, `src`, `config`, `pyproject.toml` ve `uv.lock` aynı klasör ağacında olmalı.
- ZIP içindeyken açma; önce tümünü çıkart.
- Hata normalde `.cmd` sonundaki bekleme sayesinde görünür. Proje klasöründe terminal açıp `./Baslat-Windows.cmd` ile tekrar çalıştır.
- Klasörü `Program Files` gibi korumalı bir yere koyma; kullanıcı Downloads veya Documents klasöründe tut.

## İnternet / uv / Python indirmesi başarısız

İlk kurulum resmî uv yükleyicisini, Python'u ve paketleri indirir. Ağ erişimi gerekir. Ağ politikası veya antivirüs engelini incele; TLS doğrulamasını kapatma. İstersen [resmî uv kurulumu](https://docs.astral.sh/uv/getting-started/installation/) ile uv kurup başlatıcıyı yeniden aç.

## Birden fazla bot / arka plan

“Bot zaten çalışıyor” çıkarsa diğer terminali veya `DealWatcher` görevini durdur; ikinci süreç açma. Pencereyi kapatırsan bu şekilde başlatılan bot durur. Arka planda oturum açınca başlatma için [Task Scheduler adımları](kurulum.md#windows).

Sorun devam ederse işletim sistemi ve token'dan temizlenmiş hata metniyle [issue aç](https://github.com/Darkem0/deal-watcher/issues/new/choose). `.env`, Chat ID veya SQLite yükleme.
