#!/usr/bin/env python3
"""
Post-Edit Lint - PostToolUse hook.

Runs ruff check --fix + ruff format on modified Python files.
Always exits 0 (informational only, never blocks).
Suppresses all error output from missing tools.
"""

import json
import os
import subprocess
import sys


def find_ruff(file_path: str) -> str:
    """Find ruff executable: project venv first, then global PATH."""
    # Walk up from file to find project venv
    directory = os.path.dirname(os.path.abspath(file_path))
    for _ in range(20):  # Max depth
        # Windows venv path
        candidate = os.path.join(directory, ".venv", "Scripts", "ruff.exe")
        if os.path.isfile(candidate):
            return candidate
        # Unix venv path (Git Bash compatibility)
        candidate = os.path.join(directory, ".venv", "bin", "ruff")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(directory)
        if parent == directory:
            break
        directory = parent

    # Fall back to global PATH (suppress errors)
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            return "ruff"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    return ""


def main() -> None:
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only process Python files
    if not file_path or not file_path.endswith(".py"):
        sys.exit(0)

    # Skip virtual env and cache directories
    norm_path = file_path.replace("\\", "/").lower()
    skip_dirs = [".venv/", "__pycache__/", "node_modules/", ".git/"]
    if any(d in norm_path for d in skip_dirs):
        sys.exit(0)

    # Find ruff
    ruff_cmd = find_ruff(file_path)
    if not ruff_cmd:
        sys.exit(0)  # No ruff available, silently skip

    # Run ruff check --fix (auto-fixable issues only)
    try:
        subprocess.run(
            [ruff_cmd, "check", "--fix", "--quiet", file_path],
            capture_output=True,
            timeout=15,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass

    # Run ruff format
    try:
        subprocess.run(
            [ruff_cmd, "format", "--quiet", file_path],
            capture_output=True,
            timeout=15,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
