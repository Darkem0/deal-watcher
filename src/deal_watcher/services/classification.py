from __future__ import annotations

import re
from dataclasses import dataclass

from deal_watcher.models.config import ForumConfig
from deal_watcher.models.domain import ForumTopic, ForumTopicDetail, NotificationPriority

CATEGORY_TERMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("complete_system", ("hazır sistem", "hazir sistem", "oyun bilgisayarı")),
    ("gpu", ("ekran kartı", "ekran karti", "gpu", "rtx", "radeon")),
    (
        "cpu_cooler",
        (
            "işlemci soğutucu",
            "islemci sogutucu",
            "cpu cooler",
            "termal macun",
            "thermalright",
            "phantom spirit",
        ),
    ),
    ("cpu", ("işlemci", "islemci", "ryzen", "intel core")),
    ("motherboard", ("anakart", "x870", "b650")),
    ("memory", (" ram", "ram ", "ddr4", "ddr5", "bellek")),
    ("storage", ("ssd", "nvme", "hard disk", "hdd")),
    ("power_supply", ("psu", "güç kaynağı", "guc kaynagi")),
    ("monitor", ("monitör", "monitor")),
    ("laptop", ("laptop", "notebook", "dizüstü", "dizustu")),
    ("phone_tablet_watch", ("akıllı telefon", "tablet", "akıllı saat", "watch")),
    ("audio", ("kulaklık", "mikrofon", "hoparlör")),
    ("supplement", ("whey", "protein tozu", "takviye")),
    ("cooling_and_fans", ("fan", "sıvı soğutma", "hava soğutma")),
    ("pc_case", ("kasa", "bilgisayar kasası")),
    ("peripherals", ("klavye", "fare", "mouse", "webcam")),
    ("networking", ("router", "modem", "wifi", "wi-fi", "ağ ürünü")),
    ("bank_campaign", ("banka kampanyası", "bankamatik", "world puan", "maximum")),
    ("grocery", ("market", "kahve", "deterjan", "gıda")),
)

EXCLUSIONS = {
    "gpu": ("ekran kartı tutucu", "hazır sistem", "hazir sistem", "ekran kartı standı"),
    "cpu": ("işlemci soğutucu", "islemci sogutucu", "termal macun"),
    "storage": ("ssd kutusu", "nvme kutusu"),
    "power_supply": ("psu kablosu", "güç kaynağı kablosu"),
    "phone_tablet_watch": ("watch kayışı", "watch kayisi", "saat kayışı"),
}

URGENT_SIGNAL_TERMS: dict[str, tuple[str, ...]] = {
    "fiyat_hatasi": ("fiyat hatası", "fiyat hatasi", "yanlış fiyat", "yanlis fiyat"),
    "son_stok": ("son stok",),
    "bir_veya_iki_stok": ("1 stok", "2 stok", "1 adet", "2 adet", "bir stok", "iki stok"),
    "sinirli_stok": ("sınırlı stok", "sinirli stok"),
    "tekrar_stokta": ("tekrar stokta", "yeniden stokta", "stok geri geldi"),
    "guclu_kupon": ("güçlü kupon", "guclu kupon", "kupon kodu", "kuponla"),
    "sepette_indirim": ("sepette indirim", "sepette"),
    "olagan_disi_dusuk_fiyat": ("olağan dışı düşük fiyat", "olagan disi dusuk fiyat"),
}

TURKISH_ASCII_TRANSLATION = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
    }
)


@dataclass(frozen=True, slots=True)
class Classification:
    category: str
    priority: NotificationPriority
    reason: str
    secondary_categories: tuple[str, ...] = ()


def _fold_text(value: str) -> str:
    folded = value.casefold().replace("i\u0307", "i").translate(TURKISH_ASCII_TRANSLATION)
    return re.sub(r"\s+", " ", folded)


def normalize_text(value: str) -> str:
    return _fold_text(value).strip()


def _contains_any(haystack: str, terms: tuple[str, ...]) -> bool:
    return any(_fold_text(term) in haystack for term in terms)


def _configured_urgent_terms(signal: str) -> tuple[str, ...]:
    return URGENT_SIGNAL_TERMS.get(signal, (signal.replace("_", " "),))


def classify_topic(
    topic: ForumTopic,
    config: ForumConfig,
    detail: ForumTopicDetail | None = None,
    target_names: tuple[str, ...] = (),
) -> Classification:
    detail = detail or topic.detail
    parts = [*topic.prefix_labels, topic.title]
    if detail is not None:
        parts.append(detail.first_message)
        parts.extend(detail.product_names)
    haystack = normalize_text(" ".join(parts))
    found = [
        candidate for candidate, terms in CATEGORY_TERMS if _contains_any(haystack, terms)
    ]
    for candidate, terms in EXCLUSIONS.items():
        if candidate in found and _contains_any(haystack, terms):
            found.remove(candidate)
    target_haystack = normalize_text(" ".join(target_names))
    target_category = next(
        (
            candidate
            for candidate, terms in CATEGORY_TERMS
            if _contains_any(target_haystack, terms)
        ),
        None,
    )
    category = (
        target_category
        if target_category in found
        else next((item for item in found if item in config.categories), "other")
    )
    secondary = tuple(item for item in found if item != category and item in config.categories)
    target_match = any(normalize_text(name) in haystack for name in target_names)
    urgent = target_match or any(
        _contains_any(haystack, _configured_urgent_terms(signal))
        for signal in config.urgent_signals
    )
    if detail is not None:
        normalized_stock_status = normalize_text(detail.stock_status or "")
        urgent = urgent or detail.back_in_stock or detail.personalized_coupon or detail.cart_discount
        urgent = urgent or normalized_stock_status in {
            normalize_text("son stok"),
            normalize_text("1 adet"),
            normalize_text("2 adet"),
            normalize_text("sınırlı stok"),
        }
    relevant = [category, *secondary]
    if urgent or any(item in config.priorities.urgent_categories for item in relevant):
        priority = NotificationPriority.URGENT
    elif any(item in config.priorities.normal_categories for item in relevant):
        priority = NotificationPriority.NORMAL
    else:
        priority = NotificationPriority.DIGEST
    return Classification(category, priority, f"kategori={category}", secondary)


def topic_signals(topic: ForumTopic) -> set[str]:
    text = normalize_text(
        " ".join(
            (*topic.prefix_labels, topic.title, topic.detail.first_message if topic.detail else "")
        )
    )
    signals: set[str] = set()
    if _contains_any(text, ("tekrar stokta", "stok geri", "yeniden stokta")):
        signals.add("stok_geri_geldi")
    if _contains_any(text, ("indirim bitti",)):
        signals.add("indirim_bitti")
    if topic.detail is not None:
        if topic.detail.back_in_stock:
            signals.add("stok_geri_geldi")
        if topic.detail.discount_expired:
            signals.add("indirim_bitti")
        if topic.detail.prices:
            signals.add("fiyat_tespit_edildi")
        if topic.detail.coupon_codes:
            signals.add("kupon_tespit_edildi")
        normalized_stock_status = normalize_text(topic.detail.stock_status or "")
        if normalized_stock_status in {
            normalize_text("son stok"),
            normalize_text("1 adet"),
            normalize_text("2 adet"),
            normalize_text("sınırlı stok"),
        }:
            signals.add("düşük_stok")
    if _contains_any(text, ("ana konu",)):
        signals.add("ana_konu")
    if _contains_any(text, ("reklam",)):
        signals.add("reklam")
    return signals
