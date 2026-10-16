#!/usr/bin/env python3
"""
Safety Guard - PreToolUse hook for multi-project trading system.

Blocks catastrophic actions while allowing normal development.
Called with --scope global (universal rules) or --scope trading (project-specific rules).

Exit 0 = allow, Exit 2 = block.
Fail-open on any error.
"""

import json
import os
import re
import shlex
import sys

# ---------------------------------------------------------------------------
# Pre-compiled regex patterns (universal)
# ---------------------------------------------------------------------------
RE_FORCE_PUSH = re.compile(r"git\s+push\s.*(-f\b|--force\b)", re.IGNORECASE)
RE_BRANCH_DELETE_MAIN = re.compile(r"git\s+branch\s+-D\s+(main|master)\b", re.IGNORECASE)
RE_RM_RF_DANGEROUS = re.compile(r"rm\s+-[^\s]*r[^\s]*f|rm\s+-[^\s]*f[^\s]*r", re.IGNORECASE)
RE_RM_RF_ROOT_PATHS = re.compile(r"rm\s+.*(-rf|-fr)\s+(/|~|C:[/\\])", re.IGNORECASE)
RE_DROP_SQL = re.compile(r"\b(DROP\s+(TABLE|DATABASE))\b", re.IGNORECASE)
RE_TRUNCATE_SQL = re.compile(r"\bTRUNCATE\b", re.IGNORECASE)
RE_DELETE_NO_WHERE = re.compile(r"\bDELETE\s+FROM\s+\S+\s*(?!.*\bWHERE\b)", re.IGNORECASE)
RE_CHMOD_777 = re.compile(r"chmod\s+777\b", re.IGNORECASE)
RE_PIP_INSTALL = re.compile(r"\bpip\s+install\b", re.IGNORECASE)
RE_PIP_SAFE = re.compile(
    r"(--break-system-packages|\.venv|venv|uv\s+pip|pip\s+install\s+-e\s+\.)", re.IGNORECASE
)
RE_TASKKILL = re.compile(r"taskkill\s+/F\s+.*(python|node)", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Pre-compiled regex patterns (trading-specific)
# ---------------------------------------------------------------------------
RE_TRADIER_PROD = re.compile(r"api\.tradier\.com", re.IGNORECASE)
RE_COINBASE_KEY_LITERAL = re.compile(r"COINBASE_API_KEY\s*=\s*\S+", re.IGNORECASE)
RE_DOCKER_PROD = re.compile(r"docker.*compose.*prod", re.IGNORECASE)

# Guardian sensitive file patterns
RE_GUARDIAN_STATE = re.compile(
    r"guardian[/\\](.*_state\.json|.*_health\.json|trade_journal\.json)$",
    re.IGNORECASE,
)
RE_CREDENTIALS = re.compile(r"\.credentials\.json$", re.IGNORECASE)

# Project root directories for rm -rf protection
PROJECT_ROOTS = [
    "vectorbt-workspace",
    "guardian",
    "clri",
    "strat-stock-scanner",
    "atlas-strat-momentum",
    "atlas-strat-reversion",
    "atlas-audit",
    "atlas-story",
]

# Added 2026-10-16. Unlike PROJECT_ROOTS (matched anywhere in the command), these
# are matched only as the final path component of an rm -rf target, so cleaning a
# sibling such as hip3-scanner-wt/<name> stays possible. The session's own project
# folder (basename of CLAUDE_PROJECT_DIR) is added at runtime, which also covers a
# cloud clone named differently from the local folder (Tradingview-Backtesting).
PROTECTED_TARGET_NAMES = {
    "strat_trading_bot",
    "tradingview-backtesting",
    "hip3-scanner",
    "hip3-mobile",
    "hl_paper_trader",
    "market-data-core",
}
# rm -rf targets that mean "the current directory" or "everything in it".
CWD_TARGETS = {".", "..", "*", "./*", "../*", ".*"}
# Unexpanded variables that point at the project directory.
PROJECT_DIR_VARS = ("$claude_project_dir", "${claude_project_dir}", "$pwd", "${pwd}", "$(pwd)", "`pwd`")
SHELL_SEPARATORS = {";", "&&", "||", "|", "&", ";;"}


def block(reason: str) -> None:
    """Print block message and exit with code 2."""
    msg = {"decision": "block", "reason": reason}
    print(json.dumps(msg))
    print(f"SAFETY GUARD: {reason}", file=sys.stderr)
    sys.exit(2)


def normalize_path(path: str) -> str:
    """Normalize path separators to forward slashes, lowercase on Windows."""
    return path.replace("\\", "/").lower()


def is_env_file(basename: str) -> bool:
    """Check if a filename is a .env file (not .env.template or .env.example)."""
    if basename == ".env":
        return True
    if basename.startswith(".env.") and basename not in (
        ".env.template",
        ".env.example",
        ".env.test",
    ):
        return True
    return False


# ---------------------------------------------------------------------------
# Universal rule checks (--scope global)
# ---------------------------------------------------------------------------
def check_universal_file_write(file_path: str) -> None:
    """Check universal file write rules."""
    norm = normalize_path(file_path)
    basename = os.path.basename(norm)

    # Block .env file writes (except safe templates)
    if is_env_file(basename):
        block(f"Writing to environment file is not allowed: {basename}")


def rm_targets(command: str) -> list:
    """Return the non-flag arguments of every `rm` invocation in a shell command."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        tokens = command.split()
    targets = []
    i = 0
    while i < len(tokens):
        if os.path.basename(tokens[i]) == "rm":
            j = i + 1
            while j < len(tokens) and tokens[j] not in SHELL_SEPARATORS:
                if not tokens[j].startswith("-"):
                    targets.append(tokens[j])
                j += 1
            i = j
        else:
            i += 1
    return targets


def check_rm_project_targets(command: str) -> None:
    """Block rm -rf aimed at the current directory, everything in it, or a project folder."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "").replace("\\", "/").rstrip("/")
    names = set(PROTECTED_TARGET_NAMES)
    if project_dir:
        names.add(os.path.basename(project_dir).lower())
    for raw in rm_targets(command):
        target = raw.replace("\\", "/").lower()
        stripped = target.rstrip("/") or target
        if target in CWD_TARGETS or stripped in CWD_TARGETS:
            block(f"rm -rf targeting the current directory or everything in it: {raw}")
        if any(var in target for var in PROJECT_DIR_VARS):
            block(f"rm -rf targeting the project directory: {raw}")
        if os.path.basename(stripped) in names:
            block(f"rm -rf targeting project directory: {raw}")


def check_universal_bash(command: str) -> None:
    """Check universal bash command rules."""
    cmd_lower = command.lower()

    # rm -rf protection
    if RE_RM_RF_DANGEROUS.search(command):
        # Check if targeting dangerous paths
        if RE_RM_RF_ROOT_PATHS.search(command):
            block("rm -rf targeting root or home directory")
        for root in PROJECT_ROOTS:
            if root.lower() in cmd_lower:
                block(f"rm -rf targeting project directory: {root}")
        check_rm_project_targets(command)

    # Force push
    if RE_FORCE_PUSH.search(command):
        block("git push --force is not allowed")

    # Branch delete main/master
    if RE_BRANCH_DELETE_MAIN.search(command):
        block("Deleting main/master branch is not allowed")

    # Destructive SQL
    if RE_DROP_SQL.search(command):
        block("DROP TABLE/DATABASE requires human approval")
    if RE_TRUNCATE_SQL.search(command):
        block("TRUNCATE requires human approval")
    if RE_DELETE_NO_WHERE.search(command):
        block("DELETE FROM without WHERE clause requires human approval")

    # chmod 777
    if RE_CHMOD_777.search(command):
        block("chmod 777 is not allowed (use more restrictive permissions)")

    # Unsafe pip install
    if RE_PIP_INSTALL.search(command) and not RE_PIP_SAFE.search(command):
        block("pip install outside a venv. Use 'uv pip install' or activate a venv first.")

    # taskkill on python/node
    if RE_TASKKILL.search(command):
        block("taskkill /F targeting python/node requires human approval")


# ---------------------------------------------------------------------------
# Trading-specific rule checks (--scope trading)
# ---------------------------------------------------------------------------
def check_trading_file_write(file_path: str) -> None:
    """Check trading-specific file write rules."""
    norm = normalize_path(file_path)


    # Guardian state/health/journal files
    if RE_GUARDIAN_STATE.search(norm):
        block("Writing to guardian state/health/journal file requires human approval")

    # Credentials files
    if RE_CREDENTIALS.search(norm):
        block("Writing to credentials file is not allowed")


def check_trading_bash(command: str) -> None:
    """Check trading-specific bash command rules."""
    # Production Tradier API
    if RE_TRADIER_PROD.search(command):
        block("Production Tradier API (api.tradier.com) is blocked. Use sandbox.tradier.com.")

    # Coinbase API key literals in commands
    if RE_COINBASE_KEY_LITERAL.search(command):
        block("Coinbase API key literal in command is not allowed")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    # Parse scope argument
    scope = "global"
    if len(sys.argv) > 2 and sys.argv[1] == "--scope":
        scope = sys.argv[2]

    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # Fail open

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Select check functions based on scope
    if scope == "global":
        check_file, check_bash = check_universal_file_write, check_universal_bash
    elif scope == "trading":
        check_file, check_bash = check_trading_file_write, check_trading_bash
    else:
        sys.exit(0)

    # Dispatch by tool type
    if tool_name in ("Write", "Edit", "NotebookEdit"):
        file_path = tool_input.get("file_path", "")
        if file_path:
            check_file(file_path)
    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        if command:
            check_bash(command)

    # Allow by default
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        # Fail open on any unexpected error
        sys.exit(0)
