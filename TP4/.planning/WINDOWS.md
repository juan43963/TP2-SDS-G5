---
schema_version: 1
open_count: 1
waived_count: 0
fixed_count: 0
total_count: 1
last_updated: 2026-10-03T18:12:43.150Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 06 | unrun-verify | presentacion/presentacion.tex |  | 06-03: deck never compiled (no pdflatex on this Mac); layout overflow unchecked until plan 06-04 on MiKTeX | open |  | 2026-10-03T18:12:43.150Z |  |

````json
[
  {
    "id": 1,
    "kind": "unrun-verify",
    "phase": "06",
    "file": "presentacion/presentacion.tex",
    "line": null,
    "description": "06-03: deck never compiled (no pdflatex on this Mac); layout overflow unchecked until plan 06-04 on MiKTeX",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-03T18:12:43.150Z",
    "resolved_at": null,
    "milestone": null
  }
]
````
