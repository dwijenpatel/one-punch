#!/usr/bin/env python3
"""claude_p — launcher for Claude Code headless workers (`claude -p`).

Implements the tool-neutral launcher contract (CONTRACT.md): builds the
`claude -p` invocation from the worker params, enforces the timeout, forwards
an operator stop (SIGTERM/SIGINT) to the worker's process group, and writes
result.json (with binary provenance and the session's usage) and
transcript.txt.

No isolation walls (operator decision, 2026-09-24): the worker runs with
`bypassPermissions` in its own worktree and the harness's integrate step
guards what lands. The bundle's `isolation` must therefore be empty; any
field is an intent this launcher does not express, and it refuses
(fail-closed: nonzero exit, refused_reason in result.json). Hygiene flags
keep ambient configuration (settings hooks, MCP servers, slash commands,
auto-memory, session persistence) away from the worker.

Vendor-mechanism honesty: flag semantics are vendor-build behavior, verified
only by the operator-run smoke (`smoke_workers.sh claude`); --dry-run shows
what would run. Self-contained by design — a new tool's launcher copies this
file's shape, not its imports.
"""

import datetime
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from typing import Any

KNOWN_WORKER_KEYS = {"tool", "model", "effort"}


def utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_result(bundle: str, payload: dict[str, Any]) -> None:
    with open(os.path.join(bundle, "result.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def refuse(bundle: str, reason: str) -> int:
    write_result(
        bundle,
        {
            "contract": 1,
            "ok": False,
            "exit": None,
            "started_at": None,
            "finished_at": utcnow(),
            "refused_reason": reason,
        },
    )
    print(f"refused: {reason}", file=sys.stderr)
    return 2


def validate(params: dict[str, Any]) -> str | None:
    """Return a refusal reason, or None if this launcher can express the intent."""
    if params.get("contract", 1) != 1:
        # Unknown bundle major: refuse fail-closed (T11 policy). Absence is
        # legacy major-1 — old bundles on disk stay readable.
        return f"unknown params contract {params.get('contract')!r} (this launcher speaks 1)"
    worker = params.get("worker", {})
    if not isinstance(worker, dict):
        return "params.worker must be an object"
    unknown = sorted(set(worker) - KNOWN_WORKER_KEYS)
    if unknown:
        return f"unknown worker field(s) this launcher cannot honor: {', '.join(unknown)}"
    if worker.get("tool") != "claude":
        return f"wrong launcher for tool {worker.get('tool')!r} (this is the claude launcher)"
    if not worker.get("model"):
        return "worker.model is required"

    isolation = params.get("isolation", {})
    if not isinstance(isolation, dict):
        return "params.isolation must be an object"
    if isolation:
        # Fail-closed: this launcher expresses no isolation (no walls; the
        # integrate gate guards what lands), so every field is unexpressible.
        return f"isolation field(s) this launcher does not express (it takes {{}}): {', '.join(sorted(isolation))}"

    cwd = params.get("cwd")
    if not cwd or not os.path.isdir(cwd):
        return f"cwd is not a directory: {cwd!r}"
    if not isinstance(params.get("timeout_s"), (int, float)) or params["timeout_s"] <= 0:
        return "timeout_s must be a positive number"
    return None


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


def binary_provenance(resolve_version: bool) -> dict[str, str | None]:
    """Which `claude` will actually run, and (on real runs) its version.

    Vendor builds are the fastest-decaying dependency in the system and the
    2026-07-12 skew (PATH served 2.1.202 while the desktop app ran 2.1.205)
    was invisible until someone thought to look. Recording path+version per
    spawn makes every result self-describing. Version resolution execs the
    binary, so dry-run (which promises to execute nothing) records the path
    only.
    """
    path = shutil.which("claude")
    prov: dict[str, str | None] = {"path": path}
    if path and resolve_version:
        try:
            r = subprocess.run([path, "--version"], capture_output=True,
                               text=True, timeout=30)
            prov["version"] = (r.stdout or r.stderr).strip()
        except Exception as exc:  # provenance must never break a launch
            prov["version"] = f"unavailable: {exc}"[:80]
    return prov


def build_argv(worker: dict[str, Any], instructions_path: str) -> list[str]:
    with open(instructions_path, encoding="utf-8") as fh:
        prompt = fh.read()
    argv = [
        "claude",
        "-p",
        prompt,
        "--model",
        worker["model"],
        # Unattended in its own worktree, no walls (spike 02 P1/P2 on 2.1.281
        # ran edits, tests, pipes, env-prefixed commands and commits with it).
        "--permission-mode",
        "bypassPermissions",
        # Structured output so the session's own token/cost usage is captured
        # in result.json instead of being lost (D14/R4: the harness must
        # measure its own spend). stdout becomes one JSON object; the human
        # transcript is its `result` field. Schema is vendor-build — parsed
        # fail-safe (parse_session) and probed by the smoke.
        "--output-format",
        "json",
        # Ambient-config hardening (flags verified present on 2.1.207 --help;
        # semantics are vendor-build — smoke run 5 is the arbiter): a worker
        # must be reproducible, not shaped by whoever's machine it runs on.
        # User/project/local settings (hooks! could act on every tool call)
        # are excluded; managed policy always applies. NOT --bare: that kills
        # OAuth/keychain auth, which the subscription path needs.
        "--setting-sources", "",
        "--strict-mcp-config",        # no --mcp-config given -> zero MCP servers
        "--disable-slash-commands",   # workers follow instructions.md, not skills
        "--no-session-persistence",   # one-shot workers leave no resumable state
    ]
    if worker.get("effort"):
        # Effort flag semantics are vendor-build: --dry-run shows it, the
        # smoke probe proves it; a wrong flag fails loudly at launch.
        argv += ["--effort", worker["effort"]]
    return argv


def parse_session(stdout: str) -> tuple[str, dict[str, Any], bool | None]:
    """Parse `claude -p --output-format json` stdout.

    Returns (transcript_text, usage, is_error):
    - transcript_text: the session's final message (.result), for human reading
    - usage: normalized token/cost dict, or {"error": ...} if unparseable
    - is_error: the vendor's own error flag, or None if it couldn't be read

    Fail-safe by design: a moved/renamed field or non-JSON output must never
    crash the launcher (its job is to report that the session ran). Token
    capture is best-effort; the gate is the correctness authority regardless.
    Schema decay is vendor-build (validated on the benchmark's 2.1.201 JSONs:
    .usage.{input,output,cache_read_input,cache_creation_input}_tokens,
    .total_cost_usd, .num_turns, .duration_api_ms) — re-probed by the smoke.
    """
    obj = None
    try:
        obj = json.loads((stdout or "").strip())
    except (json.JSONDecodeError, AttributeError):
        # Tolerate stray lines around the JSON: take the last line that parses.
        for line in reversed((stdout or "").splitlines()):
            line = line.strip()
            if line.startswith("{"):
                try:
                    obj = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
    if not isinstance(obj, dict):
        return (stdout or "", {"error": "unparseable --output-format json output"}, None)
    u = obj.get("usage") or {}
    usage = {
        "input_tokens": u.get("input_tokens"),
        "output_tokens": u.get("output_tokens"),
        "cache_read_tokens": u.get("cache_read_input_tokens"),
        "cache_creation_tokens": u.get("cache_creation_input_tokens"),
        "cost_usd": obj.get("total_cost_usd"),
        "num_turns": obj.get("num_turns"),
        "api_duration_ms": obj.get("duration_api_ms"),
    }
    text = obj.get("result")
    return (text if isinstance(text, str) else (stdout or ""), usage, bool(obj.get("is_error")))


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    dry_run = "--dry-run" in args
    if dry_run:
        args.remove("--dry-run")
    if len(args) != 1:
        print("usage: claude_p.py [--dry-run] <bundle-dir>", file=sys.stderr)
        return 2
    bundle = os.path.abspath(args[0])

    try:
        with open(os.path.join(bundle, "params.json"), encoding="utf-8") as fh:
            params = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read params.json: {exc}", file=sys.stderr)
        return 2
    instructions = os.path.join(bundle, "instructions.md")
    if not os.path.isfile(instructions):
        return refuse(bundle, "bundle has no instructions.md")

    reason = validate(params)
    if reason:
        return refuse(bundle, reason)

    argv_out = build_argv(params["worker"], instructions)
    # Auto-memory would leak the operator's accumulated context into a worker
    # that is supposed to see only its bundle. Env-var name is community-
    # reported, unverified on this build — harmless if ignored, and smoke
    # run 5 checks the transcript for memory traces either way.
    env_extra = {"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}

    if dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "argv": argv_out,
                    "binary": binary_provenance(resolve_version=False),
                    "cwd": params["cwd"],
                    "env_extra": env_extra,
                    "timeout_s": params["timeout_s"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    binary = binary_provenance(resolve_version=True)
    started = utcnow()
    t0 = time.monotonic()
    # stderr kept SEPARATE from stdout so stdout is clean JSON to parse;
    # stderr is preserved only when parsing fails (for debuggability).
    proc = subprocess.Popen(
        argv_out,
        cwd=params["cwd"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
        env={**os.environ, **env_extra},
    )
    timed_out = False
    interrupted: int | None = None
    # The worker runs in its own session, so a signal to this launcher's
    # process group (the harness's operator stop) never reaches it: forward
    # SIGTERM/SIGINT to the worker's group, then report, never orphan a
    # session that keeps spending quota and committing.
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, _raise_interrupted)
    try:
        out, errout = proc.communicate(timeout=params["timeout_s"])
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_group(proc.pid, signal.SIGKILL)
        out, errout = proc.communicate()
    except Interrupted as exc:
        interrupted = exc.signum
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, signal.SIG_IGN)
        _kill_group(proc.pid, signal.SIGTERM)
        try:
            out, errout = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            _kill_group(proc.pid, signal.SIGKILL)
            out, errout = proc.communicate()

    transcript_text, usage, is_error = parse_session(out or "")
    with open(os.path.join(bundle, "transcript.txt"), "w", encoding="utf-8") as fh:
        if usage.get("error"):
            # parse failed: keep the raw streams so nothing is lost
            fh.write((out or "") + (f"\n--- stderr ---\n{errout}" if errout else ""))
        else:
            fh.write(transcript_text or "")

    # Fail-closed on a vendor-reported session error (is_error), on top of the
    # exit/timeout checks. is_error is None when unparseable -> exit governs.
    ok = (not timed_out) and interrupted is None and proc.returncode == 0 and not is_error
    payload: dict[str, Any] = {
        "contract": 1,
        "ok": ok,
        "exit": None if timed_out else proc.returncode,
        "started_at": started,
        "finished_at": utcnow(),
        "duration_s": round(time.monotonic() - t0, 3),
        "timed_out": timed_out,
        "interrupted": interrupted is not None,
        "binary": binary,
        "usage": usage,
    }
    if not ok:
        # Surface the vendor's own words so the caller can classify the
        # failure (environment vs solution — e.g. the usage-window wall).
        payload["error_summary"] = (
            f"interrupted by signal {interrupted}; worker process group terminated"
            if interrupted is not None
            else (transcript_text or "").strip()[:300] or (errout or "").strip()[-300:]
        )
    write_result(bundle, payload)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
