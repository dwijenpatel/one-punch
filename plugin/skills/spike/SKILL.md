---
name: spike
description: "Settle a question about how an external system actually behaves — a framework default, an API's real response shape, a library seam, path or exception semantics — by writing and executing throwaway code, then recording a probe transcript (command, trimmed output, versions, date) on the decision ticket that asked. Use when a decision or contract sentence rests on unverified external behavior, when a review converts a mechanism claim to a spike, or when two plausible readings of a system can be discriminated by running something small. Fact-finding by execution; for reaction-seeking artifacts (does this design feel right?) use a prototype skill instead."
---

# spike — execute the question

A spike is **throwaway code that discriminates between readings of an external
system**. Its output is not the code — it is a **probe transcript** and the decision it
unblocks. The one rule that gives this skill its authority: *a claim about how an
external system behaves enters a contract only via a spike transcript.* (Measured, four
review rounds on one plan: confidently asserted external behavior was wrong at a very
high rate, and every instrument except execution was blind to it.)

Sibling: a **prototype** raises the fidelity of a *discussion* — a human reacts to it.
A spike establishes a *fact* — nobody needs to be in the loop while it runs. If the
question is "does this feel right?", use the prototype skill; if it is "what is true?",
spike it.

## Rules

1. **Smallest program that discriminates.** State the two (or more) candidate readings
   first; the spike exists to kill all but one. If you cannot name the readings, the
   question isn't sharp enough to spike yet — sharpen it first.
2. **Run against the installed reality** — the resolved version of the library, the
   real API, the actual filesystem semantics. Pin and record versions; a transcript is
   true of one version at one moment.
3. **Isolate scenarios.** One host, fixture, or account per question — shared state
   between scenarios has produced confounded probes that "disproved" true claims.
   When a spike's result surprises you, first suspect the spike.
4. **The transcript is the deliverable:** the command, the trimmed output, versions,
   and the date — enough for a stranger to re-run it. Post it on the decision ticket
   (or wherever this effort records decisions) with a one-line verdict: which reading
   survived.
5. **Throwaway means throwaway.** Park the code on a scratch branch or let the
   transcript stand alone; it never lands on main and never grows tests. If the spike
   keeps growing because "it's basically the implementation now," stop — that is a
   build ticket wearing a spike's clothes; say so and re-ticket it.
6. **Transcripts feed contracts verbatim-or-cited.** A contract sentence resting on a
   spike names it; a code snippet may be inlined only if it is the spike's own text,
   trimmed to the decision-rich part.
