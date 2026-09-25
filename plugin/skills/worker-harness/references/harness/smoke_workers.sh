#!/bin/sh
# smoke_workers.sh — v4 spike 02: headless workers on the current CLI builds.
# Launcher-level (no build loop). Builds a scratch repo, one git worktree per
# worker (created serially, as the harness will), one bundle per worker, then
# launches all workers CONCURRENTLY and reports per-worker outcome.
# No isolation walls by operator decision (plan §9): claude workers get an
# empty isolation intent -> bypassPermissions in their worktree.
#
#   smoke_workers.sh claude [--n N]  --rehearse                        # FREE: build + launcher --dry-run
#   smoke_workers.sh claude [--n N]  --i-understand-this-spends-quota  # P1 (n=1), P2 (n=2, n=4)
#   smoke_workers.sh codex --review  --rehearse | --i-understand-...   # P3: codex as read-only lens
#
# Models: SMOKE_CLAUDE_MODEL (default sonnet), SMOKE_CODEX_MODEL (default gpt-5.6-sol).
set -eu

TOOL="${1:-}"; shift || true
N=1; REVIEW=0; MODE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --n) N="$2"; shift 2 ;;
    --review) REVIEW=1; shift ;;
    --rehearse|--i-understand-this-spends-quota) MODE="$1"; shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
if [ "$TOOL" != "claude" ] && [ "$TOOL" != "codex" ]; then
  echo "usage: smoke_workers.sh claude|codex [--n N] [--review] --rehearse|--i-understand-this-spends-quota" >&2; exit 2
fi
[ -n "$MODE" ] || { echo "pass --rehearse (free) or --i-understand-this-spends-quota" >&2; exit 2; }
if [ "$TOOL" = "codex" ] && [ "$REVIEW" -ne 1 ]; then echo "codex runs only as --review (the B3 lens)" >&2; exit 2; fi

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(mktemp -d "${TMPDIR:-/tmp}/smoke-workers.XXXXXX")
REPO="$ROOT/repo"
echo "smoke root: $ROOT"

# --- scratch repo on main -----------------------------------------------------
mkdir -p "$REPO"
git -C "$REPO" init -q -b main
cat > "$REPO/calc.py" <<'PY'
def add(a, b):
    return a + b
PY
cat > "$REPO/test_calc.py" <<'PY'
import unittest
from calc import add


class AddTest(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)


if __name__ == "__main__":
    unittest.main()
PY
git -C "$REPO" add -A
git -C "$REPO" -c user.name=smoke -c user.email=smoke@localhost commit -q -m "base"
BASE=$(git -C "$REPO" rev-parse main)

bundle_params() { # $1 bundle dir, $2 cwd, $3 tool, $4 model, $5 isolation json
  cat > "$1/params.json" <<JSON
{"contract": 1, "role": "smoke-worker", "worker": {"tool": "$3", "model": "$4"},
 "isolation": $5, "cwd": "$2", "timeout_s": 900}
JSON
}

WORKERS=""
if [ "$TOOL" = "claude" ]; then
  MODEL="${SMOKE_CLAUDE_MODEL:-sonnet}"
  i=1
  while [ "$i" -le "$N" ]; do
    WT="$REPO/.worktrees/w$i"
    git -C "$REPO" worktree add -q -b "t/w$i" "$WT" main       # serial, like the harness
    B="$ROOT/bundles/w$i"; mkdir -p "$B"
    cat > "$B/instructions.md" <<MD
You are a worker in a git worktree (your cwd) on branch t/w$i. Work only in your cwd.

1. Create ops_$i.py with a function mul_$i(a, b) returning a * b, and test_ops_$i.py with a unittest for it.
2. Run: python3 -m unittest -q   (all tests must pass)
3. Run each of these commands and record for each, in probe_$i.txt, one line "<command> => ran | blocked | needed approval":
   python3 -c 'print(1)'
   echo hi | wc -c
   FOO=bar sh -c 'echo \$FOO'
4. In probe_$i.txt also record one line "skill tdd => available | unavailable" (is a skill or slash command named tdd available to you?).
5. Commit everything on your branch: git add -A && git -c user.name=worker -c user.email=worker@localhost commit -m "w$i: mul_$i"
6. Reply with one line: DONE or the reason you could not finish.
MD
    bundle_params "$B" "$WT" claude "$MODEL" "{}"
    WORKERS="$WORKERS w$i"
    i=$((i + 1))
  done
  LAUNCHER="$HERE/launchers/claude_p.py"
else
  MODEL="${SMOKE_CODEX_MODEL:-gpt-5.6-sol}"
  git -C "$REPO" switch -q -c t/review
  cat > "$REPO/calc.py" <<'PY'
def add(a, b):
    return a + b


def divide(a, b):
    return a / b
PY
  git -C "$REPO" -c user.name=smoke -c user.email=smoke@localhost commit -q -am "add divide"
  git -C "$REPO" switch -q main
  WT="$REPO/.worktrees/review"
  git -C "$REPO" worktree add -q "$WT" t/review
  B="$ROOT/bundles/review"; mkdir -p "$B"
  cat > "$B/instructions.md" <<'MD'
You are a read-only code reviewer. Review the change on this branch against main: run `git diff main...HEAD`.
Write your findings to review.md in your cwd: each finding as "- [severity] file:line — problem — failure scenario".
Do not modify, create or delete any other file, and do not commit. Reply with one line: DONE.
MD
  bundle_params "$B" "$WT" codex "$MODEL" '{"sandbox": true, "network": true}'
  WORKERS=" review"
  LAUNCHER="$HERE/launchers/codex_p.py"
fi

if [ "$MODE" = "--rehearse" ]; then
  for w in $WORKERS; do
    echo "--- $w (dry-run) ---"
    python3 "$LAUNCHER" --dry-run "$ROOT/bundles/$w" | rg -v '^\s*"(You are|[0-9]\.|  )' || true
  done
  echo; echo "rehearsal OK ($TOOL, n=$N). The real run: $0 $TOOL --n $N $( [ $REVIEW -eq 1 ] && echo --review ) --i-understand-this-spends-quota"
  exit 0
fi

# --- launch all workers concurrently -------------------------------------------
T0=$(date +%s)
for w in $WORKERS; do
  ( python3 "$LAUNCHER" "$ROOT/bundles/$w" > "$ROOT/bundles/$w/launcher.out" 2> "$ROOT/bundles/$w/launcher.err"; \
    echo $? > "$ROOT/bundles/$w/launcher.exit" ) &
done
wait
T1=$(date +%s)

# --- report -------------------------------------------------------------------
echo "wall-clock all workers: $((T1 - T0))s   main unchanged: $( [ "$(git -C "$REPO" rev-parse main)" = "$BASE" ] && echo yes || echo NO )"
for w in $WORKERS; do
  B="$ROOT/bundles/$w"
  echo "=== $w  launcher exit $(cat "$B/launcher.exit")"
  python3 - "$B/result.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
print(json.dumps({k: r.get(k) for k in ("ok", "exit", "duration_s", "timed_out", "binary", "usage", "error_summary", "refused_reason")}, indent=1))
PY
  if [ "$TOOL" = "claude" ]; then
    echo "branch t/$w commits:"; git -C "$REPO" log --oneline "main..t/$w"
    echo "files changed vs main:"; git -C "$REPO" diff --name-only main "t/$w"
    echo "probe:"; cat "$REPO/.worktrees/$w/probe_${w#w}.txt" 2>/dev/null || echo "(no probe file)"
  else
    echo "worktree status (expect only review.md untracked):"; git -C "$REPO/.worktrees/review" status --short
    echo "review.md:"; cat "$REPO/.worktrees/review/review.md" 2>/dev/null || echo "(missing)"
  fi
  [ -s "$B/launcher.err" ] && { echo "launcher stderr:"; tail -20 "$B/launcher.err"; }
done
echo; echo "artifacts: $ROOT (bundles/*/{result.json,transcript.txt})"
