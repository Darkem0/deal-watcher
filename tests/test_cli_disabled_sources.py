from pathlib import Path

from deal_watcher.cli import main


def test_disabled_akakce_once_returns_readable_result_without_fetching(
    tmp_path: Path, capsys
) -> None:
    result = main(["once", "--source", "akakce", "--database", str(tmp_path / "test.sqlite3")])

    captured = capsys.readouterr()
    assert result == 0
    assert "source disabled: akakce" in captured.out
    assert captured.err == ""
