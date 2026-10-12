# 🐧 Linux: izinler ve sık sorunlar

[← Ana sayfa](../README.md) · [Telegram bağlantısı](telegram-kurulum.md)

## Normal açılış

1. `deal-watcher-linux-v0.3.0-alpha.zip` dosyasını indirip çıkart.
2. Çıkan `deal-watcher` klasöründe **`Baslat-Linux.sh`** dosyasını program olarak çalıştır.
3. Dosya yöneticisi bunu desteklemiyorsa klasöre sağ tık → **Terminalde Aç**, sonra:

```sh
bash Baslat-Linux.sh
```

Normal başlatma sudo veya systemd istemez. İlk açılışta uv kurulumuna onay ver; Python ve paketlerden sonra Telegram yardımcısı gelir.

## Dosya metin editöründe açılıyor

Linux masaüstü ortamlarının script açma davranışı farklıdır. Dosya özelliklerinde **İzinler → Program olarak çalıştırılmasına izin ver** seçeneği varsa aç; yine de en taşınabilir yol `bash Baslat-Linux.sh` komutudur. Terminalde doğrudan açmak için:

```sh
chmod +x Baslat-Linux.sh
./Baslat-Linux.sh
```

## curl veya unzip bulunamadı

Ubuntu / Debian için, bu paketler eksikse:

```sh
sudo apt update
sudo apt install curl unzip
```

Fedora için `sudo dnf install curl unzip`; Arch için `sudo pacman -S curl unzip`. Paket kurulumu dağıtım yöneticisinin iznini isteyebilir; botu sudo ile başlatma. ZIP'i bir arşiv yöneticisiyle de çıkartabilirsin.

## Permission denied / salt okunur disk

Yazılabilir kullanıcı klasörü kullan. Tüm klasör ağacı aynı yerde olmalı; yalnız `.sh` dosyasını indirme. Harici diskte `noexec` olabilir: dosyayı kullanıcı klasörüne çıkartıp tekrar dene. `.venv` klasörünü başka işletim sisteminden taşıma.

## uv / Python indirmesi başarısız

İlk kurulum internet ister. [Resmî uv kurulum seçenekleri](https://docs.astral.sh/uv/getting-started/installation/) alternatif sunar. Ağ/proxy/politika sorunlarını düzelt; TLS kontrollerini kapatma. Desteklenmeyen çok eski sistem veya mimaride paket kurulumu başarısız olabilir; bu sürüm bütün Linux dağıtımlarında native olarak test edilmiş değildir.

## Arka plan servisi / systemd

Doğrudan başlatıcı systemd kullanmaz. Otomatik açılış istersen [kullanıcı systemd servisini](kurulum.md#linux-systemd-kullanıcı-oturumu) kur. `systemctl --user` çalışmıyorsa oturumun systemd kullanıcı servisi sağlamıyor olabilir; terminalde çalışan yöntemi kullan.

“Bot zaten çalışıyor” çıkarsa diğer pencereyi veya `deal-watcher.service` örneğini durdur. Terminali kapatmak ya da bilgisayarı uyutmak bu yöntemle yapılan takibi durdurur.
