## What changed

Describe the user-visible or protocol-level change.

## Why

Explain the problem, evidence and tradeoffs.

## Verification

- [ ] `ruff check .`
- [ ] `pytest`
- [ ] `python scripts/e2e_check.py` when routing, memory or lifecycle behavior changes
- [ ] Added or updated tests
- [ ] Updated documentation or explicitly marked it unnecessary

## Safety and compatibility

- [ ] No credentials, private memory, model weights or user data are included
- [ ] API/version behavior is backward compatible or migration is documented
- [ ] Performance/research claims include hardware, versions and failure boundaries

Closes #

