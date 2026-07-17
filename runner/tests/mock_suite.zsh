#!/bin/zsh
# Mock test of runner.py's plan-review A/B choreography (no quota: claude is shimmed).
set -e
SCRATCH=$(mktemp -d /tmp/one-punch-mock.XXXXXX)
HERE="${0:a:h}"
RUNNER="${0:a:h}/../runner.py"
mkdir -p "$SCRATCH/bin" && cp "$HERE/bin/claude" "$SCRATCH/bin/claude"
export PATH="$SCRATCH/bin:$PATH"
chmod +x "$SCRATCH/bin/claude"

fail() { print -u2 "FAIL: $1"; exit 1 }

rm -rf "$SCRATCH/work" && mkdir -p "$SCRATCH/work" && cd "$SCRATCH/work"

--- () { print -r -- "--- $*" }  # zsh-safe separator func

--- seed
mkdir seed && cd seed && git init -q
git -c user.email=t@t -c user.name=t commit -q --allow-empty -m x >/dev/null 2>&1 || true
print "the design doc" > design-draft.md
git add -A && git -c user.email=t@t -c user.name=t commit -qm seed
cd ..

--- "1: plan + stop-after-plan (fork point)"
out=$(python3 "$RUNNER" --repo "$PWD/seed" --plan design-draft.md --stop-after-plan --yes)
print "$out" | grep -q "PLAN COMPLETE" || fail "no PLAN COMPLETE banner"
[[ -f seed/tasks.json ]] || fail "planner left no tasks.json"
[[ -f seed/.runner/ledger.jsonl ]] || fail "no ledger after plan"
grep -q '"stage": "planned"' seed/.runner/ledger.jsonl || fail "no planned record"

--- "2: fork"
cp -R seed armA
cp -R seed armB

--- "3: arm A (no plan-review)"
python3 "$RUNNER" --repo "$PWD/armA" --yes > armA.log
grep -q "RUN COMPLETE" armA.log || fail "arm A did not complete"
grep -q "plan-review-done" armA/.runner/ledger.jsonl && fail "arm A ran plan-review"
[[ -f armA/plan-review-report.md ]] && fail "arm A has a report"

--- "4: arm B (--plan-review)"
python3 "$RUNNER" --repo "$PWD/armB" --plan-review --yes > armB.log
grep -q "RUN COMPLETE" armB.log || fail "arm B did not complete"
grep -q '"stage": "plan-review-done"' armB/.runner/ledger.jsonl || fail "no plan-review-done record"
[[ -f armB/plan-review-report.md ]] || fail "arm B report missing"
grep -q "PINNED" armB/specs/t1.md || fail "spec amendment missing"
git -C armB ls-files | grep -q "^.claude/skills/plan-review" && fail "skill still installed at HEAD"
[[ -d armB/.claude/skills/plan-review ]] && fail "skill dir still on disk"

--- "5: ledger never tracked (info/exclude fix)"
git -C armB ls-files | grep -q "^.runner" && fail ".runner is tracked"
git -C armA ls-files | grep -q "^.runner" && fail ".runner is tracked (A)"

--- "6: resume idempotence (arm B rerun: everything skipped)"
python3 "$RUNNER" --repo "$PWD/armB" --plan-review --yes > armB2.log
grep -q "skip (done): t1" armB2.log || fail "resume did not skip t1"
[[ $(grep -c '"stage": "plan-review-done"' armB/.runner/ledger.jsonl) -eq 1 ]] || fail "plan-review re-ran on resume"

--- "7: silent-no-op guard (skill unresolved -> halt)"
cp -R seed armC
mv "$SCRATCH/bin/claude" "$SCRATCH/bin/claude.real"
print '#!/bin/zsh\nprint "{\\"num_turns\\":1}"' > "$SCRATCH/bin/claude"
chmod +x "$SCRATCH/bin/claude"
set +e
python3 "$RUNNER" --repo "$PWD/armC" --plan-review --yes > armC.log 2>&1
rc=$?
set -e
mv "$SCRATCH/bin/claude.real" "$SCRATCH/bin/claude"
[[ $rc -eq 1 ]] || fail "no-op arm exited $rc, want 1"
grep -q "no plan-review-report.md" armC.log || fail "wrong halt reason"

--- "8: permission-denied planner -> clean Halt, no planned record"
mkdir seedX && cd seedX && git init -q
print "doc" > design-draft.md
git add -A && git -c user.email=t@t -c user.name=t commit -qm seed
cd ..
set +e
CLAUDE_SHIM_DENY=1 python3 "$RUNNER" --repo "$PWD/seedX" --plan design-draft.md --yes > seedX.log 2>&1
rc=$?
set -e
[[ $rc -eq 1 ]] || fail "denied planner exited $rc, want 1"
grep -q "wrote no tasks.json" seedX.log || fail "wrong halt reason for denied planner"
grep -q "permission denials" seedX.log || fail "denial warning not surfaced"
grep -q '"stage": "planned"' seedX/.runner/ledger.jsonl && fail "planned record written despite no manifest"
grep -q '"permission_denials": 2' seedX/.runner/ledger.jsonl || fail "denial count missing from ledger"

--- "9: closure base derives from ledger planned sha, not resume-point HEAD"
plannedsha=$(python3 -c "
import json
sha=None
for line in open('armB/.runner/ledger.jsonl'):
    r=json.loads(line)
    if r.get('stage')=='planned': sha=r['sha']
print(sha)")
derived=$(python3 -c "
import sys, argparse
sys.path.insert(0, '$(dirname $RUNNER)')
import runner
r = runner.Runner(argparse.Namespace(repo='$PWD/armB'))
print(r.plan_base())")
headsha=$(git -C armB rev-parse HEAD)
[[ "$derived" == "$plannedsha" ]] || fail "plan_base $derived != planned $plannedsha"
[[ "$derived" != "$headsha" ]] || fail "plan_base degenerated to HEAD"

--- "10: --stop-after-plan-review halts before any task builds"
cp -R seed armD
python3 "$RUNNER" --repo "$PWD/armD" --plan-review --stop-after-plan-review --yes > armD.log
grep -q "PLAN-REVIEW COMPLETE" armD.log || fail "no PLAN-REVIEW COMPLETE banner"
grep -q '"stage": "plan-review-done"' armD/.runner/ledger.jsonl || fail "no plan-review-done record"
[[ -f armD/plan-review-report.md ]] || fail "armD report missing"
grep -q '"stage": "task-done"' armD/.runner/ledger.jsonl && fail "a task built despite stop flag"
[[ -f armD/hello.py ]] && fail "implement ran despite stop flag"

--- "ALL MOCK TESTS PASS"
