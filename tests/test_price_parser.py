from deal_watcher.sources.forum import extract_price_kurus


def test_turkish_price_formats() -> None:
    assert extract_price_kurus("Fiyat 34.999 TL") == [3_499_900]
    assert extract_price_kurus("Sepette 1.249,90 ₺") == [124_990]
    assert extract_price_kurus("₺ 799,50 yerine 699 TRY") == [79_950, 69_900]


def test_hardware_specs_are_not_prices() -> None:
    assert extract_price_kurus("16 GB RAM, 2 TB SSD, 850W PSU, 180 Hz monitör") == []
