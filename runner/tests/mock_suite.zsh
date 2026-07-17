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

--- "11: worker BLOCKED status -> clean halt carrying the worker's reason"
cp -R seed armE
set +e
CLAUDE_SHIM_BLOCK=1 python3 "$RUNNER" --repo "$PWD/armE" --yes > armE.log 2>&1
rc=$?
set -e
[[ $rc -eq 1 ]] || fail "blocked worker exited $rc, want 1"
grep -q "worker reports BLOCKED: spec contradicts CLAUDE.md rule 3" armE.log || fail "blocked reason not surfaced"
grep -q '"stage": "worker-blocked"' armE/.runner/ledger.jsonl || fail "no worker-blocked record"
[[ -f armE/hello.py ]] && fail "blocked worker still produced the artifact"
grep -q '"stage": "task-done"' armE/.runner/ledger.jsonl && fail "task marked done despite block"

--- "12: liar status (done, no commit) -> contradiction halt"
cp -R seed armF
set +e
CLAUDE_SHIM_LIAR=1 python3 "$RUNNER" --repo "$PWD/armF" --yes > armF.log 2>&1
rc=$?
set -e
[[ $rc -eq 1 ]] || fail "liar worker exited $rc, want 1"
grep -q "says done but no commit exists" armF.log || fail "contradiction not surfaced"

--- "13: oracle authors blind at build-base, suite runs green against built tree"
mkdir seedO && cd seedO && git init -q
print "the design doc" > design-draft.md
mkdir -p docs && print "# PRD: acceptance criteria A1-A9" > docs/prd.md
git add -A && git -c user.email=t@t -c user.name=t commit -qm seed
cd ..
python3 "$RUNNER" --repo "$PWD/seedO" --plan design-draft.md --yes > seedO.log
grep -q "RUN COMPLETE" seedO.log || fail "oracle-green run did not complete"
grep -q "oracle GREEN" seedO.log || fail "no oracle GREEN in banner"
grep -q '"stage": "oracle", "green": true' seedO/.runner/ledger.jsonl || fail "no green oracle record"
[[ -d seedO/oracle_tests ]] && fail "oracle_tests left in the built tree"
[[ -n "$(git -C seedO status --porcelain)" ]] && fail "built tree left dirty by oracle"
ls seedO/.runner/*/oracle_tests/test_oracle.py >/dev/null 2>&1 || fail "oracle suite not archived"
clone_impl=(seedO/.runner/*/oracle-clone/hello.py(N))
[[ ${#clone_impl} -eq 0 ]] || fail "oracle clone contains the implementation (blindness broken)"

--- "14: oracle RED -> exit 3, verdict is evidence not a halt"
mkdir seedR && cd seedR && git init -q
print "the design doc" > design-draft.md
mkdir -p docs && print "# PRD: acceptance criteria A1-A9" > docs/prd.md
git add -A && git -c user.email=t@t -c user.name=t commit -qm seed
cd ..
set +e
CLAUDE_SHIM_ORACLE_RED=1 python3 "$RUNNER" --repo "$PWD/seedR" --plan design-draft.md --yes > seedR.log 2>&1
rc=$?
set -e
[[ $rc -eq 3 ]] || fail "oracle-red run exited $rc, want 3"
grep -q "ORACLE RED" seedR.log || fail "no ORACLE RED banner"
grep -q '"stage": "oracle", "green": false' seedR/.runner/ledger.jsonl || fail "no red oracle record"
grep -q '"stage": "task-done"' seedR/.runner/ledger.jsonl || fail "tasks should still have built"

--- "15: --skip-plan records run-base; plan_base derives from it, not HEAD"
mkdir seedS && cd seedS && git init -q
mkdir -p specs && cp ../seed/specs/t1.md specs/t1.md && cp ../seed/tasks.json tasks.json
git add -A && git -c user.email=t@t -c user.name=t commit -qm seed
basesha=$(git rev-parse HEAD)
cd ..
python3 "$RUNNER" --repo "$PWD/seedS" --skip-plan --yes > seedS.log
grep -q "RUN COMPLETE" seedS.log || fail "skip-plan run did not complete"
grep -q '"stage": "run-base"' seedS/.runner/ledger.jsonl || fail "no run-base record"
derived=$(python3 -c "
import sys, argparse
sys.path.insert(0, '$(dirname $RUNNER)')
import runner
r = runner.Runner(argparse.Namespace(repo='$PWD/seedS'))
print(r.plan_base())")
[[ "$derived" == "$basesha" ]] || fail "plan_base $derived != run-base $basesha"
[[ "$derived" != "$(git -C seedS rev-parse HEAD)" ]] || fail "plan_base degenerated to post-build HEAD"

--- "ALL MOCK TESTS PASS"
