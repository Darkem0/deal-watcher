# Windows dağıtımı

Geliştirme/test ortamı Windows'tur. .venv, YAML doğrulaması ve tüm offline
testler operations.md komutlarıyla çalışır. Yerel bildirim WindowsToastNotifier
adaptöründedir ve uv sync --extra notifications gerektirir.

install_windows_task.ps1 preflight sonrasında görevi mevcut kullanıcı için
Interactive ve Limited principal ile kaydeder. Varsayılan tetikleyici kullanıcı
girişidir; -AtStartup sistem başlangıcını seçer. Görev, proje kökünden
.venv\Scripts\python.exe -m deal_watcher.cli run komutunu çalıştırır; .env
buradan yüklenir, log klasörü oluşturulur ve Akakçe kapalı kalır.

Erişim reddedilirse, -NoElevation verilmemişse script kendisini tek sefer UAC
ile yükseltir. Var olan görev -Force olmadan değiştirilmez. Kullanıcı
oturumu yokken çalıştırma Interactive principal yerine ayrıca Windows
admin/credential kararı gerektirir.

Kurulum:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\scripts\install_windows_task.ps1" -ProjectRoot "C:\Users\emre\Documents\deal-watcher"
```

Kurulumdan sonra doğrulama:

```powershell
Get-ScheduledTask -TaskName "DealWatcher"
Get-ScheduledTaskInfo -TaskName "DealWatcher"
Start-ScheduledTask -TaskName "DealWatcher"
Start-Sleep -Seconds 15
Get-ScheduledTaskInfo -TaskName "DealWatcher"
```

pwsh.exe yoksa script powershell.exe fallback kullanır. Kaldırma scripti
yalnız belirtilen görevi hedefler ve aynı UAC modelini kullanır:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\scripts\uninstall_windows_task.ps1" -TaskName "DealWatcher"
```
