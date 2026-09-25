#!/usr/bin/env python3
"""grok_p — PLACEHOLDER launcher for grok CLI workers. Refuses all launches.

No probed facts exist for the grok CLI on this host: headless invocation
shape and usage/limit reporting are unknown. Per the launcher contract,
unknown means REFUSE — never launch on guesses. The smoke procedure below
converts this stub into a real launcher.

Smoke-first procedure (record dated, build-pinned results in the vendor
compatibility checklist before editing this file into a real launcher):
1. Headless invocation: does the CLI accept a one-shot prompt + auto-approve?
   Exit codes? Machine-readable output/usage?
2. Hygiene: can ambient user configuration (hooks, MCP servers, memory) be
   kept away from the worker? Probe it the way claude_p's flags were probed.
3. Limits: what does hitting the plan's usage window look like (error string,
   exit code)? The governor needs to classify it as a LimitHit with a cooldown.
4. Stop: does SIGTERM to the CLI's process group end the session? Then, and
   only then, write build_argv here, following claude_p.py's shape (empty
   isolation intent, stop forwarding, provenance, usage parsing).
"""

import json
import os
import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    bundle = os.path.abspath(args[0]) if args else "."
    reason = (
        "grok_p is a smoke-first placeholder: no probed facts for the grok CLI "
        "on this host (invocation, hygiene, limits). Run the smoke procedure "
        "in this file's docstring and record results before first real use."
    )
    try:
        with open(os.path.join(bundle, "result.json"), "w", encoding="utf-8") as fh:
            json.dump({"contract": 1, "ok": False, "exit": None, "refused_reason": reason}, fh, indent=2)
            fh.write("\n")
    except OSError:
        pass
    print(f"refused: {reason}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
