from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from nfi_engine.maintenance import create_backup


def _config_with_database_url(tmp_path: Path, database_url: str) -> Path:
    config = tmp_path / "database-url.yaml"
    config.write_text(
        Path("examples/futures-paper.yaml")
        .read_text(encoding="utf-8")
        .replace("sqlite+aiosqlite:///data/nfi_engine.sqlite3", database_url),
        encoding="utf-8",
    )
    return config


def _database_info(archive_path: Path) -> str:
    with ZipFile(archive_path) as archive:
        return archive.read("database.json").decode("utf-8")


def test_backup_create_redacts_credential_database_url(tmp_path: Path) -> None:
    # Given: a config with a credential-bearing non-SQLite database URL.
    output = tmp_path / "backup.zip"
    config = _config_with_database_url(
        tmp_path,
        "postgresql+asyncpg://backup-user:backup-pass@example.com/engine?ssl=prefer",
    )

    # When: a backup archive is created.
    result = create_backup(config=config, output=output)

    # Then: database metadata preserves shape without leaking raw DSN credentials.
    database_info = _database_info(output)
    assert result.redacted is True
    assert "backup-user" not in database_info
    assert "backup-pass" not in database_info
    assert "ssl=prefer" not in database_info
    assert "postgresql+asyncpg://REDACTED@example.com/engine?REDACTED" in database_info


def test_backup_create_redacts_socket_database_url_query_credentials(tmp_path: Path) -> None:
    # Given: a non-SQLite socket-style DSN with credentials in query parameters.
    output = tmp_path / "backup.zip"
    config = _config_with_database_url(
        tmp_path,
        (
            "postgresql+asyncpg:///engine?"
            "host=/var/run/postgresql&user=socket-user&password=socket-pass"
        ),
    )

    # When: a backup archive is created.
    create_backup(config=config, output=output)

    # Then: socket path shape is retained without leaking query credentials.
    database_info = _database_info(output)
    assert "socket-user" not in database_info
    assert "socket-pass" not in database_info
    assert "/var/run/postgresql" not in database_info
    assert "postgresql+asyncpg:///engine?REDACTED" in database_info
