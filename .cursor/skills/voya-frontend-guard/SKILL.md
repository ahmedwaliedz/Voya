---
name: voya-frontend-guard
description: Review changed VOYA frontend work (HTML, CSS, JavaScript, interactions, responsive behavior, accessibility, animation, and frontend performance) after implementation or during review. Supports review-only, guard-pass, and live modes.
---

# voya-frontend-guard

Review changed VOYA frontend code and interactions. This guard complements the VOYA project rules; it does not replace manual testing, security review, or browser verification.

## When to use

- After implementing or changing frontend code in a VOYA phase.
- Before marking a frontend phase as complete.
- During review when HTML, CSS, JavaScript, assets, or animation are in scope.
- Before commit or push as part of the pre-Git review.

## Operating modes

- **review-only** — Default for reviews. Report findings without editing. Never edit files unless fixes are explicitly authorized.
- **guard-pass** — After authorized implementation, fix only confirmed in-scope issues and rerun verification. Do not fix unrelated pre-existing issues. Repeat up to two correction cycles, then report.
- **live** — Provide checks while code is being written, then perform a final guard pass before delivery.

## Baseline

Load before every review:

- `../../rules/voya-project-rules.mdc`
- `../../context/VOYA_REVIEW_CONTEXT.md`

## Required checks

### Correctness

- No JavaScript runtime or syntax errors.
- Menu, category switching, cart, quantities, removal, totals, and WhatsApp ordering still work.
- Rapid Papa, Mama, and Voya switching cannot render stale content.
- Latest selection wins.
- Reverse scrolling restores the correct scene state when scroll animation exists.

### Accessibility

- Keyboard navigation.
- Visible focus.
- Semantic controls.
- Alternative text.
- Contrast and readability.
- Reduced-motion fallback.

### Responsive and visual

- Desktop viewport: `1440x900`.
- Mobile viewport: `390x844`.
- No overflow, clipping, overlap, or unreadable text.
- Brand colors and illustrations remain consistent.
- Compare with baseline screenshots when appropriate.

### Performance

- Large image and asset review.
- Lazy loading where safe.
- Layout shift risk.
- Scroll jank.
- Avoid animating layout-heavy properties when transforms are sufficient.
- No unnecessary dependencies.

### Maintainability

- Minimal phase-scoped changes.
- Clear names and focused functions.
- No duplicated state.
- No debug code or dead experiments.
- No speculative abstractions.

## Evidence standard

Every finding must contain:

- Severity: critical, high, medium, or low.
- Exact file and line.
- Observed evidence.
- User impact.
- Minimal recommended fix.
- Verification required after the fix.

## Reporting

- Findings come first, ordered by severity.
- Label inference-based findings as `[inference]`.
- List testing gaps and residual risks.
- If no findings remain, state so explicitly.
