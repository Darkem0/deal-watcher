# Deal Watcher

Windows üzerinde çalışan, yalnızca fırsatları izleyen ve bildirim üreten yerel takip sistemi. Otomatik satın alma, sepet/ödeme işlemi veya CAPTCHA/erişim kontrolü aşma içermez.

## Kurulum

```powershell
uv venv --python 3.12 .venv
uv sync --locked
Copy-Item .env.example .env
uv run deal-watcher validate-config
uv run deal-watcher once --source forum --dry-run
uv run deal-watcher test-notification --dry-run
```

Gerçek secret değerleri Git’e koymayın. `.env.example` yalnız gerekli değişkenleri gösterir; gerçek `.env` dosyası yerel kalmalıdır:

```powershell
Copy-Item .env.example .env
```

## Çalıştırma

Donanım Arşivi takibi aktif üretim özelliğidir. İlk offline forum taraması baseline oluşturur ve bildirim göndermez:

```powershell
.\.venv\Scripts\python.exe -m deal_watcher.cli forum-scan --fixture tests\fixtures\forum_baseline.html --database data\demo.sqlite3
.\.venv\Scripts\python.exe -m deal_watcher.cli once --source forum --dry-run --forum-fixture tests\fixtures\forum_update.html --database data\demo.sqlite3
```

Genel tek seferlik tarama ve sürekli runtime:

```powershell
uv run deal-watcher once --source all --dry-run
uv run deal-watcher once --source forum --dry-run
uv run deal-watcher run
uv run deal-watcher test-notification
```

`--dry-run` gerçek Telegram veya Windows bildirimi göndermez. Gerçek bildirim için secret ayarları ve ayrıca açıkça onaylanmış operasyon gerekir.

Gerçek Telegram testi yalnız token ve chat ID ayarlandıktan sonra, kullanıcı onayıyla çalıştırılmalıdır:

```powershell
uv run deal-watcher test-notification --send
```

Akakçe parserı deneysel ve varsayılan olarak kapalıdır. `--source akakce` açıkça etkinleştirilmeden çalıştırılırsa ağ isteği yapmadan `source disabled` sonucu verir. Deneysel offline parser testleri korunur; etkinleştirmek için `config/settings.yaml` içindeki `akakce.enabled` değeri açıkça `true` yapılmalıdır.

## Windows Task Scheduler

Script önce mevcut kullanıcı için `Interactive/Limited` görev kaydını dener. Windows erişim politikası izin vermezse ve `-NoElevation` verilmemişse kendisini yalnız bir kez UAC ile yükseltir. Var olan görevi değiştirmek için açıkça `-Force` gerekir. Varsayılan davranış yalnızca kullanıcı oturum açtığında çalışır; kullanıcı oturumu yokken çalışma için ek Windows yetkisi/credential gerekir.

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\scripts\install_windows_task.ps1" -ProjectRoot "C:\Users\emre\Documents\deal-watcher"
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\scripts\install_windows_task.ps1" -ProjectRoot "C:\Users\emre\Documents\deal-watcher" -AtStartup -Force
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\scripts\uninstall_windows_task.ps1" -TaskName DealWatcher
```

## Depolama ve operasyon

- SQLite: `data/deal_watcher.sqlite3` (config’den değiştirilebilir)
- Log: `logs/deal-watcher.log`, dönen dosya loglarıyla sınırlıdır.
- Backup: `uv run deal-watcher backup-db --destination data\backup.sqlite3`
- HTTP client timeout, sınırlı retry/backoff, jitter, `Retry-After`, User-Agent, response boyutu ve içerik türü kontrolleri uygular.
- 401/403, CAPTCHA/challenge ve rate-limit durumlarında erişim kontrolü aşılmaz; CAPTCHA, proxy veya başka bir bypass uygulanmaz.
- Canlı Akakçe HTTP erişimi 403 döndürdüğü için doğrulanamamıştır. Fiyat alarmı için Akakçe’nin resmi “Fiyatı Takip Edin” özelliği önerilir.
- Playwright yalnız `experimental` extra içindedir: `uv sync --extra experimental`. Bu, canlı Akakçe’yi üretim kapsamına almaz ve erişim kontrolünü aşmaz.
- Araç otomatik satın alma, sepet veya ödeme işlemi yapmaz. Kullanıcı site kullanım koşullarına ve makul tarama sıklığına uymalıdır.

Durum için [STATUS.md](STATUS.md), kararlar için [DECISIONS.md](DECISIONS.md), fixture sözleşmesi için [docs/fixtures.md](docs/fixtures.md) ve operasyon ayrıntıları için [docs/operations.md](docs/operations.md) dosyalarına bakın.
