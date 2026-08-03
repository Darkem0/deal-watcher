from pathlib import Path

import pytest

from deal_watcher.sources.akakce_category import AkakceCategoryParser
from deal_watcher.sources.akakce_common import ParserChangedError, parse_price_kurus
from deal_watcher.sources.akakce_product import AkakceProductParser

FIXTURES = Path(__file__).parent / "fixtures"


def test_product_parser_extracts_multiple_sellers_and_shipping() -> None:
    html = (FIXTURES / "akakce_product.html").read_text(encoding="utf-8")
    offers = AkakceProductParser().parse(
        html, "https://www.akakce.com/akilli-saat/x,123.html", "watch"
    )
    assert len(offers) == 2
    assert offers[0].shipping_price == 0
    assert offers[0].total_price == offers[0].listed_price
    assert offers[1].shipping_price == 7_990
    assert offers[1].stock_status == "out_of_stock"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("31.999 TL", 3_199_900),
        ("31.999,90 TL", 3_199_990),
        ("31,9K", 3_190_000),
        ("31,9 bin TL", 3_190_000),
    ],
)
def test_turkish_akakce_price_formats(text: str, expected: int) -> None:
    assert parse_price_kurus(text) == expected


def test_specs_are_not_prices() -> None:
    assert parse_price_kurus("16 GB 2 TB 180 Hz 850W 41 mm 9700X 5070 Ti 4000 g") is None


def test_category_parser_applies_exact_filters_and_normalizes_models() -> None:
    html = (FIXTURES / "akakce_category.html").read_text(encoding="utf-8")
    items = AkakceCategoryParser().parse(
        html, "https://www.akakce.com/ekran-karti/rtx-5070-ti,1,2.html"
    )
    assert [item.source_product_id for item in items] == ["1001", "1004"]
    assert "gaming" not in items[0].normalized_model
    assert all(item.chipset == "RTX 5070 Ti" for item in items)


def test_changed_category_markup_is_controlled_error() -> None:
    with pytest.raises(ParserChangedError):
        AkakceCategoryParser().parse(
            "<html><body><p>challenge</p></body></html>", "https://example.test"
        )
