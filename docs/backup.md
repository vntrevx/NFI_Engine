# Backup And Restore

Backups capture local config, database metadata, and diagnostic context needed
for dry-run recovery. They are intentionally conservative.

## Create And Verify

```bash
uv run nfi-engine backup create --config examples/futures-paper.yaml --output .omo/evidence/backup.zip
uv run nfi-engine backup verify .omo/evidence/backup.zip
```

Verification checks the archive manifest and member hashes.

## Restore Dry Run

```bash
uv run nfi-engine backup restore --dry-run .omo/evidence/backup.zip
```

Use dry-run first. Mutating restore paths require explicit backup validity and
must not run from the read-only UI mode.

## Support Bundle

The `/logs` page exports a support report zip. It contains redacted config and
recent logs only. API tokens and exchange credentials are rendered as `REDACTED`.

## Limitations

M1 restore is a guarded maintenance workflow. It is not a one-click production
disaster recovery system.
