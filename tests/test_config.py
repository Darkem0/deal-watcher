from pathlib import Path

import pytest
import yaml

from deal_watcher.models.config import ConfigLoadError, ProductsConfig, _load_yaml

ROOT = Path(__file__).resolve().parents[1]


def test_five_real_akakce_urls_and_source_types(app_config) -> None:
    products = app_config.products.products
    assert len(products) == 5
    assert all(str(product.url).startswith("https://www.akakce.com/") for product in products)
    assert sum(product.source_type == "product_page" for product in products) == 4
    assert sum(product.source_type == "category_page" for product in products) == 1


def test_akakce_is_disabled_and_experimental_by_default(app_config) -> None:
    assert app_config.settings.akakce.enabled is False
    assert app_config.settings.akakce.status == "experimental"


def test_null_target_prices_are_supported(app_config) -> None:
    assert all(product.target_price_try is None for product in app_config.products.products)
    assert app_config.products.defaults.target_price_try is None


def test_invalid_source_type_has_readable_error(tmp_path: Path) -> None:
    data = yaml.safe_load((ROOT / "config" / "products.yaml").read_text(encoding="utf-8"))
    data["products"][0]["source_type"] = "search_page"
    path = tmp_path / "products.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ConfigLoadError, match="source_type"):
        _load_yaml(path, ProductsConfig)


def test_duplicate_product_id_is_rejected() -> None:
    data = yaml.safe_load((ROOT / "config" / "products.yaml").read_text(encoding="utf-8"))
    data["products"][1]["id"] = data["products"][0]["id"]
    with pytest.raises(ValueError, match="duplicate product"):
        ProductsConfig.model_validate(data)
