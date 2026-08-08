#!/usr/bin/env python3
"""grok_p — PLACEHOLDER launcher for grok CLI workers. Refuses all launches.

No probed facts exist for the grok CLI on this host: headless invocation
shape, usage/limit reporting, and isolation mechanisms are all unknown.
Per the launcher contract, unknown means REFUSE — never launch unwalled on
guesses. The smoke procedure below converts this stub into a real launcher.

Smoke-first procedure (record dated, build-pinned results in the vendor
compatibility checklist before editing this file into a real launcher):
1. Headless invocation: does the CLI accept a one-shot prompt + auto-approve?
   Exit codes? Machine-readable output/usage?
2. Isolation: any native sandbox? If none (the expected case), the wall is a
   CONTAINER: run the worker inside a container with the workspace mounted and
   nothing else — deny_read intent is then expressed by the mount set, network
   intent by the container's network config. Probe both.
3. Limits: what does hitting the plan's usage window look like (error string,
   exit code)? The governor needs to classify it as a LimitHit with a cooldown.
4. Walls probe: from inside the worker, attempt reads outside the mount and a
   network call that policy denies; both must fail. Then and only then, write
   build_argv/build_settings here, following claude_p.py's shape.
"""

import json
import os
import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    bundle = os.path.abspath(args[0]) if args else "."
    reason = (
        "grok_p is a smoke-first placeholder: no probed facts for the grok CLI "
        "on this host (invocation, limits, isolation). Run the smoke procedure "
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
