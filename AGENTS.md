# Agent Skills (OpenCode)

This project uses the production-grade engineering skills from
[addyosmani/agent-skills](https://github.com/addyosmani/agent-skills), installed under
`.agents/skills/`.

## Core Rules

- If a task matches a skill, invoke it with the `skill` tool before acting.
- Skills are located in `.agents/skills/<skill-name>/SKILL.md`.
- Follow the skill workflow strictly; do not partially apply it.
- Never skip required steps such as spec, plan, or test when a skill demands them.

## Intent → Skill Mapping

Map the user's intent to the matching skill automatically:

- New feature / new functionality → `spec-driven-development`, then `incremental-implementation` and `test-driven-development`
- Planning / task breakdown → `planning-and-task-breakdown`
- Bug / failure / unexpected behavior → `debugging-and-error-recovery`
- Code review → `code-review-and-quality`
- Refactoring / simplification → `code-simplification`
- API or interface design → `api-and-interface-design`
- UI work → `frontend-ui-engineering`
- Security / auth / data handling → `security-and-hardening`
- Performance → `performance-optimization`
- Observability / logging / alerting → `observability-and-instrumentation`

## Execution Model

For every request:

1. Determine if any skill applies (even a small chance).
2. Load the skill with the `skill` tool (e.g. `skill({ name: "<skill-name>" })`).
3. Follow the skill workflow exactly.
4. Only proceed to implementation once required steps are complete.

## Notes

- The slash commands (`/spec`, `/plan`, `/build`, `/test`, `/review`, `/ship`) map to skills
  and are invoked through the same workflow — use the namespaced form
  (`agent-skills:<command>` style) where a built-in command name collides.
- The `addyosmani/agent-skills` repository's own root `AGENTS.md`/`CLAUDE.md` are repo-scoped
  for contributors and should not be copied into this project.
- Skills referencing shared checklists under `references/` are self-contained per-skill
  installs; whole-pack installs include the shared references.
