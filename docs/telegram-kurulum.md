# 💬 Telegram botunu bağla — telefondan adım adım

[← Ana sayfa](../README.md)

Bu işlemi ilk kurulumda bir kez yapacaksın. Telegram'ın ücretsiz BotFather aracı sana ait bir bot oluşturur; Deal Watcher onun üzerinden bildirim gönderir. Telefon ve bilgisayarda **aynı Telegram hesabını** kullanmak token'ı kopyalamayı kolaylaştırır.

## 1 · Telefonda resmî BotFather'ı aç

[**Telegram'da @BotFather'ı aç →**](https://t.me/BotFather)

Aramayla buluyorsan kullanıcı adı tam olarak `@BotFather` ve resmî doğrulanmış hesap olmalı. Sohbeti açıp **Başlat / Start** düğmesine dokun.

## 2 · Yeni bot oluştur

Sohbete `/newbot` yaz. BotFather iki şey ister:

| Soru | Ne yazacaksın? |
| --- | --- |
| Botun görünen adı | Örneğin `Benim Fırsat Takipçim` |
| Kullanıcı adı | Benzersiz bir ad; `bot` ile bitmeli. Örneğin `benim_firsatlarim_2026_bot` |

Örnek kullanıcı adı alınmışsa farklı bir ad seç. BotFather sonunda botunun bağlantısını ve **token** verir. Token, botun anahtarıdır; burada örnek bir gerçek token gösterilmiyor.

## 3 · Bilgisayarda başlatıcıyı aç

ZIP'i tamamen çıkartmış olmalısın. Sistemine göre:

- Windows: **`Baslat-Windows.cmd`** dosyasına çift tıkla.
- macOS: **`Baslat-macOS.command`** dosyasını aç.
- Linux: **`Baslat-Linux.sh`** dosyasını program olarak aç veya terminalde `bash Baslat-Linux.sh` çalıştır.

İlk açılışta `uv` yoksa kurulum için onay istenir. Python ve bağımlılıklar indirilirken bekle. Daha sonra terminalde Telegram kurulumu başlar.

## 4 · Token'ı kopyala

Bilgisayarda [Telegram Desktop](https://desktop.telegram.org/) veya [Telegram Web](https://web.telegram.org/) üzerinden kendi hesabındaki BotFather sohbetini aç. Telefonda gördüğün token aynı sohbette bulunur; oradan kopyala. Token'ı arkadaşlarına, issue'lara veya ekran görüntülerine koyma.

Terminalde `Bot token:` sorusuna yapıştır:

| Sistem | Yapıştırma |
| --- | --- |
| Windows | Ctrl+V veya terminale sağ tık |
| macOS | Command+V |
| Linux | Ctrl+Shift+V; terminaline göre sağ tık da olabilir |

**Hiçbir harf görünmemesi normaldir.** Gizli giriş token'ı ekrana yazmaz. Yapıştırdıktan sonra Enter bas.

## 5 · Chat ID'yi otomatik bul

Terminal `Chat ID biliyorsanız yazın; otomatik bulmak için Enter:` dediğinde **boş bırakıp Enter bas**.

Şimdi telefonda BotFather'ın verdiği **kendi botunun bağlantısını aç**. `@BotFather` sohbetine değil, yeni oluşturduğun bota **`/start`** gönder.

Bilgisayardaki terminale dön ve Enter bas. Yardımcı Telegram'dan sohbeti okur:

```mermaid
flowchart LR
    A[Telefonda kendi botunu aç] --> B[/start gönder]
    B --> C[Bilgisayarda Enter bas]
    C --> D[Sohbet bulundu]
    D --> E[Takip başlar]
```

Tek sohbet varsa otomatik seçilir. Birden fazla sohbet varsa listeden **sıra numarasını** seçersin. Token ve Chat ID yalnız bilgisayarındaki `.env` dosyasına kaydedilir; dosya düzenlemek zorunda değilsin.

> [!NOTE]
> Bot `/start` mesajına cevap vermeyebilir. Bu normal: Deal Watcher sohbet botu değil, bildirim göndericisidir. `/start`, senin botunun sana mesaj gönderebilmesi ve kurulum yardımcısının sohbeti görebilmesi için kullanılır.

## 6 · Başladı mı?

Terminalde **“Takip başlıyor”** görünür. Başlangıç ve ilk başarılı tarama durum mesajı gelebilir. İlk tarama mevcut konuları sessizce kaydeder; eski fırsatlar topluca gönderilmez. Yeni/uygun konular sonraki taramalarda bildirilir.

Pencereyi açık tut. **Ctrl+C** ile durdur. Bir sonraki kullanımda aynı başlatıcıyı açman yeterli; kayıtlı token ve sohbet korunur. Bilgisayar kapalı veya uyuyorsa takip de durur. [Otomatik başlatma](kurulum.md#otomatik-başlatma).

## Bir gruba bildirim göndermek istersen

1. Botunu gruba ekle. Yönetici olması yalnız normal grup mesajı göndermek için şart değildir; grubun izinleri botların yazmasına izin vermeli.
2. Grupta botuna yönelik bir komut gönder; örneğin `/start@senin_bot_kullanici_adin`.
3. İlk kurulumdaki sohbet listesinde `group` veya `supergroup` olan satırı seç.
4. Zaten özel sohbetle kurduysan [manuel ayar](#manuel-kurulum-isteğe-bağlı) üzerinden ilgili Chat ID'yi `.env` dosyasında değiştir; çalışan botu önce durdur.

Grup ID'sinin negatif olması normaldir. Kanal kurulumu bu rehberin temel özel-sohbet akışından farklıdır; kanalda mesaj için botun uygun yönetici yetkisi olmalıdır.

## Sık takılan yerler

| Sorun | Yapılacak işlem |
| --- | --- |
| “Sohbet bulunamadı” | `/start` mesajını BotFather'a değil **kendi botuna** gönder; ardından tekrar denemeyi seç |
| “Telegram'a erişilemedi” | Token'ın tamamını kopyaladığını ve internetini kontrol et |
| Token girişinde yazı yok | Gizli giriş normal; yapıştır ve Enter bas |
| Başlangıç mesajı var, fırsat yok | İlk tarama sessizdir; yeni konuları bekle |
| Yanlış sohbete gidiyor | Botu durdur; `.env` içindeki `TELEGRAM_CHAT_ID` alanını doğru sohbetle değiştir |
| Aynı token başka bot yazılımında kullanılıyor | Chat bulma sırasında webhook veya başka `getUpdates` istemcisi çakışabilir; ayrı bir bot oluşturmak en kolay çözümdür |
| Token ifşa oldu | Resmî BotFather üzerinden token'ı yenile; yerel `.env` dosyasını güncelle |

## Manuel kurulum (isteğe bağlı)

Başlatıcı yerine komut kullanmak istersen proje klasöründe:

```sh
uv sync --locked
uv run deal-watcher-setup --guided
uv run deal-watcher run
```

Mevcut token ile sohbet ID'lerini görmek:

```sh
uv run deal-watcher-setup --find-chat
```

Gerçek bir test mesajı göndermek için:

```sh
uv run deal-watcher test-notification --send
```

Bu son komut gerçek Telegram mesajı gönderir. Kurulum yardımcısı mevcut dolu alanları değiştirmez; yalnız eksik bağlantı bilgilerini tamamlar. [Telegram'ın resmî bot rehberi](https://core.telegram.org/bots/tutorial).
