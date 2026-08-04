# Windows dağıtımı

Bu rehber Windows 10/11 üzerinde Python 3.12+, `uv` ve Telegram kurulumu varsayar. Örnek proje yolu `C:\Projects\deal-watcher` olarak nötr tutulmuştur.

## Kurulum

```powershell
git clone https://github.com/Darkem0/deal-watcher.git C:\Projects\deal-watcher
Set-Location C:\Projects\deal-watcher
uv sync --locked
Copy-Item .env.example .env
uv run deal-watcher validate-config
```

`.env` içine BotFather’dan alınan tokenı ve hedef chat ID’yi yazın. Gerçek değerleri commit etmeyin. Önce dry-run:

```powershell
uv run deal-watcher test-notification --dry-run
```

Açıkça izin verilen kontrollü Telegram testi:

```powershell
uv run deal-watcher test-notification --send
```

## Forum ve baseline

```powershell
uv run deal-watcher once --source forum --dry-run
```

İlk başarılı tarama mevcut konuları baseline yapar; eski konular topluca bildirilmez. Yeni konu ve dedup davranışı fixture testleriyle doğrulanır.

## Task Scheduler

Varsayılan görev mevcut kullanıcı için `Interactive`/`Limited` principal ve `AtLogOn` trigger kullanır:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\scripts\install_windows_task.ps1" -ProjectRoot "C:\Projects\deal-watcher"
Get-ScheduledTask -TaskName DealWatcher
Get-ScheduledTaskInfo -TaskName DealWatcher
```

Script önce normal kullanıcı kaydını dener. Windows erişim politikası izin vermezse bir kez UAC self-elevation yapar. `-NoElevation` ile yükseltme kapatılabilir. `-Force` mevcut görevi açıkça günceller.

Görev oturum açıldığında çalışır; kullanıcı oturumu olmadan SYSTEM/credential ile çalıştırma bu kurulumun varsayılanı değildir. Akakçe kapalıdır; Forum aktiftir.

Forum ilk sayfası yaklaşık beş dakikada bir taranır. Task Scheduler idle sonlandığında görevi durdurmayacak şekilde yapılandırılır; sürekli runtime için execution time limit de kapatılır.

`LastTaskResult=267009` veya `0x41301`, görevin çalışıyor olduğunu gösterir; hata değildir. Görev loglarını `logs/deal-watcher.log` altında, secret içermeyecek biçimde kontrol edin.

## Durdurma, başlatma, kaldırma

```powershell
Stop-ScheduledTask -TaskName DealWatcher
Start-ScheduledTask -TaskName DealWatcher
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\scripts\uninstall_windows_task.ps1" -TaskName DealWatcher
```

Kaldırma yalnız belirtilen görev adını siler; görev yoksa anlaşılır biçimde tamamlanır.

## Sorun giderme

- Config hatasında `uv run deal-watcher validate-config` çalıştırın.
- `0x80070005` için UAC davranışını ve `-NoElevation` seçimini kontrol edin.
- `Running` ve `267009` normal sürekli runtime durumudur.
- Telegram hatasında token/chat ID’nin yalnız `.env` içinde olduğunu ve loglarda redaction bulunduğunu kontrol edin.
- 403/CAPTCHA için bypass denemeyin; kaynağı disabled/experimental tutun.
