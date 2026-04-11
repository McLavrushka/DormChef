#!/usr/bin/env python3
"""Fail if any function/method exceeds a numeric cyclomatic complexity limit.

Uses radon's visitor (same family of metrics as ``radon cc``). Default max is
**9**, i.e. enforce **strictly below 10**.

Run:

    poetry run python scripts/check_max_cc.py
    poetry run python scripts/check_max_cc.py --max 9 backend frontend

"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

try:
    from radon.complexity import cc_visit
except ModuleNotFoundError:
    print(
        "Error: radon is not available in this Python environment.\n"
        "Install dev dependencies and run:\n"
        "  poetry install\n"
        "  poetry run python scripts/check_max_cc.py",
        file=sys.stderr,
    )
    raise SystemExit(1) from None

DEFAULT_MAX_COMPLEXITY = 9
DEFAULT_ROOTS = ("backend", "frontend")

_SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "node_modules",
    },
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _iter_py_files(roots: list[str]) -> list[Path]:
    base = _repo_root()
    out: list[Path] = []
    for root in roots:
        path = base / root
        if not path.is_dir():
            continue
        for f in path.rglob("*.py"):
            if _SKIP_DIR_NAMES.intersection(f.parts):
                continue
            out.append(f)
    return sorted(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--max",
        type=int,
        default=DEFAULT_MAX_COMPLEXITY,
        metavar="N",
        help=(
            f"Maximum allowed complexity per block (default: "
            f"{DEFAULT_MAX_COMPLEXITY})"
        ),
    )
    parser.add_argument(
        "roots",
        nargs="*",
        default=list(DEFAULT_ROOTS),
        help="Directories to scan (paths relative to repo root).",
    )
    args = parser.parse_args()
    max_cc = args.max

    violations: list[tuple[Path, int, str, int]] = []
    for py_path in _iter_py_files(args.roots):
        try:
            source = py_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_path))
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            print(f"ERROR: {py_path}: {exc}", file=sys.stderr)
            return 1

        for block in cc_visit(tree):
            if block.complexity > max_cc:
                rel = py_path.relative_to(_repo_root())
                violations.append(
                    (rel, block.lineno, block.name, block.complexity),
                )

    if violations:
        print(
            f"FAIL: cyclomatic complexity > {max_cc} for "
            f"{len(violations)} block(s):",
            file=sys.stderr,
        )
        for rel, lineno, name, cc in sorted(violations):
            print(f"  {rel}:{lineno}  {name!r}  (CC={cc})", file=sys.stderr)
        return 1

    roots_display = ", ".join(args.roots)
    print(
        f"OK: cyclomatic complexity ≤ {max_cc} for all blocks "
        f"under [{roots_display}]",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
