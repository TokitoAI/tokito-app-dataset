# Offline board-dataset bundle

This checkout is an offline bundle when every asset listed in
`docs/samples/ultimainboard-2.1.4/offline-manifest.json` is materialized and
hashes to its SHA-256 record.  The manifest intentionally excludes itself to
avoid a self-referential hash.

Verify it from the bundle root:

```powershell
python scripts/verify_offline_manifest.py
```

The verification does not require network access or Git LFS.  It checks the
full file bytes, including originally Git-LFS-managed CAD, model, and photo
assets.  `fully_materialized` must be `true`; a `git_lfs_pointer_not_materialized`
record means the bundle is incomplete.

For the identified physical board, start at
`docs/samples/ultimainboard-2.1.4/README.md`.  `docs/ALL_BOARD_INDEX.json`
lists the available material for every dataset board and records missing
evidence separately.
