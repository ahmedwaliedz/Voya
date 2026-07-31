---
name: voya-docs-guard
description: Verify VOYA documentation (phase reports, plans, baseline documents, README) against the actual implementation and Git data. Trigger when documentation is created or changed, or when documented behavior may have drifted from the implementation.
---

# voya-docs-guard

Verify VOYA documentation against actual project sources. Detect documentation drift, unverifiable claims, broken links, and incorrect file or asset references.

## When to use

- After adding or changing phase reports, plans, baseline documents, README, or other markdown.
- When documented behavior may no longer match implementation.
- During review when documentation is part of the diff.
- During the pre-Git review for any documentation changes.

## What to verify

- Phase reports against the actual Git diff.
- Acceptance criteria against actual behavior.
- File and asset paths.
- Screenshot existence and viewport sizes.
- Commit and tag claims using actual Git data.
- Runtime-error claims against available logs.
- Product names and brand claims against approved VOYA content.
- Documentation links.
- UTF-8 encoding.
- No unsupported claims such as "completed", "tested", or "approved" without evidence.

## Key principle

Never treat planned behavior as implemented behavior.

## Baseline

Load before every review:

- `../../context/VOYA_REVIEW_CONTEXT.md`
- `../../rules/voya-project-rules.mdc`

## Reporting

- Report findings by severity with exact evidence.
- If no findings remain, state so explicitly.

## Final result

- `Documentation approved`
- `Documentation needs correction`
