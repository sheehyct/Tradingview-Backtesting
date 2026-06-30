#!/usr/bin/env python3
"""Pre-push / session-end secret-scan gate.

Scans the files that would actually be pushed (git-tracked content) for
high-confidence secret material before an automated push reaches the remote.
This is the safety net that makes unattended auto-push (the EQUITY-182
remote-review workflow) acceptable: it is deterministic, high-precision, and
exits non-zero on any CRITICAL/HIGH finding so a CI step, git pre-push hook, or
the /session-end command can block the push.

Scope notes
-----------
- Only SCANS git-tracked files (``git ls-files``) by default, because those are
  exactly what a push sends. Gitignored material (real ``.env``, the
  force-ignored ``guardian/`` docs, scratch ``Temporary/``) is never scanned
  because it is never pushed.
- Detects SECRETS / KEYS / TOKENS / public IPs / wallet addresses / the owner's
  personal email. It does NOT attempt to detect free-text PII (health terms,
  account P&L narratives) -- that class is handled by .gitignore + the human
  audit, not a regex, because regexing prose is fragile and noisy.
- Placeholder-aware: ``sk-ant-xxxxxxxx`` style template values pass.
- IP-aware: uses ``ipaddress.is_global`` so localhost / RFC1918 / RFC5737
  documentation ranges pass and only a genuine public IP (e.g. a live VPS) trips
  the gate.

Usage
-----
    uv run python scripts/secret_scan.py            # scan all tracked files
    uv run python scripts/secret_scan.py --staged   # scan only staged changes
    uv run python scripts/secret_scan.py --paths a.md b.py   # scan given files
    uv run python scripts/secret_scan.py --strict   # also fail on LOW findings

Allowlist
---------
``scripts/secret_scan_allowlist.txt`` (optional) holds one entry per line:
- a regex -> any matched secret text matching it is downgraded to ALLOWED.
- ``path:<glob>`` -> files matching the glob are skipped entirely.
Lines starting with ``#`` are comments.

Exit codes: 0 = clean (or only LOW without --strict); 2 = blocking finding(s).
"""

from __future__ import annotations

import argparse
import fnmatch
import ipaddress
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files that legitimately contain secret-shaped patterns (this scanner and its
# allowlist) -- skip to avoid self-flagging.
SELF_SKIP = {
    "scripts/secret_scan.py",
    "scripts/secret_scan_allowlist.txt",
}

# Binary / non-text extensions we never scan as text.
BINARY_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".ico",
    ".pdf",
    ".gz",
    ".zip",
    ".parquet",
    ".db",
    ".sqlite",
    ".pkl",
    ".joblib",
    ".h5",
    ".hdf5",
    ".npy",
    ".npz",
    ".mp3",
    ".wav",
    ".m4a",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".so",
    ".pyd",
    ".dll",
    ".exe",
    ".bin",
    ".jar",
    ".class",
}

MAX_BYTES = 2_000_000  # skip files larger than this (data blobs, not source)

# (name, compiled regex, severity). CRITICAL/HIGH block the push; LOW warns.
PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"), "CRITICAL"),
    ("openai_key", re.compile(r"sk-(?:proj-|live-|svcacct-)?[A-Za-z0-9]{20,}"), "CRITICAL"),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "CRITICAL"),
    (
        "aws_secret",
        re.compile(r"aws_secret_access_key\s*[=:]\s*['\"]?[A-Za-z0-9/+]{40}"),
        "CRITICAL",
    ),
    (
        "private_key_block",
        # Require a real base64 key body after the header, so format-string
        # markers like f"-----BEGIN EC PRIVATE KEY-----\n{key}" do not match.
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[ \t]*[\r\n]+[A-Za-z0-9+/=\r\n]{60,}"),
        "CRITICAL",
    ),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"), "HIGH"),
    ("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b"), "CRITICAL"),
    ("github_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"), "CRITICAL"),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "CRITICAL"),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"), "CRITICAL"),
    (
        "discord_webhook",
        re.compile(
            # Require a realistic 17-20 digit id and a >=50 char token so short
            # test-fixture webhooks (.../webhooks/123/abc) do not match.
            r"https://(?:canary\.|ptb\.)?discord(?:app)?\.com/api/webhooks/\d{17,20}/[A-Za-z0-9_\-]{50,}"
        ),
        "CRITICAL",
    ),
    ("alpaca_live_key", re.compile(r"\bAK[A-Z0-9]{18}\b"), "HIGH"),
    ("crypto_wallet", re.compile(r"\b0x[0-9a-fA-F]{40}\b"), "HIGH"),
    ("personal_email", re.compile(r"\bsheehyct@gmail\.com\b"), "LOW"),
]

# Standalone dotted-quad, not part of a longer token (e.g. a version string).
IP_RE = re.compile(r"(?<![\w.])((?:\d{1,3}\.){3}\d{1,3})(?![\w.])")
# Context heuristics to suppress version-string false positives on IP matches.
VERSION_CONTEXT = re.compile(r"(?i)version|release|\bbuild\b|semver|changelog|__version__|\bv\d")
NETWORK_CONTEXT = re.compile(
    r"(?i)\b(ip|host|hostname|addr|address|server|vps|gateway|dns|subnet|endpoint|url)\b"
)

PLACEHOLDER_MARKERS = (
    "xxxx",
    "placeholder",
    "example",
    "your_",
    "your-",
    "changeme",
    "change_me",
    "redacted",
    "dummy",
    "sample",
    "<",
    ">",
    "...",
    "abc123",
    "deadbeef",
    "0000000",
)
KNOWN_PREFIXES = re.compile(
    r"^(sk-ant-|sk-|pk|akia|asia|ak|ghp_|gho_|github_pat_|xox.-|aiza|eyj)", re.IGNORECASE
)


def is_placeholder(text: str) -> bool:
    """True if a key-shaped match is obviously a template/placeholder value."""
    low = text.lower()
    if any(marker in low for marker in PLACEHOLDER_MARKERS):
        return True
    body = KNOWN_PREFIXES.sub("", low)
    # All-same-character (or two-character) bodies are placeholders (xxxx, 0000).
    if body and len(set(body)) <= 2:
        return True
    return False


def load_allowlist() -> tuple[list[re.Pattern[str]], list[str]]:
    """Return (regex allowlist, path-glob allowlist) from the allowlist file."""
    regexes: list[re.Pattern[str]] = []
    path_globs: list[str] = []
    allow_file = REPO_ROOT / "scripts" / "secret_scan_allowlist.txt"
    if not allow_file.exists():
        return regexes, path_globs
    for raw in allow_file.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("path:"):
            path_globs.append(line[len("path:") :].strip())
            continue
        try:
            regexes.append(re.compile(line))
        except re.error:
            print(f"[secret-scan] WARNING: bad allowlist regex skipped: {line}", file=sys.stderr)
    return regexes, path_globs


def git_files(mode: str, paths: list[str]) -> list[str]:
    if mode == "paths":
        return paths
    if mode == "staged":
        cmd = ["git", "-C", str(REPO_ROOT), "diff", "--cached", "--name-only", "--diff-filter=ACM"]
    else:
        cmd = ["git", "-C", str(REPO_ROOT), "ls-files"]
    out = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
    ).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def added_lines_in_range(base: str) -> dict[str, set[int]]:
    """Map each changed file to the set of NEW-file line numbers added in base..HEAD.

    This is the correct scope for a push gate: it scans only what the push
    introduces, so pre-existing content (old test fixtures, historical docs)
    never blocks a push -- only newly added secrets do.
    """
    cmd = [
        "git",
        "-C",
        str(REPO_ROOT),
        "diff",
        f"{base}..HEAD",
        "--unified=0",
        "--no-color",
        "--diff-filter=ACM",
    ]
    out = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
    ).stdout
    added: dict[str, set[int]] = {}
    cur: str | None = None
    newline = 0
    for line in out.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            cur = None if path == "/dev/null" else (path[2:] if path.startswith("b/") else path)
            if cur is not None:
                added.setdefault(cur, set())
            continue
        if line.startswith("@@"):
            m = _HUNK_RE.match(line)
            if m:
                newline = int(m.group(1))
            continue
        if cur is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added[cur].add(newline)
            newline += 1
        elif line.startswith("-") and not line.startswith("---"):
            continue
    return added


def scan_file(
    rel_path: str, allow_regexes: list[re.Pattern[str]]
) -> list[tuple[str, str, int, str]]:
    """Return list of (severity, pattern_name, line_no, snippet)."""
    abs_path = REPO_ROOT / rel_path
    if not abs_path.is_file():
        return []
    if abs_path.suffix.lower() in BINARY_SUFFIXES:
        return []
    try:
        if abs_path.stat().st_size > MAX_BYTES:
            return []
        raw = abs_path.read_bytes()
    except OSError:
        return []
    if b"\x00" in raw[:4096]:  # binary
        return []
    text = raw.decode("utf-8", errors="replace")

    findings: list[tuple[str, str, int, str]] = []
    lines = text.splitlines()

    def allowed(token: str) -> bool:
        return any(rx.search(token) for rx in allow_regexes)

    for name, pattern, severity in PATTERNS:
        for m in pattern.finditer(text):
            token = m.group(0)
            if is_placeholder(token) or allowed(token):
                continue
            line_no = text.count("\n", 0, m.start()) + 1
            snippet = _redact(token)
            findings.append((severity, name, line_no, snippet))

    for m in IP_RE.finditer(text):
        token = m.group(1)
        try:
            ip = ipaddress.ip_address(token)
        except ValueError:
            continue
        if ip.version != 4 or not ip.is_global or allowed(token):
            continue
        line_no = text.count("\n", 0, m.start()) + 1
        line_text = lines[line_no - 1] if line_no - 1 < len(lines) else ""
        # A dotted-quad on a version/release line is almost always a version
        # string, not an IP -- skip unless the line is clearly network-related.
        if VERSION_CONTEXT.search(line_text) and not NETWORK_CONTEXT.search(line_text):
            continue
        findings.append(("HIGH", "public_ipv4", line_no, token))

    return findings


def _redact(token: str) -> str:
    """Show only enough of a secret to identify it; hide the body."""
    if len(token) <= 10:
        return token[:4] + "***"
    return token[:8] + "***" + token[-2:]


def main() -> int:
    parser = argparse.ArgumentParser(description="Secret-scan gate for safe (auto-)push.")
    parser.add_argument("--staged", action="store_true", help="scan only staged changes")
    parser.add_argument("--paths", nargs="*", default=None, help="scan only these paths")
    parser.add_argument(
        "--range",
        dest="range_base",
        default=None,
        help="push gate: scan only lines added in <base>..HEAD (e.g. origin/main)",
    )
    parser.add_argument("--strict", action="store_true", help="also fail on LOW findings")
    args = parser.parse_args()

    allow_regexes, allow_path_globs = load_allowlist()

    def skip(norm: str) -> bool:
        return norm in SELF_SKIP or any(fnmatch.fnmatch(norm, g) for g in allow_path_globs)

    all_findings: list[tuple[str, str, str, int, str]] = []  # path + the 4-tuple

    if args.range_base:
        added = added_lines_in_range(args.range_base)
        scanned = len(added)
        for rel, line_set in added.items():
            norm = rel.replace("\\", "/")
            if skip(norm):
                continue
            for severity, name, line_no, snippet in scan_file(norm, allow_regexes):
                if line_no in line_set:
                    all_findings.append((norm, severity, name, line_no, snippet))
    else:
        mode = "paths" if args.paths else ("staged" if args.staged else "all")
        files = git_files(mode, args.paths or [])
        scanned = len(files)
        for rel in files:
            norm = rel.replace("\\", "/")
            if skip(norm):
                continue
            for severity, name, line_no, snippet in scan_file(norm, allow_regexes):
                all_findings.append((norm, severity, name, line_no, snippet))

    blocking = [f for f in all_findings if f[1] in ("CRITICAL", "HIGH")]
    low = [f for f in all_findings if f[1] == "LOW"]

    if not all_findings:
        print(f"[secret-scan] OK: scanned {scanned} files, no secrets found.")
        return 0

    print(f"[secret-scan] {len(all_findings)} finding(s) across {scanned} scanned files:\n")
    for path, severity, name, line_no, snippet in sorted(
        all_findings, key=lambda x: (x[1] != "CRITICAL", x[0])
    ):
        print(f"  [{severity:8}] {name:18} {path}:{line_no}  ->  {snippet}")

    if blocking:
        print(
            f"\n[secret-scan] BLOCKED: {len(blocking)} CRITICAL/HIGH finding(s). "
            "Remove the secret, gitignore the file, or add a reviewed allowlist "
            "entry to scripts/secret_scan_allowlist.txt before pushing."
        )
        return 2
    if low and args.strict:
        print(f"\n[secret-scan] BLOCKED (--strict): {len(low)} LOW finding(s).")
        return 2
    print(f"\n[secret-scan] PASS with {len(low)} LOW warning(s) (non-blocking).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
