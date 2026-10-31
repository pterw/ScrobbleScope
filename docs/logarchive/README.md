# Log Archive Index

Canonical untagged execution-log archive:
- `PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` -- an index since 2026-10-31. Its
  entries are on the numbered pages in `pages/`, which it lists oldest first.

Related archives:
- Per-batch logs remain in `docs/history/logs/BATCHN_LOG.md`
- Batch definitions remain in `docs/history/definitions/BATCHN_DEFINITION.md`
- Any of these archives that outgrows 500 lines is paginated the same way:
  the file stays as the index and its pages sit in `pages/` beside it.

Quick lookup examples (search the directory, not the index file):
- `rg -n "^### 20" docs/logarchive/`
- `rg -n "Batch 14" docs/history/logs/`
