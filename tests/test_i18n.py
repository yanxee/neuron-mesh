from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAIRED_MARKDOWN = [
    ("README.md", "README.zh-CN.md"),
    ("ARCHITECTURE.md", "ARCHITECTURE.zh-CN.md"),
    ("CHANGELOG.md", "CHANGELOG.zh-CN.md"),
    ("CODE_OF_CONDUCT.md", "CODE_OF_CONDUCT.zh-CN.md"),
    ("CONTRIBUTING.md", "CONTRIBUTING.zh-CN.md"),
    ("CONTRIBUTORS.md", "CONTRIBUTORS.zh-CN.md"),
    ("GOVERNANCE.md", "GOVERNANCE.zh-CN.md"),
    ("ROADMAP.md", "ROADMAP.zh-CN.md"),
    ("SECURITY.md", "SECURITY.zh-CN.md"),
    ("docs/CONTRIBUTOR_TASKS.md", "docs/CONTRIBUTOR_TASKS.zh-CN.md"),
    ("docs/DEMO.md", "docs/DEMO.zh-CN.md"),
    ("docs/I18N.md", "docs/I18N.zh-CN.md"),
    ("docs/JOIN.md", "docs/JOIN.zh-CN.md"),
    ("docs/OUTREACH.md", "docs/OUTREACH.zh-CN.md"),
    ("docs/TASK_ORCHESTRATION.md", "docs/TASK_ORCHESTRATION.zh-CN.md"),
    ("docs/research/README.md", "docs/research/README.zh-CN.md"),
    ("docs/architecture/DECISIONS.md", "docs/architecture/DECISIONS.zh-CN.md"),
    (
        "docs/architecture/INTERFACE_CONTRACTS.md",
        "docs/architecture/INTERFACE_CONTRACTS.zh-CN.md",
    ),
    (
        "docs/architecture/QUALITY_SCENARIOS.md",
        "docs/architecture/QUALITY_SCENARIOS.zh-CN.md",
    ),
    ("docs/architecture/README.md", "docs/architecture/README.zh-CN.md"),
    (
        "docs/architecture/STATE_AND_FAILURE.md",
        "docs/architecture/STATE_AND_FAILURE.zh-CN.md",
    ),
    ("docs/architecture/THREAT_MODEL.md", "docs/architecture/THREAT_MODEL.zh-CN.md"),
]

RESEARCH_PAIRS = [
    (
        "神经元式去中心化大模型网络系统-研究型邀请制可执行方案.md",
        "docs/research/invite-only-executable-plan.en.md",
    ),
    (
        "神经元式去中心化大模型网络系统-持续学习与持久记忆方案.md",
        "docs/research/continual-learning-persistent-memory.en.md",
    ),
    (
        "神经元式去中心化大模型网络系统-元宇宙接入预留方案.md",
        "docs/research/metaverse-integration.en.md",
    ),
    (
        "神经元式去中心化大模型网络系统-技术交底书.md",
        "docs/research/technical-disclosure.en.md",
    ),
]

HTML_PAIRS = [
    ("docs/index.html", "docs/zh-CN/index.html"),
    ("docs/join.html", "docs/zh-CN/join.html"),
]
LEGAL_PAIRS = [("LICENSE", "LICENSE.zh-CN.md")]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_required_language_pairs_exist_and_link_to_each_other() -> None:
    missing: list[str] = []
    for english, chinese in PAIRED_MARKDOWN:
        english_path = ROOT / english
        chinese_path = ROOT / chinese
        if not english_path.is_file() or not chinese_path.is_file():
            missing.append(f"{english} <-> {chinese}")
            continue
        english_text = _read(english)
        chinese_text = _read(chinese)
        if Path(english).name not in chinese_text[:1200]:
            missing.append(f"{chinese} has no English language switch")
        if Path(chinese).name not in english_text[:1200]:
            missing.append(f"{english} has no Chinese language switch")

    assert missing == [], "Missing or unlinked translation pairs:\n" + "\n".join(missing)


def test_every_public_markdown_file_has_a_language_partner() -> None:
    expected = {
        ROOT / path
        for pair in (*PAIRED_MARKDOWN, *RESEARCH_PAIRS)
        for path in pair
    }
    expected.add(ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md")
    expected = {path for path in expected if path.suffix == ".md"}
    expected.update(ROOT / path for pair in LEGAL_PAIRS for path in pair if path.endswith(".md"))
    actual = {
        path
        for path in ROOT.rglob("*.md")
        if not any(
            part in {".git", ".venv", ".pytest_cache", "data", "dist", "build"}
            for part in path.parts
        )
    }
    assert actual == expected, (
        "Unpaired Markdown files:\n"
        + "\n".join(str(path.relative_to(ROOT)) for path in sorted(actual - expected))
    )


def test_research_editions_are_available_in_both_languages() -> None:
    missing: list[str] = []
    for chinese, english in RESEARCH_PAIRS:
        chinese_path = ROOT / chinese
        english_path = ROOT / english
        if not chinese_path.is_file() or not english_path.is_file():
            missing.append(f"{chinese} <-> {english}")
            continue
        if Path(english).name not in _read(chinese)[:1200]:
            missing.append(f"{chinese} does not link to {english}")
        if Path(chinese).name not in _read(english)[:1200]:
            missing.append(f"{english} does not link to {chinese}")
    assert missing == [], "Research language links are incomplete:\n" + "\n".join(missing)


def test_github_forms_are_bilingual() -> None:
    forms = [
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/ISSUE_TEMPLATE/research_proposal.yml",
        ".github/ISSUE_TEMPLATE/deployment_report.yml",
    ]
    cjk = re.compile(r"[\u3400-\u9fff]")
    incomplete = [path for path in forms if not cjk.search(_read(path))]
    assert incomplete == [], f"GitHub forms without Chinese text: {incomplete}"


def test_public_website_has_language_variants() -> None:
    missing: list[str] = []
    for english, chinese in HTML_PAIRS:
        english_text = _read(english)
        chinese_text = _read(chinese)
        if 'hreflang="zh-CN"' not in english_text:
            missing.append(f"{english} lacks zh-CN hreflang")
        if 'lang="zh-CN"' not in chinese_text:
            missing.append(f"{chinese} lacks zh-CN document language")
        if 'hreflang="en"' not in chinese_text:
            missing.append(f"{chinese} lacks en hreflang")
    assert missing == [], "\n".join(missing)


def test_legal_license_pair_exists() -> None:
    assert all((ROOT / path).is_file() for pair in LEGAL_PAIRS for path in pair)
