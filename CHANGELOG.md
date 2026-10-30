# Changelog

## 0.2.0 - 2026-10-30

- Enforce minimum storage admission and reject backups that exceed pledged capacity.
- Add signed drain receipts that distinguish hardened, degraded and local-only persistence.
- Checkpoint SQLite WAL before reporting a drain result.
- Add manual virtual-role export/import with password-derived encryption and re-encryption at the target node.
- Add `/readyz`, status/drain CLI commands and automatic best-effort drain on graceful process shutdown.
- Add tests for admission, local-only shutdown and cross-node role migration.
- Add two-node process integration test to CI.
- Add search-focused project metadata, citation file, public roadmap, contributor guide and GitHub Pages landing site.
- Add governance, code of conduct, pull-request template, contributor task board, reproducible demo and outreach kit.
- Add a contributor entry page, research/deployment issue forms, recognition policy and contribution-time paths from a 10-minute demo to sustained research collaboration.

## 0.1.0 - 2026-10-30

- Initial invite-only HTTP mesh MVP.
- Signed node capabilities, encrypted memory, blind indexing, remote ciphertext backup and cold recall.
- OpenAI-compatible chat endpoint and spatial-session mock interface.

