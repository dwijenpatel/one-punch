#!/usr/bin/env python3
"""codex_p — launcher for Codex CLI headless workers (`codex exec`).

Implements the tool-neutral launcher contract (CONTRACT.md): builds the
`codex exec` invocation from the worker params, enforces the timeout,
forwards an operator stop (SIGTERM/SIGINT) to the worker's process group, and
writes result.json (with binary provenance and the session's usage) and
transcript.txt.

Its one job in the harness is the decorrelated B3 lens: a read-only reviewer
from another model family. The harness sends the isolation intent
`{"sandbox": true, "network": true}`, the shape spike 02 (P3, codex-cli
0.156.1, 2026-09-25) ran unattended: the worker wrote only its review file.
There are no isolation walls (operator decision, 2026-09-24); the harness
rejects a reviewer's change outside its review files.

`sandbox: true` is expressed as a generated Codex permission profile, written
per spawn as $CODEX_HOME/<uniq>.config.toml and loaded via `--profile <uniq>`
(`-c` cannot carry the profile table; smoke attempt 1, 2026-07-13). The
profile `extends = ":workspace"` (cwd writable, unattended commands) and sets
`network.enabled` from the intent; activation stays on the flat
`-c default_permissions=...`, so a profile file that fails to load aborts
loudly instead of running under whatever the user's config says. Profiles
are mutually exclusive with the older `--sandbox` flag, so it is never
passed. `sandbox: false` has no safe expression (an unflagged `codex exec`
inherits the user's config) and is refused, as is any other isolation field.

Ambient config: `--ignore-user-config` is deliberately absent — it suppresses
`--profile` files too (probed 2026-07-13). The user's config.toml loads under
the profile layer: keys the launcher sets win (model and effort on argv;
`notify = []` in the profile), unset keys are a documented ambient residual.
`--ignore-rules` drops ambient execpolicy rules; `--strict-config` turns an
unknown key into a loud startup failure.

Vendor-mechanism honesty: permission profiles are beta and the event schema
is vendor-build; the operator-run smoke (`smoke_workers.sh codex --review`)
is the arbiter. Self-contained by design.
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

KNOWN_ISOLATION_KEYS = {"sandbox", "network"}
KNOWN_WORKER_KEYS = {"tool", "model", "effort"}
PROFILE = "worker_workspace"


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
        return f"unknown params contract {params.get('contract')!r} (this launcher speaks 1)"
    worker = params.get("worker", {})
    if not isinstance(worker, dict):
        return "params.worker must be an object"
    unknown = sorted(set(worker) - KNOWN_WORKER_KEYS)
    if unknown:
        return f"unknown worker field(s) this launcher cannot honor: {', '.join(unknown)}"
    if worker.get("tool") != "codex":
        return f"wrong launcher for tool {worker.get('tool')!r} (this is the codex launcher)"
    if not worker.get("model"):
        return "worker.model is required"

    isolation = params.get("isolation", {})
    if not isinstance(isolation, dict):
        return "params.isolation must be an object"
    unknown = sorted(set(isolation) - KNOWN_ISOLATION_KEYS)
    if unknown:
        return f"unknown isolation field(s) this launcher cannot express: {', '.join(unknown)}"
    if isolation.get("sandbox") is not True:
        # `codex exec` without an explicit profile inherits whatever
        # ~/.codex/config.toml says — unknowable here.
        return (
            "this launcher only launches sandboxed workers "
            "(isolation.sandbox must be true; sandbox=false has no safe "
            "codex expression)"
        )
    if isolation.get("network", True) not in (True, False):
        return "isolation.network must be a boolean"

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
    """Which `codex` will actually run, and (on real runs) its version.
    Same rationale as claude_p: vendor builds are the fastest-decaying
    dependency; path+version per spawn makes every result self-describing.
    Dry-run promises to execute nothing, so it records the path only."""
    path = shutil.which("codex")
    prov: dict[str, str | None] = {"path": path}
    if path and resolve_version:
        try:
            r = subprocess.run([path, "--version"], capture_output=True,
                               text=True, timeout=30)
            prov["version"] = (r.stdout or r.stderr).strip()
        except Exception as exc:  # provenance must never break a launch
            prov["version"] = f"unavailable: {exc}"[:80]
    return prov


def build_profile_toml(isolation: dict[str, Any]) -> str:
    """The generated permission profile, as a TOML config-profile file.

    `extends = ":workspace"` is load-bearing: unmentioned paths are denied by
    default, so a bare profile would break the worker. The file layers over
    the user's config.toml, so its top-level keys neutralize ambient
    behavior: `notify = []` keeps turn-end hooks from firing for workers.
    Top-level keys must precede the first table header.
    """
    lines = [
        "# generated per-spawn by codex_p.py — removed after the run",
        "notify = []",
        f"[permissions.{PROFILE}]",
        'extends = ":workspace"',
        f"[permissions.{PROFILE}.network]",
        "enabled = " + ("true" if isolation.get("network", True) else "false"),
    ]
    return "\n".join(lines) + "\n"


def codex_home() -> str:
    return os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")


def build_argv(worker: dict[str, Any], cwd: str, last_message_path: str, profile_name: str) -> list[str]:
    """Translate params into `codex exec` argv. The prompt travels via stdin
    (explicit `-`), never argv — instructions.md can be long.

    Flag facts (codex-cli --help + the permissions docs; vendor-build):
    - `--profile <name>` loads $CODEX_HOME/<name>.config.toml
      (build_profile_toml); the flat `-c default_permissions=...` activates
      it, so a failed file load aborts loudly;
    - `--ignore-rules`: no ambient execpolicy rules;
    - `--strict-config`: unknown keys abort instead of silently degrading;
    - `--skip-git-repo-check`: a cwd that is not a git repository is allowed;
    - `--ephemeral`: workers are one-shot; persist no session;
    - `--output-last-message`: the worker's final message, captured to a
      file (the transcript source of truth);
    - `--json`: JSONL events on stdout (usage extraction, best-effort).
    """
    argv = [
        "codex", "exec",
        "--json",
        "--color", "never",
        "--cd", cwd,
        "--model", worker["model"],
        "--ignore-rules",
        "--strict-config",
        "--skip-git-repo-check",
        "--ephemeral",
        "--output-last-message", last_message_path,
        "--profile", profile_name,
        "-c", f'default_permissions="{PROFILE}"',
    ]
    if worker.get("effort"):
        # Effort names are vendor-interpreted (model_reasoning_effort);
        # a wrong value fails loudly at launch — same doctrine as claude_p.
        argv += ["-c", f'model_reasoning_effort="{worker["effort"]}"']
    argv.append("-")  # prompt from stdin
    return argv


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def parse_events(stdout: str | None) -> tuple[dict[str, Any], bool | None]:
    """Parse `codex exec --json` JSONL stdout. Returns (usage, is_error).

    Fail-safe by design: the event schema is vendor-build; a moved field must
    never crash the launcher. Walk every line that parses as a JSON object,
    remember the last plausible token-usage payload (at the event's top
    level, under "usage", and under "info" token-usage keys — the shapes
    Codex versions are known to emit), and whether the last event type looks
    fatal.
    """
    usage_raw: dict[str, Any] | None = None
    turns = 0
    last_type = None
    for line in (stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        msg = _dict(event.get("msg"))
        etype = str(event.get("type") or msg.get("type") or "")
        if etype:
            last_type = etype
        if "turn.completed" in etype:
            turns += 1
        for candidate in (
            event.get("usage"),
            msg.get("usage"),
            _dict(event.get("info")).get("total_token_usage"),
            _dict(msg.get("info")).get("total_token_usage"),
        ):
            if isinstance(candidate, dict) and any(
                isinstance(candidate.get(k), int)
                for k in ("input_tokens", "output_tokens")
            ):
                usage_raw = candidate
    usage: dict[str, Any]
    if usage_raw is None:
        usage = {"error": "no usage-bearing event found in --json output"}
    else:
        usage = {
            "input_tokens": usage_raw.get("input_tokens"),
            "output_tokens": usage_raw.get("output_tokens"),
            # codex names cache reads "cached_input_tokens"; no write counter
            "cache_read_tokens": usage_raw.get("cached_input_tokens"),
            "cache_creation_tokens": None,
            "cost_usd": None,  # codex exposes no cost field
            "num_turns": turns or None,
            "api_duration_ms": None,
        }
    is_error = None
    if last_type:
        is_error = any(marker in last_type for marker in ("error", "failed"))
    return usage, is_error


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    dry_run = "--dry-run" in args
    if dry_run:
        args.remove("--dry-run")
    if len(args) != 1:
        print("usage: codex_p.py [--dry-run] <bundle-dir>", file=sys.stderr)
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

    last_message_path = os.path.join(bundle, "last-message.txt")
    profile_toml = build_profile_toml(params.get("isolation", {}))
    profile_name = f"codex-p-{os.getpid()}-{int(time.time())}"
    argv_out = build_argv(params["worker"], params["cwd"], last_message_path, profile_name)
    # Audit copy: the profile's exact definition travels with the bundle.
    with open(os.path.join(bundle, "generated-profile.toml"), "w", encoding="utf-8") as fh:
        fh.write(profile_toml)

    if dry_run:
        plan = {
            "dry_run": True,
            "argv": argv_out,
            "binary": binary_provenance(resolve_version=False),
            "cwd": params["cwd"],
            "generated_profile": {
                "would_write": f"$CODEX_HOME/{profile_name}.config.toml",
                "content": profile_toml,
            },
            "prompt_from": instructions,
            "timeout_s": params["timeout_s"],
        }
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    with open(instructions, encoding="utf-8") as fh:
        prompt = fh.read()

    # The profile file must live in $CODEX_HOME — the only place --profile
    # reads from. Uniquely named per spawn, removed in the finally below; a
    # hard crash can orphan one (harmless, identifiable by the codex-p- prefix).
    home = codex_home()
    if not os.path.isdir(home):
        return refuse(
            bundle, f"CODEX_HOME not found at {home} (codex is not configured here)"
        )
    profile_path = os.path.join(home, f"{profile_name}.config.toml")

    binary = binary_provenance(resolve_version=True)
    started = utcnow()
    t0 = time.monotonic()
    with open(profile_path, "w", encoding="utf-8") as fh:
        fh.write(profile_toml)
    timed_out = False
    interrupted: int | None = None
    try:
        proc = subprocess.Popen(
            argv_out,
            cwd=params["cwd"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        # The worker runs in its own session, so a signal to this launcher's
        # process group (the harness's operator stop) never reaches it:
        # forward SIGTERM/SIGINT to the worker's group, then report — never
        # orphan a session that keeps spending quota.
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, _raise_interrupted)
        try:
            out, errout = proc.communicate(input=prompt, timeout=params["timeout_s"])
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
    finally:
        try:
            os.remove(profile_path)
        except OSError:
            pass

    # Raw JSONL events are the debugging/smoke record; keep them verbatim.
    with open(os.path.join(bundle, "events.jsonl"), "w", encoding="utf-8") as fh:
        fh.write(out or "")

    usage, is_error = parse_events(out or "")
    final_message = None
    if os.path.isfile(last_message_path):
        with open(last_message_path, encoding="utf-8") as fh:
            final_message = fh.read()
    with open(os.path.join(bundle, "transcript.txt"), "w", encoding="utf-8") as fh:
        if final_message is not None:
            fh.write(final_message)
        else:
            # no final message captured: keep the raw streams so nothing is lost
            fh.write((out or "") + (f"\n--- stderr ---\n{errout}" if errout else ""))

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
        # failure (environment vs solution — e.g. a usage limit).
        payload["error_summary"] = (
            f"interrupted by signal {interrupted}; worker process group terminated"
            if interrupted is not None
            else (final_message or "").strip()[:300]
            or (errout or "").strip()[-300:]
            or (out or "").strip()[-300:]
        )
    write_result(bundle, payload)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
