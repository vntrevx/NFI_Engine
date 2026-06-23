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
The CLI currently refuses `--apply` with `BACKUP_RESTORE_APPLY_UNSUPPORTED`
until the later apply/rollback slice exists.
Backup verification also fails closed when archive members fall outside the
engine-owned backup manifest allowlist.
Verification requires the non-optional backup members and rejects incomplete
manifest-only archives before they can be used for restore rehearsal.
Restore dry-run refuses checksum-invalid archives before printing restore steps.
Backup metadata redacts credential-bearing database URLs before writing
`database.json`.

## Safety Rehearsal

The S8 WP8.1 rehearsal exercises the real CLI and shell surfaces in one flow:
backup create, backup verify, restore `--dry-run`, safe uninstall `--dry-run`,
and purge uninstall `--dry-run` against a marker-protected runtime directory.
The rehearsal must keep the runtime marker, token file, and operator files
present after both uninstall dry-runs. Unsafe purge targets must fail with a
stable machine-readable code before any removal scope is printed.

## Support Bundle

The `/logs` page exports a support report zip. It contains redacted config and
recent logs only. API tokens and exchange credentials are rendered as `REDACTED`.

## Limitations

Restore remains a guarded preview-first maintenance workflow. It is not a
one-click production disaster recovery system until a later apply/rollback
slice proves mutation, restart/reload, and rollback evidence.
