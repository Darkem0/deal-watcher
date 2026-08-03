from pathlib import Path

from deal_watcher import cli

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def run_forum_once(database: Path, fixture_name: str) -> int:
    return cli.main(
        [
            "once",
            "--source",
            "forum",
            "--dry-run",
            "--forum-fixture",
            str(FIXTURES / fixture_name),
            "--database",
            str(database),
        ]
    )


def test_forum_once_prints_baseline_summary_and_updates_database(tmp_path, capsys) -> None:
    result = run_forum_once(tmp_path / "forum.sqlite3", "forum_baseline.html")

    output = capsys.readouterr().out
    assert result == 0
    assert "Forum taraması tamamlandı." in output
    assert "Çekilen konu: 3" in output
    assert "Baseline konu: 3" in output
    assert "Üretilen bildirim: 0" in output
    assert "Gönderilen bildirim: 0" in output
    assert "Veritabanı güncellendi: evet" in output
    assert "Dry-run: evet" in output
    assert "Sonuç: success" in output


def test_forum_once_reports_new_topics_and_deduplicates_second_scan(tmp_path, capsys) -> None:
    database = tmp_path / "forum.sqlite3"
    assert run_forum_once(database, "forum_baseline.html") == 0
    capsys.readouterr()

    assert run_forum_once(database, "forum_update.html") == 0
    update_output = capsys.readouterr().out
    assert "Yeni konu: 2" in update_output
    assert "Üretilen bildirim: 2" in update_output

    assert run_forum_once(database, "forum_update.html") == 0
    duplicate_output = capsys.readouterr().out
    assert "Üretilen bildirim: 0" in duplicate_output
    assert "Gönderilen bildirim: 0" in duplicate_output
