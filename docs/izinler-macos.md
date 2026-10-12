# 🍎 macOS: izinler ve sık sorunlar

[← Ana sayfa](../README.md) · [Telegram bağlantısı](telegram-kurulum.md)

## Normal açılış

1. `deal-watcher-macos-v0.3.0-alpha.zip` dosyasını indir.
2. ZIP'e çift tıkla; çıkan `deal-watcher` klasörünü aç.
3. **`Baslat-macOS.command`** dosyasını aç. Terminal penceresi gelir.
4. `uv` kurulumunu onayla; Python ve paketler uygun mimariyle kurulunca Telegram yardımcısı başlar.

Intel veya Apple Silicon için aynı paket kullanılır; Python'u uv sistem mimarisine göre seçer. Başlatıcıda sudo kullanılmaz. Bu dosya imzalı/notarize bir `.app` değildir; sistem izin kontrolü gösterebilir.

## Çalıştırma izni yok / metin olarak açılıyor

Finder'da klasöre sağ tıkla; **Klasörde Yeni Terminal** servisi varsa onu kullan. Alternatif olarak Terminal'i aç, `cd ` yazıp klasörü pencereye sürükle ve Enter bas. Klasörde:

```sh
chmod +x Baslat-macOS.command
./Baslat-macOS.command
```

Veya scripti Terminal'de açıkça bash ile çalıştır:

```sh
bash Baslat-macOS.command
```

## Tanımlanamayan geliştirici / Apple doğrulama uyarısı

İndirme kaynağının bu deponun release sayfası olduğunu kontrol et. Güvendiğin dosyada macOS'un **Sistem Ayarları → Gizlilik ve Güvenlik → Yine de Aç** seçeneği sunuluyorsa yalnız bu dosya için kullan. macOS sürümüne göre seçenekler değişebilir. [Apple'ın resmî açıklaması](https://support.apple.com/en-us/102445).

Gatekeeper'ı sistem genelinde devre dışı bırakma. “Bilgisayarınıza zarar verecek” gibi bir uyarıyı sıradan geliştirici uyarısı sayma; çalıştırmadan önce incele. Kurum politikası engelliyorsa yöneticine başvur.

## Downloads / Documents erişim izni

Terminal klasöre erişirken macOS izin isteyebilir; gerekli proje klasörü erişimini ver. Uygulama için genel **Tam Disk Erişimi** gerekmiyor. Yazılabilir kullanıcı klasörü kullan; salt okunur diskten veya ZIP içinden açma.

## Token yapıştırırken yazı yok

Gizli giriş olduğu için normaldir. Command+V ile yapıştırıp Enter bas. [Telefondan Telegram rehberi](telegram-kurulum.md).

## Terminal kapanınca takip duruyor / uyku

Terminalden başlatılan örnek için pencere açık kalmalı. Uyku sırasında forum taranmaz. Oturum açınca arka planda başlatmak için [kullanıcı LaunchAgent kurulumu](kurulum.md#macos). Bu yöntem oturumsuz bir root LaunchDaemon kurmaz.

## İndirme veya ağ hatası

İlk kurulum internet ister. uv kurulmazsa [resmî uv belgesini](https://docs.astral.sh/uv/getting-started/installation/) izle; farklı bilgisayardan `.venv` kopyalama. macOS/Intel ortamında native ilk açılış bu yayında ayrıca denenmedi; CI macOS runner'ında offline test ve paket başlatma kontrolü yapılır.
