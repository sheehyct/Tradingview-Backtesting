#!/usr/bin/env bash
# Cloud test gate for tradingview-backtesting (Stop hook; settings.json runs it
# only when CLAUDE_CODE_REMOTE=true). Mirrors the tvb branch of the spine's
# C:\Strat_Trading_Bot\.claude\hooks\stop_test_gate.sh, minus its
# directory-name detection: a cloud clone is named Tradingview-Backtesting,
# which that script's lowercase case-match misses (it would skip silently).
#
# Exit 0 = allow completion. Exit 2 = tests failed, keep working.
# SKIP_TEST_GATE=1 bypasses the gate.

if [[ "${SKIP_TEST_GATE:-0}" == "1" ]]; then
    exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

if ! command -v uv >/dev/null 2>&1; then
    echo "stop_test_gate (cloud): uv not found, skipping; install uv in the environment setup script" >&2
    exit 0
fi

uv run pytest tests/ -q 2>&1 | tail -20
TEST_EXIT=${PIPESTATUS[0]}

if [[ $TEST_EXIT -ne 0 ]]; then
    echo "STOP TEST GATE (cloud): tests FAILED (exit code $TEST_EXIT). Fix failing tests before completing. Set SKIP_TEST_GATE=1 to bypass." >&2
    exit 2
fi

echo "stop_test_gate (cloud): tests passed" >&2
exit 0
