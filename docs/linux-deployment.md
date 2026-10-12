# Linux dağıtımı

Güncel kurulum: [KURULUM.md](kurulum.md#linux-systemd-kullanıcı-oturumu).

Servis `~/.config/systemd/user/deal-watcher.service` içinde; localhost database ve `.env` proje klasöründedir. Kurulum systemd kullanıcı oturumu kullanır, sudo gerektirmez. Servis yönetim yardımcısı yolları quote eder ve systemd `%` specifierlarını escape eder. Kaldırma kullanıcı verisini korur.
