# Apple Silicon macOS dağıtımı

Hedef kalıcı ortam 16 GB RAM'li Mac mini M4'tür; bu aşamada hedef makinede kurulum yapılmamıştır. Python/uv bağımlılıkları platform-native Apple Silicon paketlerinden kurulmalı, `.venv/bin/python` kullanılmalıdır. Yerel bildirim `MacOSNotifier`, servis yönetimi launchd adapter'ındadır.

`deployment/macos/com.dealwatcher.agent.plist.example` ve `scripts/install_macos_launchd.sh` scheduler hazır olduğunda kullanıcı `~/Library/LaunchAgents` dizinine kurulum için şablondur. Script scheduler bulunmadığı sürece bilerek kurulum yapmaz; kaldırma `scripts/uninstall_macos_launchd.sh` ile yapılır. Shell scriptlerine çalıştırma izni gerekebilir: `chmod +x scripts/*macos*.sh`.

Windows ve Mac aynı anda ayrı SQLite dosyalarıyla etkin olursa kalıcı dedup anahtarları paylaşılmaz ve çift bildirim oluşabilir. Taşınma sırasında eski host kapatılmalı, SQLite güvenli biçimde kopyalanıp doğrulanmalı ve yalnız yeni host başlatılmalıdır.
