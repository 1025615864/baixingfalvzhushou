# Skill Loading Limits

## Goal
Ensure each turn loads only the minimum required skills. Never read all skills in bulk.

## Mandatory Rules
1. No full-scan behavior.
Do not enumerate or open every skill folder or every `SKILL.md` file in one turn.

2. Trigger-based loading only.
Load a skill only when:
- the user explicitly names it, or
- the current task clearly matches the skill description.

3. Minimal skill set first.
Default to:
- at most 1 process skill, and
- at most 1 domain skill.
Hard cap: no more than 3 `SKILL.md` files per turn unless the user explicitly asks for broader comparison.

4. Progressive disclosure.
Read only the minimum part of each `SKILL.md` needed to execute the task. Open referenced files only when the current step truly requires them.

5. No recursive reference expansion.
If a skill points to `references/` or `scripts/`, do not bulk-read that directory. Open only the exact file required for the next action.

6. Announce chosen skills briefly.
Before implementation, state which skill(s) are being used and why (one short line).

7. Fallback without broad scanning.
If a requested skill is missing/unreadable, state it briefly and continue with the best local fallback. Do not scan unrelated skills.

## Turn Checklist
- Is there a clear trigger for each loaded skill?
- Is the loaded set minimal (usually 1-2 skills)?
- Did we avoid bulk directory reads?
- Did we read only required sections/files?
