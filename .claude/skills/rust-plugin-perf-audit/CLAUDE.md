# rust-plugin-perf-audit

Skill for auditing and fixing server performance in an Oxide Rust plugin, with every cost proved from decompiled game and Oxide code.

- `SKILL.md` is the entry point (trigger, decompiled facts, workflow, the five patterns, checklist, verification). Read it first.

Rules:
- Keep `SKILL.md` as the single source of truth. Do not duplicate its content here.
- Keep it generic: no plugin, class, or field names from any one plugin. The examples came from EventCtf with the names made neutral.
- Add a pattern only from a finding that was verified by reading the implementation, and only with code that compiled.
- When the DLLs in `e:\Rust\Plugins\Oxide\` are updated, re-check "What the code does not tell you" first; the patterns follow from it.
- CUI send and destroy cost belongs to `cui-partial-refresh-audit`. Link to it, do not repeat it.
- Finish an audit by opening the before/after diff in the user's IDE (see the plugin `AGENTS.md` Change review rule).
