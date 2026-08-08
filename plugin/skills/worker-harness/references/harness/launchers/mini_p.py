#!/usr/bin/env python3
"""mini_p — launcher for mini-swe-agent workers (local models; lowest tier).

Same bundle contract as the other launchers (params.json + instructions.md in,
result.json + transcript out). mini offers NO isolation mechanisms, so any
isolation intent beyond an empty one is refused fail-closed — route only
trivial, low-sensitivity tickets here, in throwaway clones. Cost is 0 by
construction (local inference); usage reports step count when parseable.

Operator prerequisites: `mini` on PATH, a repo-root mini config (mini.yaml
with the model/agent settings, incl. any compaction agent for small context
windows), and the local model server running. The harness treats a dead server
as a LimitHit with a short cooldown, not a failure of the ticket.
"""

import json
import os
import signal
import subprocess
import sys
import time


def write_result(bundle: str, payload: dict) -> None:
    with open(os.path.join(bundle, "result.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def refuse(bundle: str, reason: str) -> int:
    write_result(bundle, {"contract": 1, "ok": False, "exit": None, "refused_reason": reason})
    print(f"refused: {reason}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: mini_p.py <bundle-dir>", file=sys.stderr)
        return 2
    bundle = os.path.abspath(args[0])
    with open(os.path.join(bundle, "params.json"), encoding="utf-8") as fh:
        params = json.load(fh)

    if params.get("worker", {}).get("tool") != "mini":
        return refuse(bundle, "wrong launcher for this tool")
    if any(params.get("isolation", {}).get(k) for k in ("deny_read", "sandbox")):
        return refuse(bundle, "mini has no isolation mechanisms; refuse rather than launch unwalled")
    cwd = params.get("cwd")
    if not cwd or not os.path.isdir(cwd):
        return refuse(bundle, f"cwd is not a directory: {cwd!r}")

    with open(os.path.join(bundle, "instructions.md"), encoding="utf-8") as fh:
        prompt = fh.read()
    step_limit = int(params.get("worker", {}).get("step_limit", 200))
    argv_out = [
        "mini", "-t", prompt, "-y", "--exit-immediately",
        "-o", os.path.join(bundle, "trajectory.json"),
        "-c", "mini.yaml", "-c", f"agent.step_limit={step_limit}",
    ]
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    t0 = time.monotonic()
    proc = subprocess.Popen(
        argv_out, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, start_new_session=True,
    )
    timed_out = False
    try:
        out, _ = proc.communicate(timeout=params["timeout_s"])
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        out, _ = proc.communicate()

    with open(os.path.join(bundle, "transcript.txt"), "w", encoding="utf-8") as fh:
        fh.write(out or "")
    steps = (out or "").count("mini-swe-agent (step")
    ok = (not timed_out) and proc.returncode == 0
    write_result(bundle, {
        "contract": 1, "ok": ok,
        "exit": None if timed_out else proc.returncode,
        "started_at": started,
        "duration_s": round(time.monotonic() - t0, 3),
        "timed_out": timed_out,
        "usage": {"steps": steps, "cost_usd": 0.0},
    })
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
