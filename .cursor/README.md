# VOYA Cursor Agent Package

Project-specific agent guidance for the VOYA static frontend (`index.html`, `style.css`, `script.js`, assets, and documentation). This package was adapted from a Laravel reference package with all Laravel, PHP, Blade, database, API, RBAC, and backend-specific instructions intentionally excluded.

## Purpose

Keep VOYA implementation safe and verifiable across phased work:

- Safe frontend implementation that preserves brand and behavior.
- Phase-by-phase validation against the approved plan.
- Documentation verification against the real implementation and Git data.
- Full pre-Git review before commit or push.
- Evidence-based review reports.

## Package files

| File | Role |
|------|------|
| `.cursor/rules/voya-project-rules.mdc` | Always-relevant project rules: scope control, brand protection, frontend quality, accessibility, responsive behavior, performance, security. |
| `.cursor/context/VOYA_REVIEW_CONTEXT.md` | Authoritative review router: categories, required process, evidence standard, final decisions. |
| `.cursor/skills/voya-frontend-guard/SKILL.md` | Guard for changed HTML, CSS, JavaScript, interactions, responsive behavior, accessibility, animation, and performance. |
| `.cursor/skills/voya-docs-guard/SKILL.md` | Guard that verifies phase reports, plans, baseline documents, and claims against actual implementation and Git data. |
| `.cursor/prompt-library/VOYA_PRE_GIT_REVIEW_PROMPT.md` | Reusable strict prompt for a full pre-Git review before commit or push. |

## When to use each guard

- **voya-frontend-guard**: after implementing or changing frontend code, before marking a phase complete, and during any review that touches HTML, CSS, or JavaScript.
- **voya-docs-guard**: when phase reports, plans, baseline documents, or README claims are created or changed.
- **Pre-Git review prompt**: before committing or pushing a completed phase.

## Implementation mode vs review-only mode

- **Implementation mode**: the user has authorized changes for the current phase. You may edit in-scope files, then run the relevant guard to verify.
- **Review-only mode (default for reviews)**: report findings only. Do not edit files, commit, tag, push, install packages, or rewrite history unless the user explicitly authorizes it.

## Pre-Git review rules

The pre-Git review prompt must not edit, commit, tag, or push anything unless explicitly authorized. It reports what will be committed or pushed and lets the user decide.

## Usage examples

Review a completed phase:

```text
Run voya-frontend-guard in review-only mode on the current phase.
Read .cursor/context/VOYA_REVIEW_CONTEXT.md first, then review the phase diff.
```

Review before Git push:

```text
Run the pre-Git review using .cursor/prompt-library/VOYA_PRE_GIT_REVIEW_PROMPT.md.
Report findings ordered by severity and the final decision without committing or pushing.
```
