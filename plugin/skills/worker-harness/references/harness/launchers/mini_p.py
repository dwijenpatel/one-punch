#!/usr/bin/env python3
"""mini_p — launcher for mini-swe-agent workers (local models; lowest tier).

Same bundle contract as the other launchers (params.json + instructions.md in,
result.json + transcript out). It takes the empty isolation intent only (no
walls; any isolation field is refused fail-closed) and forwards an operator
stop (SIGTERM/SIGINT) to the worker's process group. Cost is 0 by
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


def write_result(bundle: str, payload: dict[str, object]) -> None:
    with open(os.path.join(bundle, "result.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def refuse(bundle: str, reason: str) -> int:
    write_result(bundle, {"contract": 1, "ok": False, "exit": None, "refused_reason": reason})
    print(f"refused: {reason}", file=sys.stderr)
    return 2


class Interrupted(Exception):
    def __init__(self, signum: int) -> None:
        super().__init__(signum)
        self.signum = signum


def _raise_interrupted(signum: int, frame: object) -> None:
    raise Interrupted(signum)


def _kill_group(pid: int, sig: int) -> None:
    try:
        os.killpg(pid, sig)
    except (ProcessLookupError, PermissionError):
        pass


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    dry_run = "--dry-run" in args
    if dry_run:
        args.remove("--dry-run")
    if len(args) != 1:
        print("usage: mini_p.py [--dry-run] <bundle-dir>", file=sys.stderr)
        return 2
    bundle = os.path.abspath(args[0])
    with open(os.path.join(bundle, "params.json"), encoding="utf-8") as fh:
        params = json.load(fh)

    if params.get("worker", {}).get("tool") != "mini":
        return refuse(bundle, "wrong launcher for this tool")
    if params.get("isolation", {}):
        return refuse(bundle, "mini expresses no isolation; it takes the empty intent {} only")
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
    if dry_run:
        print(json.dumps({"dry_run": True, "argv": argv_out, "cwd": cwd, "timeout_s": params["timeout_s"]}, indent=2))
        return 0
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    t0 = time.monotonic()
    proc = subprocess.Popen(
        argv_out, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, start_new_session=True,
    )
    timed_out = False
    interrupted: int | None = None
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, _raise_interrupted)
    try:
        out, _ = proc.communicate(timeout=params["timeout_s"])
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_group(proc.pid, signal.SIGKILL)
        out, _ = proc.communicate()
    except Interrupted as exc:
        interrupted = exc.signum
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, signal.SIG_IGN)
        _kill_group(proc.pid, signal.SIGTERM)
        try:
            out, _ = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            _kill_group(proc.pid, signal.SIGKILL)
            out, _ = proc.communicate()

    with open(os.path.join(bundle, "transcript.txt"), "w", encoding="utf-8") as fh:
        fh.write(out or "")
    steps = (out or "").count("mini-swe-agent (step")
    ok = (not timed_out) and interrupted is None and proc.returncode == 0
    payload: dict[str, object] = {
        "contract": 1, "ok": ok,
        "exit": None if timed_out else proc.returncode,
        "started_at": started,
        "duration_s": round(time.monotonic() - t0, 3),
        "timed_out": timed_out,
        "interrupted": interrupted is not None,
        "usage": {"steps": steps, "cost_usd": 0.0},
    }
    if not ok:
        payload["error_summary"] = (
            f"interrupted by signal {interrupted}; worker process group terminated"
            if interrupted is not None
            else (out or "").strip()[-300:]
        )
    write_result(bundle, payload)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
