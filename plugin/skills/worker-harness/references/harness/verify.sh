#!/usr/bin/env bash
# The harness's one verify command: every test suite plus strict typing over
# every .py file. The harness itself stays stdlib-only at runtime; this script
# is dev-time and needs uv (it runs mypy through uvx).
#
# Runs from any directory: bash <path>/verify.sh
set -euo pipefail
cd "$(dirname "$0")"

echo "== harness unittest suite"
uv run --no-project python -m unittest

# launchers/ is not a package, so unittest discovery never collects these.
echo "== launchers/test_codex_p.py"
uv run --no-project python launchers/test_codex_p.py
echo "== launchers/test_launchers.py"
uv run --no-project python launchers/test_launchers.py

echo "== mypy --strict (all harness .py)"
uvx mypy --strict ./*.py checks/*.py launchers/*.py

echo "verify: OK"
