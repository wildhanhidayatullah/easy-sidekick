"""Tests for the Markdown documentation link checker."""

from pathlib import Path

from tools import check_docs


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_heading_slugs_follow_github_style() -> None:
    text = "\n".join(
        [
            "# Phase 0 — Foundation and decisions",
            "## Pasal dan Ayat",
            "## foo_bar",
            "## Use `check_docs`",
            "## Duplicate",
            "## Duplicate",
            "## Duplicate-1",
            "```",
            "# Ignored heading",
            "```",
        ]
    )

    slugs = check_docs.heading_slugs(text)

    assert "phase-0--foundation-and-decisions" in slugs
    assert "pasal-dan-ayat" in slugs
    assert "foo_bar" in slugs
    assert "use-check_docs" in slugs
    assert {"duplicate", "duplicate-1", "duplicate-1-1"}.issubset(slugs)
    assert "ignored-heading" not in slugs


def test_check_links_accepts_valid_targets(tmp_path: Path) -> None:
    root = tmp_path
    _write(root / "docs" / "target.md", "# Target Section\n")
    source = _write(
        root / "docs" / "source.md",
        "[target](target.md#target-section)\n[external](https://example.com)\n",
    )

    checked, problems = check_docs.check_links(source, root)

    assert checked == 1
    assert problems == []


def test_check_links_reports_missing_target_and_fragment(tmp_path: Path) -> None:
    root = tmp_path
    _write(root / "docs" / "target.md", "# Target Section\n")
    source = _write(
        root / "docs" / "source.md",
        "[missing](missing.md)\n[fragment](target.md#missing)\n",
    )

    _checked, problems = check_docs.check_links(source, root)

    assert any("missing link target: missing.md" in problem for problem in problems)
    assert any("missing heading fragment: target.md#missing" in problem for problem in problems)


def test_check_links_rejects_paths_outside_repository(tmp_path: Path) -> None:
    root = tmp_path
    source = _write(root / "docs" / "source.md", "[escape](../../outside.md)\n")

    _checked, problems = check_docs.check_links(source, root)

    assert any("link escapes repository" in problem for problem in problems)


def test_check_links_ignores_code_blocks_and_inline_code(tmp_path: Path) -> None:
    root = tmp_path
    _write(root / "docs" / "target.md", "# Target\n")
    source = _write(
        root / "docs" / "source.md",
        "\n".join(
            [
                "```",
                "[missing](missing.md)",
                "```",
                "Use `[missing](missing.md)` in code.",
                "[target](target.md)",
                "",
            ]
        ),
    )

    checked, problems = check_docs.check_links(source, root)

    assert checked == 1
    assert problems == []


def test_check_links_supports_titles_and_nested_parentheses(tmp_path: Path) -> None:
    root = tmp_path
    _write(root / "docs" / "target.md", "# Target\n")
    _write(root / "docs" / "target (1).md", "# Target One\n")
    source = _write(
        root / "docs" / "source.md",
        "\n".join(
            [
                '[target](target.md "A title")',
                "[nested](target%20(1).md)",
                "[angle](<target (1).md>)",
                "",
            ]
        ),
    )

    checked, problems = check_docs.check_links(source, root)

    assert checked == 3
    assert problems == []


def test_check_links_supports_reference_links(tmp_path: Path) -> None:
    root = tmp_path
    _write(root / "docs" / "target.md", "# Target Section\n")
    source = _write(
        root / "docs" / "source.md",
        "\n".join(
            [
                "[target][ref]",
                '[ref]: target.md#target-section "Title"',
                "",
            ]
        ),
    )

    checked, problems = check_docs.check_links(source, root)

    assert checked == 1
    assert problems == []


def test_check_links_reports_undefined_reference_labels(tmp_path: Path) -> None:
    root = tmp_path
    source = _write(root / "docs" / "source.md", "[target][missing]\n")

    _checked, problems = check_docs.check_links(source, root)

    assert any("undefined reference link label" in problem for problem in problems)


def test_docs_reports_is_not_excluded(tmp_path: Path) -> None:
    root = tmp_path
    _write(root / "docs" / "reports" / "report.md", "# Report\n")
    _write(root / "reports" / "generated.md", "# Generated\n")

    files = check_docs.markdown_files(root)

    assert root / "docs" / "reports" / "report.md" in files
    assert root / "reports" / "generated.md" not in files


def test_pytest_temp_directories_are_excluded(tmp_path: Path) -> None:
    root = tmp_path
    _write(root / "pytest-of-user" / "pytest-0" / "source.md", "# Temporary\n")
    _write(root / "docs" / "source.md", "# Source\n")

    files = check_docs.markdown_files(root)

    assert root / "docs" / "source.md" in files
    assert root / "pytest-of-user" / "pytest-0" / "source.md" not in files
