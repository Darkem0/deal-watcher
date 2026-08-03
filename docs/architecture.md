# Mimari

YAML yapılandırması Pydantic modelleriyle sözdizimsel ve semantik olarak doğrulanır. Kaynak adapter'ları HTML'i kaynak-spesifik seçicilerle ayrıştırıp storage'dan bağımsız domain modelleri üretir. Servis katmanı önceki SQLite durumuyla karşılaştırarak baseline, değişim, sınıflandırma ve olay kararlarını verir. Repository katmanı SQL'i parser ve domain mantığından izole eder. Dispatcher yalnız veritabanına kalıcı yazılmış ve ilgili kanal için teslim edilmemiş olayları notifier'a yollar.

Katmanlar:

- `models/`: Pydantic config ve storage/HTML'den bağımsız domain tipleri.
- `sources/`: Kaynak-spesifik parser/adaptörler; canlı ağ erişimi henüz yok.
- `services/`: Baseline, değişim, kategori ve öncelik kararları.
- `storage/`: SQLite migration ve repository.
- `notifiers/`: Ortak protokol, dry-run/logging ve ayrı Windows/macOS adapter'ları.
- `runtime.py`: UTC/gösterim zamanı, güvenli kapanma sinyali ve host-bazlı instance lock.

Çekirdekte sabit işletim sistemi yolu yoktur; `pathlib.Path` ve YAML/CLI yolları kullanılır. Platform ayrımı notifier/deployment adapter'larında `platform.system()` ile sınırlıdır. SQLite'taki tüm uygulama zamanları UTC ISO-8601 olarak saklanır; kullanıcı gösterimi `Europe/Istanbul` zoneinfo dönüşümüyle yapılır.

Yerel instance lock aynı makinede iki scheduler'ı engeller. İki ayrı makinede (örneğin Windows ve Mac) aynı anda çalışma host kilidiyle engellenemez; aynı paylaşılan SQLite kullanılmıyorsa her makine kendi event/delivery anahtarını üreteceği için çift bildirim riski vardır.
