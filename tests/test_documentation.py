from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE_FILES = {
    ROOT / "ARCHITECTURE.md",
    ROOT / "docs" / "architecture" / "README.md",
    ROOT / "docs" / "architecture" / "STATE_AND_FAILURE.md",
    ROOT / "docs" / "architecture" / "INTERFACE_CONTRACTS.md",
    ROOT / "docs" / "architecture" / "THREAT_MODEL.md",
    ROOT / "docs" / "architecture" / "QUALITY_SCENARIOS.md",
    ROOT / "docs" / "architecture" / "DECISIONS.md",
}
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _markdown_files() -> list[Path]:
    ignored = {".git", ".venv", "data", "dist", "build"}
    return [
        path
        for path in ROOT.rglob("*.md")
        if not any(part in ignored for part in path.relative_to(ROOT).parts)
    ]


def test_architecture_documents_exist_and_are_linked() -> None:
    missing = sorted(
        str(path.relative_to(ROOT)) for path in ARCHITECTURE_FILES if not path.is_file()
    )
    assert missing == []

    root_architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "State ownership and consistency" in root_architecture
    assert "Implementation gates" in root_architecture
    assert "Current implementation vs target" in root_architecture


def test_relative_markdown_links_resolve() -> None:
    broken: list[str] = []
    for document in _markdown_files():
        content = document.read_text(encoding="utf-8")
        for raw_target in LINK_PATTERN.findall(content):
            target = raw_target.strip().strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith("#"):
                continue
            relative_path = unquote(parsed.path)
            if not relative_path:
                continue
            resolved = (document.parent / relative_path).resolve()
            if not resolved.exists():
                broken.append(f"{document.relative_to(ROOT)} -> {raw_target}")

    assert broken == [], "Broken relative Markdown links:\n" + "\n".join(broken)
