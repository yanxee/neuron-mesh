# Contributing to NeuronMesh

NeuronMesh is an early research project. Small, testable and clearly documented contributions are welcome.

## Development setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
ruff check .
pytest
python scripts/e2e_check.py
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\e2e_check.py
```

## Pull requests

- Keep the OpenAI-compatible and internal APIs backward compatible unless the change is explicitly versioned.
- Add tests for routing, memory durability, permissions and failure recovery.
- Do not put raw credentials, user memory or model weights in the repository.
- Preserve the distinction between implemented capabilities and roadmap items.
- Include performance numbers with hardware, model, prompt/output lengths and network conditions.

## Research claims

Claims about memory persistence, fault recovery, decentralization or model quality must include a reproducible test and a clearly stated failure boundary.

