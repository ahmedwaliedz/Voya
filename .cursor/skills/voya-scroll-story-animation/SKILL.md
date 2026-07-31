---
name: voya-scroll-story-animation
description: Implement and review VOYA Phases 3-8 scroll-story scenes with GSAP and ScrollTrigger while keeping the layered 2D approach.
---

# VOYA Scroll Story Animation

Use this skill for Phase 3 through Phase 8.

## Boundaries

- Reuse GSAP and ScrollTrigger. Do not add Three.js or another animation stack.
- Keep characters as layered 2D artwork.
- Simulate depth with transforms, perspective, scale, shadow, opacity, and restrained parallax.
- Preserve native scrolling.
- Keep menus semantic and keep menu, cart, and order data in the current source of truth.
- Make animation progressive enhancement only.

## Scene rules

1. Use one reversible GSAP timeline per scene.
2. Scope selectors and temporary styles to the scene root.
3. Define start and end states so reverse scroll restores the authored scene.
4. Keep each trigger and cleanup hook together.
5. Kill stale timelines, triggers, listeners, and temporary styles before rebuilds.
6. Rebuild only when responsive assumptions change; otherwise refresh measurements.
7. Refresh after fonts or assets settle.
8. Avoid duplicate triggers on resize or repeated init.

## Phase gates

- Phase 3: pinning, reveal, reverse scroll, resize, cleanup, and HTML menu usability.
- Phase 4: Papa as the reference for pacing, plate tilt, ingredient count, menu reveal, mobile, and reduced motion.
- Do not implement Mama until Papa is reviewed and accepted.
- Phase 5: reuse the accepted framework for Mama with a distinct action.
- Phase 6: Coffee and House scenes with no repeat of Papa's falling-plate motion.
- Phase 7: simplify mobile and reduced motion without blocking menu access.
- Phase 8: remove unused work and finish performance and browser QA.

## Motion and accessibility

- Build a short mobile version with less travel and less pinning where needed.
- Recalculate trigger positions after breakpoint and orientation changes.
- Keep controls visible and usable during pinned and reversing states.
- Respect `prefers-reduced-motion`.
- Hide decorative layers from assistive tech.

## Verification

Test at `1440x900` and `390x844`.
Check forward, reverse, skipped-section scrolling, resize, orientation change, menu switching, cart totals, WhatsApp ordering, keyboard, touch, reduced motion, and console errors.
Record browser, viewport, motion preference, paths, screenshots or recordings, and limitations.

## Routing

- Use `voya-frontend-guard` for HTML, CSS, JavaScript, layout, loading, browser behavior, semantics, menu/cart/order regressions, and performance.
- Use `voya-docs-guard` for phase reports, plans, evidence claims, and Git facts.
- This skill owns scene choreography, lifecycle, reverse-scroll behavior, and phase-specific motion gates.

## Decision

Return `Accepted`, `Accepted with minor notes`, `Changes required`, or `Incomplete`.
