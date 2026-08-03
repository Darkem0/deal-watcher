from deal_watcher.models.domain import ForumTopic, NotificationPriority
from deal_watcher.services.classification import classify_topic, normalize_text, topic_signals


def _topic(title: str, *, prefix_labels: tuple[str, ...] = ()) -> ForumTopic:
    return ForumTopic(
        topic_id="test-topic",
        canonical_topic_url="https://example.invalid/test-topic",
        title=title,
        prefix_labels=prefix_labels,
    )


def test_turkish_diacritics_and_ascii_forms_classify_equally(app_config) -> None:
    accented = classify_topic(_topic("Sınırlı stok Ryzen işlemci fırsatı"), app_config.forum)
    ascii_only = classify_topic(_topic("Sinirli stok Ryzen islemci firsati"), app_config.forum)

    assert accented.category == ascii_only.category == "cpu"
    assert accented.priority == ascii_only.priority == NotificationPriority.URGENT


def test_configured_low_stock_code_matches_real_title_phrase(app_config) -> None:
    result = classify_topic(_topic("Kampanya: yalnızca 1 adet kaldı"), app_config.forum)

    assert result.category == "other"
    assert result.priority == NotificationPriority.URGENT


def test_topic_signals_survive_turkish_text_folding() -> None:
    signals = topic_signals(_topic("Sınırlı stok, ürün tekrar stokta"))

    assert "stok_geri_geldi" in signals


def test_discount_expired_signal_is_detected_case_insensitively() -> None:
    signals = topic_signals(_topic("İNDİRİM BİTTİ - fiyat güncellendi"))

    assert "indirim_bitti" in signals


def test_gpu_accessory_is_not_classified_as_graphics_card(app_config) -> None:
    result = classify_topic(_topic("RTX ekran kartı standı indirimi"), app_config.forum)

    assert result.category != "gpu"


def test_normalize_text_folds_turkish_characters() -> None:
    assert normalize_text("ÇĞIİÖŞÜ  Fırsat") == "cgiiosu firsat"
