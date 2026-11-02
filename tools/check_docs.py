"""Check local Markdown links and heading fragments in project documentation."""

from __future__ import annotations

import os
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "node_modules",
}
EXCLUDED_ROOTS = {
    Path("data/raw"),
    Path("data/processed"),
    Path("reports"),
    Path("tmp"),
}
EXCLUDED_PREFIXES = ("pytest-",)
HEADING_PATTERN = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")
REFERENCE_DEFINITION_PATTERN = re.compile(
    r"^\s{0,3}\[([^\]]+)\]:\s*(<[^>]*>|\S+)(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*$"
)
REFERENCE_USAGE_PATTERN = re.compile(r"\[([^\]]+)\]\[([^\]]*)\]")


def markdown_files(root: Path) -> list[Path]:
    """Return project Markdown files, excluding generated and local-only trees."""
    result: list[Path] = []
    for current, directories, filenames in os.walk(root):
        current_path = Path(current)
        relative = current_path.relative_to(root)
        directories[:] = [
            name
            for name in directories
            if name not in EXCLUDED_NAMES
            and not name.startswith(EXCLUDED_PREFIXES)
            and (relative / name) not in EXCLUDED_ROOTS
        ]
        result.extend(current_path / filename for filename in filenames if filename.endswith(".md"))
    return sorted(result)


def _strip_fenced_code(text: str) -> str:
    """Blank fenced code blocks while preserving line breaks."""
    lines = text.splitlines(keepends=True)
    in_fence = False
    fence_character = ""
    fence_length = 0

    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if not in_fence:
            match = re.match(r"(`{3,}|~{3,})", stripped)
            if match is not None:
                in_fence = True
                fence_character = match.group(1)[0]
                fence_length = len(match.group(1))
                lines[index] = "\n" if line.endswith("\n") else ""
            continue

        match = re.match(r"(`{3,}|~{3,})\s*$", stripped)
        if (
            match is not None
            and match.group(1)[0] == fence_character
            and len(match.group(1)) >= fence_length
        ):
            in_fence = False
            fence_character = ""
            fence_length = 0
        lines[index] = "\n" if line.endswith("\n") else ""

    return "".join(lines)


def _strip_inline_code(text: str) -> str:
    """Blank inline code spans while preserving line breaks."""
    characters = list(text)
    index = 0
    length = len(text)

    while index < length:
        if text[index] != "`":
            index += 1
            continue

        run_length = 1
        while index + run_length < length and text[index + run_length] == "`":
            run_length += 1

        search = index + run_length
        closing_start = -1
        while search < length:
            if text[search] != "`":
                search += 1
                continue

            closing_length = 1
            while search + closing_length < length and text[search + closing_length] == "`":
                closing_length += 1
            if closing_length == run_length:
                closing_start = search
                break
            search += closing_length

        if closing_start == -1:
            index += run_length
            continue

        for position in range(index, closing_start + run_length):
            if characters[position] != "\n":
                characters[position] = " "
        index = closing_start + run_length

    return "".join(characters)


def _blank_line(line: str) -> str:
    """Replace a line with spaces while preserving its newline."""
    newline = "\n" if line.endswith("\n") else ""
    return " " * (len(line) - len(newline)) + newline


def _line_number(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def _parse_inline_destination(text: str, start: int) -> tuple[str, int] | None:
    """Parse the destination of an inline Markdown link starting after '('."""
    index = start
    length = len(text)

    while index < length and text[index].isspace():
        index += 1
    if index >= length:
        return None

    if text[index] == "<":
        closing = text.find(">", index + 1)
        if closing == -1:
            return None
        target = text[index + 1 : closing]
        index = closing + 1
    else:
        destination: list[str] = []
        depth = 0
        while index < length:
            character = text[index]
            if character == "\\" and index + 1 < length:
                destination.append(text[index + 1])
                index += 2
                continue
            if character == "(":
                depth += 1
                destination.append(character)
                index += 1
                continue
            if character == ")":
                if depth == 0:
                    break
                depth -= 1
                destination.append(character)
                index += 1
                continue
            if character.isspace() and depth == 0:
                break
            destination.append(character)
            index += 1
        target = "".join(destination)

    while index < length and text[index].isspace():
        index += 1

    if index < length and text[index] in {'"', "'", "("}:
        quote = text[index]
        closing_quote = ")" if quote == "(" else quote
        index += 1
        while index < length:
            if text[index] == "\\":
                index += 2
                continue
            if text[index] == closing_quote:
                index += 1
                break
            index += 1
        while index < length and text[index].isspace():
            index += 1

    if index < length and text[index] == ")":
        return target, index + 1
    return None


def _inline_links(text: str) -> Iterator[tuple[str, int]]:
    """Yield inline link targets and their line numbers."""
    index = 0
    length = len(text)

    while index < length:
        if text[index] == "\\":
            index += 2
            continue
        if text[index] != "[":
            index += 1
            continue

        closing_bracket = index + 1
        depth = 0
        while closing_bracket < length:
            if text[closing_bracket] == "\\":
                closing_bracket += 2
                continue
            if text[closing_bracket] == "[":
                depth += 1
            elif text[closing_bracket] == "]":
                if depth == 0:
                    break
                depth -= 1
            closing_bracket += 1
        if closing_bracket >= length:
            break

        if closing_bracket + 1 < length and text[closing_bracket + 1] == "(":
            parsed = _parse_inline_destination(text, closing_bracket + 2)
            if parsed is not None:
                target, end = parsed
                if target:
                    yield target, _line_number(text, index)
                index = end
                continue

        index = closing_bracket + 1


def _normalize_heading(heading: str) -> str:
    """Convert heading text to a GitHub-style slug base."""
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    heading = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    heading = re.sub(r"\[([^\]]*)\]\[[^\]]*\]", r"\1", heading)
    heading = heading.replace("`", "").strip().lower()

    slug: list[str] = []
    for character in heading:
        if character.isspace():
            slug.append("-")
        elif character.isalnum() or character in "-_":
            slug.append(character)
    return "".join(slug)


def heading_slugs(text: str) -> set[str]:
    """Return GitHub-style slugs for Markdown headings outside fenced code blocks."""
    slugs: set[str] = set()
    used: set[str] = set()
    body = _strip_fenced_code(text)

    for line in body.splitlines():
        match = HEADING_PATTERN.match(line)
        if match is None:
            continue

        base_slug = _normalize_heading(match.group(1))
        if not base_slug:
            continue

        slug = base_slug
        suffix = 1
        while slug in used:
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        used.add(slug)
        slugs.add(slug)

    return slugs


def _check_target(
    source: Path,
    root: Path,
    target: str,
    line_number: int,
    problems: list[str],
) -> bool:
    """Validate one local link target; return whether it was checked."""
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]

    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return False

    path_text = unquote(parsed.path)
    fragment = unquote(parsed.fragment).lower()

    destination = (source.parent / path_text).resolve() if path_text else source.resolve()

    if not destination.is_relative_to(root):
        problems.append(f"{source}:{line_number}: link escapes repository: {target}")
        return True
    if not destination.exists():
        problems.append(f"{source}:{line_number}: missing link target: {target}")
        return True
    if fragment and destination.is_file() and destination.suffix.lower() == ".md":
        destination_text = destination.read_text(encoding="utf-8")
        if fragment not in heading_slugs(destination_text):
            problems.append(f"{source}:{line_number}: missing heading fragment: {target}")
    return True


def check_links(source: Path, root: Path = ROOT) -> tuple[int, list[str]]:
    """Check local file targets and fragments in one Markdown file."""
    text = source.read_text(encoding="utf-8")
    body = _strip_inline_code(_strip_fenced_code(text))
    checked = 0
    problems: list[str] = []

    definitions: dict[str, tuple[str, int]] = {}
    lines = body.splitlines(keepends=True)
    for index, line in enumerate(lines):
        match = REFERENCE_DEFINITION_PATTERN.match(line)
        if match is None:
            continue
        label = match.group(1).strip().lower()
        target = match.group(2)
        definitions[label] = (target, index + 1)
        lines[index] = _blank_line(line)

    body_without_definitions = "".join(lines)

    for _label, (target, line_number) in definitions.items():
        if _check_target(source, root, target, line_number, problems):
            checked += 1

    for target, line_number in _inline_links(body_without_definitions):
        if _check_target(source, root, target, line_number, problems):
            checked += 1

    for match in REFERENCE_USAGE_PATTERN.finditer(body_without_definitions):
        label = (match.group(2) or match.group(1)).strip().lower()
        if label and label not in definitions:
            line_number = _line_number(body_without_definitions, match.start())
            problems.append(
                f"{source}:{line_number}: undefined reference link label: {match.group(0)}"
            )

    return checked, problems


def main() -> int:
    """Run the documentation link check and return a process status."""
    files = markdown_files(ROOT)
    checked_links = 0
    problems: list[str] = []

    for source in files:
        file_links, file_problems = check_links(source, ROOT)
        checked_links += file_links
        problems.extend(file_problems)

    if problems:
        print("Documentation link check failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1

    print(f"Checked {len(files)} Markdown files and {checked_links} local links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
