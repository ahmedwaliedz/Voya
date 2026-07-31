# VOYA Review Context

This file is the authoritative review router for review sessions in the VOYA project. Use it to classify the review and select the correct guard instead of re-reading the whole `.cursor` tree.

## Review-only default

- Reviews do not edit files unless fixes are explicitly authorized.
- Reviews do not commit, tag, push, install packages, or rewrite history.
- Findings come before summaries.

## Review categories

| Category | Scope |
|----------|-------|
| Production frontend | HTML, CSS, JavaScript, interactions, menu/cart/WhatsApp flows |
| Visual and responsive | Desktop and mobile layout, branding, illustration consistency, animation |
| Documentation | Phase plans, phase reports, baseline documents, README and other markdown |
| Assets | Images, illustration layers, optimization, format suitability |
| Mixed | Combine only the relevant checks from the above categories |

## Guard routing

- Phase 2 implementation or review: use `.cursor/skills/voya-illustration-layer-prep/SKILL.md`.
- Phases 3-8 implementation or review: use `.cursor/skills/voya-scroll-story-animation/SKILL.md`.
- Production frontend and visual/responsive changes: use `.cursor/skills/voya-frontend-guard/SKILL.md` only when HTML, CSS, JavaScript, loading, layout, or browser behavior changed.
- Documentation changes: use `.cursor/skills/voya-docs-guard/SKILL.md` only when docs or evidence claims changed.
- Assets: phase skill first, then frontend guard for technical checks plus docs guard when asset claims are documented.
- Mixed: run each applicable guard against the files it governs.
- Load `.cursor/rules/voya-project-rules.mdc` for every review.
- Read `.cursor/context/VOYA_REVIEW_CONTEXT.md` first; do not open deeper files unless the changed area matches.

## Required review process

1. Identify the phase and its intended acceptance criteria.
2. Select the phase skill for the current phase.
3. Identify the comparison reference.
4. Inspect Git status and the exact diff (unstaged and staged).
5. Confirm changed files are within phase scope.
6. Choose only the guards that match the changed files.
7. Inspect complete affected flows, not only isolated lines.
8. Run relevant non-destructive checks.
9. Compare implementation with baseline screenshots when visual behavior changed.
10. Report findings by severity.
11. Include exact file paths and line numbers.
12. Label inference as `[inference]`.
13. List testing gaps and residual risks.
14. Give a final decision:
    - `Approved`
    - `Minor changes required`
    - `Changes required`

## Comparison reference warning

Do not assume that `baseline/pre-implementation` is the correct comparison for every later phase. Use the phase-start commit, tag, or user-provided reference when one is available. `baseline/pre-implementation` is the Phase 0 checkpoint and is correct only for phases that compare against the original implementation.

## Evidence requirements

- Every finding must cite the exact file path and line number.
- Do not reference files, functions, or assets that do not exist in the repository.
- Label inference-based findings as `[inference]`.
- Verify claims against actual source files and Git data.
- Never treat planned behavior as implemented behavior.
- State clearly when no findings are discovered.

## Prompt style for fixes

```text
Fix [problem] in [file(s)].

Constraints:
- Make the smallest in-scope change for the current phase.
- Preserve existing menu, cart, WhatsApp, and navigation behavior.
- Do not touch unrelated files.
- Rerun the applicable guard after the fix.

Expected result:
- [clear success condition]
```
