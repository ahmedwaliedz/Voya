# Phase 3 — Menu Story Framework

**Date:** 2026-08-01
**Phase skill:** `.cursor/skills/voya-scroll-story-animation/SKILL.md`
**Phase start commit:** `d84f212` (HEAD of `main`)
**Phase scope:** shared scroll-scene framework only. No Papa / Mama / Voya / House artwork.
**Status:** Phase 3 implementation complete — ready for final external review. Phase 4 not started.

---

## 1. Goal

Build the shared scroll-scene structure once inside the existing `<section id="menu">`,
connect it to the real menu below, and prove the framework is reusable. No final character
animation, no Papa ingredients, no scene-specific artwork.

## 2. Files changed

| File | Type | Note |
|------|------|------|
| `index.html` | modified | +2 / -1 lines on the Skip link and `.menu-header`. Added the decorative `.p3-menu-story` stage as the first child of `#menu`. No existing markup changed. |
| `style.css` | modified | Phase 3 `.p3-*` block, two hide media queries, plus the new `scroll-margin-top` rules for the fixed-header offset. No existing rules changed. |
| `script.js` | modified | `initMenuStoryFramework()`, the `p3MenuStory` module state, and the Skip-link + reduced-motion update inside the existing `setupSmoothScroll()`. No other functions changed. |
| `docs/phase3/PHASE_3_MENU_STORY_FRAMEWORK.md` | new | this document |
| `docs/phase3/capture-evidence.mjs` | new | hardened Playwright evidence capture (readiness, assertions, non-zero exit) |
| `docs/phase3/evidence/browser/*.png` | new | 6 PNGs from the final successful run |
| `docs/VOYA_IMPLEMENTATION_PLAN_EN.md` | modified | Phase 3 row set to `Ready for review` only |

## 3. Protected scope — unchanged

- `assets/**` — untouched (temporary + scenes + images).
- `docs/phase2/**` — untouched (baselines, evidence, generators, verifiers).
- `AGENTS.md` — untouched.
- `.cursor/**` — untouched.
- `vendor/**` — untouched.
- `docs/baseline/package.json` (Phase 0 capture-tooling manifest) and
  `docs/baseline/node_modules/playwright` (the existing Playwright install used for
  evidence) — unchanged.
- No new npm packages. No Three.js, Playwright MCP, Context7, Semgrep, Laravel Boost,
  or any other framework.
- No staging, no commits, no pushes.

## 4. DOM additions (inside the existing `<section id="menu">`)

```html
<!-- Phase 3: shared menu-story framework (decorative; real menu stays in normal flow below) -->
<div class="p3-menu-story" id="p3MenuStory" aria-hidden="true" data-phase3-story>
  <div class="p3-stage">
    <div class="p3-frame">
      <div class="p3-group">
        <span class="p3-arm"></span>
        <span class="p3-plate"></span>
      </div>
    </div>
    <div class="p3-elements" aria-hidden="true">
      <span class="p3-el p3-el--1"></span>
      <span class="p3-el p3-el--2"></span>
      <span class="p3-el p3-el--3"></span>
      <span class="p3-el p3-el--4"></span>
      <span class="p3-el p3-el--5"></span>
    </div>
  </div>
</div>

...

<div class="menu-header reveal" id="menuContentStart" tabindex="-1">
  ...
</div>
```

- All `p3-*` selectors are scoped to the story root. No reusable class names were added
  to the existing menu tree.
- `aria-hidden="true"` is on the story root and the inner `.p3-elements` group. No
  essential content is in this tree.
- The story is the **first** child of `#menu`; everything that was already inside
  `#menu` is unchanged and still the real menu.
- The Skip link now targets the real menu header. The `.menu-header` carries
  `id="menuContentStart"` and `tabindex="-1"` so it can receive focus from the
  keyboard but is not in the natural tab order.

## 5. Controller and timeline structure

One new function: `initMenuStoryFramework()` in `script.js`. It is called once from
`initPageIntro`'s `onComplete`, right after `initScrollReveals()` and
`initHeroScrollParallax()`. It is skipped when `gsap` or `ScrollTrigger` are absent —
the stage is then hidden via CSS (mobile + reduced-motion) or the function returns early
(desktop without GSAP: the stage is visible but the timeline never starts; the real
menu is still the next sibling, so the page is usable).

The controller uses `gsap.matchMedia()` for two reasons:
1. Mobile and reduced-motion never enter the pinned branch (CSS hides the stage instead,
   so matchMedia correctly does not register the desktop branch at all).
2. Resize cycles are handled by matchMedia's own add/remove lifecycle; when the media
   condition stops matching, GSAP automatically reverts that matchMedia context and
   kills only the Phase 3 trigger and timeline, never the existing hero or
   scroll-reveal triggers.

```text
initMenuStoryFramework()
  └─ gsap.matchMedia()
       └─ add('(min-width: 769px) and (prefers-reduced-motion: no-preference)')
            └─ gsap.timeline({ scrollTrigger: { id: 'p3-menu-story', trigger: #p3MenuStory,
                                                start: 'top top', end: '+=80%',
                                                pin: true, pinSpacing: true,
                                                pinReparent: true,
                                                anticipatePin: 1, scrub: 0.5 } })
                 ├─ to(frame, { scale: 1, opacity: 1, duration: 0.12 }) @ 0       // entrance
                 ├─ to(group, { rotate: 7, duration: 0.26 }) @ 0.14               // arm tilt
                 ├─ to(plate, { rotate: -12, y: 4, duration: 0.26 }) @ 0.18         // plate tilt
                 ├─ to(elements, { opacity: 1, scale: 1, stagger: 0.015 }) @ 0.42  // release
                 ├─ to(elements, { x, y, stagger: 0.015 }) @ 0.46                  // drift
                 └─ to([frame, group, plate, elements], { opacity: 0, duration: 0.18 }) @ 0.82 // exit
```

- **One** GSAP timeline. **One** ScrollTrigger. **One** matchMedia. The id `p3-menu-story`
  is namespaced for Phase 3 so future phases can filter their own triggers.
- `pinReparent: true` is required because the menu section gets a leftover
  `transform: matrix(1,0,0,1,0,0)` from the existing `initScrollReveals` section-motion
  reveal, which would otherwise become the containing block for `position: fixed` and
  trap the pinned story above the viewport. Re-parenting the pinned element to `<body>`
  during the pin avoids this.
- The media callback itself does **not** currently return a cleanup function. GSAP
  automatically reverts the matchMedia context when its media condition stops
  matching (desktop → mobile / reduced-motion), which kills only the Phase 3
  timeline and the `p3-menu-story` ScrollTrigger.
- Separately, `p3MenuStory.revert` stores an explicit controller-level function that
  calls `mm.revert()` when `initMenuStoryFramework()` is invoked again. That path
  makes re-init idempotent; it is not the media-callback cleanup.
- Only the Phase 3 matchMedia context, timeline, and `p3-menu-story` ScrollTrigger
  are affected by either path.

## 6. Timeline sequence (single scrubbed timeline)

| Phase | Range | Effect |
|-------|-------|--------|
| Entrance | 0.00 – 0.12 | `.p3-frame` scales from 0.88 to 1 and fades to opacity 1. |
| Prototype motion | 0.14 – 0.40 | `.p3-group` rotates 7°, `.p3-plate` rotates -12° and shifts y 4px. |
| Decorative release | 0.42 – 0.50 | 5 `.p3-el` circles fade in and scale to 1 with a 15 ms stagger. |
| Drift | 0.46 – 0.74 | The 5 elements travel to (x, y) targets, each with its own vector. They exit the visible stage area toward the bottom, visually pointing toward the menu categories below. |
| Scene exit | 0.82 – 1.00 | Frame, group, plate and elements all fade to opacity 0. |

Progress is bound to scroll by `scrub: 0.5`. Reverse scroll restores the previous visual
state. Fast scroll does not leave a partially hidden or unusable menu because the
pin-spacer equals the pin distance, the menu-header follows the pin-spacer, and the
CSS keeps the menu content at full opacity regardless of timeline progress.

## 7. Pin duration

- Desktop: `end: '+=80%'` — the pin lasts 80 % of the viewport height (≈720 px on a
  900 px viewport). `pinSpacing: true` adds a pin-spacer of the same height so the
  document height matches the scroll height and there is no visible page jump.
- The story stage itself is `height: 100vh; min-height: 600px` so it fills the
  viewport on a 900 px screen and stays usable on a 700 px laptop. The 20 % gap
  between story height and pin distance is the natural handoff: the timeline reaches
  1.0 exactly when the pin ends, and the user lands at the `.menu-header` position.
- Mobile: no pin, no ScrollTrigger. The CSS hides the stage entirely.
- Reduced motion: same — no pin, no ScrollTrigger.

## 8. Desktop behavior (1440 x 900)

- The story pins the viewport for ≈720 px of scroll.
- Scene entrance: at scroll progress 0.10, the frame is visibly rendered and the
  arm / plate are in the early entrance state. Confirmed in
  `evidence/browser/01-desktop-scene-entrance.png`.
- Pinned prototype: at scroll progress 0.5, the prototype is mid-motion. Frame is
  centered, the arm has rotated, the plate is tilted, and the trigger is active with
  progress ≈ 0.45. Confirmed in
  `evidence/browser/02-desktop-pinned-prototype.png`.
- Menu revealed: after the pin releases, `.menu-header` is at the natural scroll
  position and the full real menu (header, flow, featured image, brand buttons, room
  intro) is visible and interactive. Confirmed in
  `evidence/browser/03-desktop-menu-revealed.png`.
- Reverse scroll: entrance and restored states are both measured at progress 0.10.
  The reverse scenario records the visual state at 0.10, advances to 0.70 (which must
  differ), then returns to 0.10 and compares trigger count/progress, frame/group/plate/
  element opacity + transform, header visibility, pinned position, and horizontal
  overflow within documented tolerances (progress ≤ 0.02, opacity ≤ 0.02, transform
  matrix component ≤ 0.1). Confirmed in
  `evidence/browser/06-desktop-reverse-restored.png`.
- Fast scroll: `scrub: 0.5` smooths the timeline so fast scroll cannot land between
  keyframes with a visible artifact; the menu content below is not affected.
- No horizontal overflow, no clipped menu / cart / heading / prototype.

## 9. Mobile behavior (390 x 844)

- `@media (max-width: 768px) { .p3-menu-story { display: none; } }` removes the
  stage from the layout. No pin-spacer is created because the desktop matchMedia
  branch is not entered.
- `scroll-margin-top: 100px` on `#menu` (and on `#menuContentStart`) clears the
  fixed mobile header so the menu heading "Your Table Awaits" is fully visible
  below it after navigating to `#menu`. Confirmed in
  `evidence/browser/04-mobile-menu-revealed.png` — the heading is no longer clipped.
- Runtime probe (final run): `stageDisplay: "none"`, `headerTop: 100`, `titleTop` ≥ 80,
  `triggerCount: 0`, no horizontal overflow.

## 10. Reduced motion (`prefers-reduced-motion: reduce`)

- `@media (prefers-reduced-motion: reduce) { .p3-menu-story { display: none; } }`
  removes the stage.
- The desktop matchMedia condition includes
  `(prefers-reduced-motion: no-preference)`, so the pinned branch is never
  registered when reduced motion is active — there is no pin, no timeline, no
  ScrollTrigger.
- The full real menu is visible immediately on `#menu`. `scroll-margin-top: 110px`
  on `#menuContentStart` keeps the heading below the fixed header. Confirmed in
  `evidence/browser/05-reduced-motion-menu-visible.png`.
- Runtime probe: `stageDisplay: "none"`, `triggerCount: 0`, `headerTop` in [80, 110],
  `titleTop` ≥ 80, no horizontal overflow.

## 11. Resize and lifecycle

- `gsap.matchMedia()` owns the desktop branch. Resize desktop → mobile stops the
  media condition from matching; GSAP automatically reverts that matchMedia context
  and kills the Phase 3 trigger and timeline only. Existing hero and reveal
  triggers are not affected. The media callback does not return a cleanup function.
- `p3MenuStory.revert` is a controller-level function that calls `mm.revert()` when
  `initMenuStoryFramework()` runs again (defensive re-init). It is not used as the
  media-query leave path.
- Resize mobile → desktop re-registers the desktop branch, creating a new timeline
  and a new `p3-menu-story` ScrollTrigger. The re-registration is automatic.
- Confirmed by the hardened capture script: `initial: 1` desktop trigger →
  `afterMobile: 0` triggers (mobile matchMedia dropped the desktop branch) →
  `afterDesktopAgain: 1` trigger (desktop matchMedia re-added it). No duplicates.
- `ScrollTrigger.refresh()` is not called manually; matchMedia handles it.

## 12. State safety — menu and cart regression

- No cart, brand, category, or product code was changed. The story stage is a
  sibling of the real menu inside `#menu`; it does not touch the menu data flow.
- The latest `currentBrand` wins during rapid switching (Phase 1 behavior, preserved
  by the existing `beginMenuTransition()` generation counter). Confirmed:
  rapid `voya → mama → papa` ends on Papa (`finalName: "The Healthy Room"`).
- Add-to-cart, cart count, cart drawer open/close, WhatsApp button enabled state:
  all confirmed at runtime (`cartCount: 1`, `whatsappDisabled: false`,
  `cartOpen: true`).
- Cart contents survive a full resize cycle (desktop → mobile → desktop) — the
  hardened regression probe asserts `cartAfterResize === cartAfter`.
- Cart contents are not reset on scene init or rebuild. The story stage is built
  once on page intro and never touches the cart array.

## 13. Accessible Skip link

The Skip link (`<a href="#menuContentStart" class="skip-link">Skip to menu</a>`)
bypasses the decorative Phase 3 stage and moves keyboard focus directly to the
real `.menu-header` (which carries `id="menuContentStart" tabindex="-1"`).

- Normal navigation links (header "Menu", Mood "Explore Coffee / Healthy /
  Comfort", hero "Explore Menu") still target `#menu`, so on desktop the user
  enters the story framework; on mobile / reduced-motion the user lands on the
  real menu.
- The existing `setupSmoothScroll()` handler detects the Skip link via its
  `.skip-link` class: it scrolls to the real target, then calls
  `t.focus({ preventScroll: true })` to move keyboard focus to the menu header
  without a second scroll.
- Under `prefers-reduced-motion: reduce` the handler uses `scrollIntoView({
  behavior: 'auto' })`, so the CSS `scroll-behavior: auto !important` override
  yields instant navigation. The focus call still runs.
- No new global click listener was added — the existing handler carries the
  Skip-link branch.

## 14. Fixed-header anchor offset

Implemented as CSS-only via `scroll-margin-top` (no JS scroll math):

```css
#menuContentStart { scroll-margin-top: 110px; }
@media (max-width: 768px) {
    #menu { scroll-margin-top: 100px; }
    #menuContentStart { scroll-margin-top: 100px; }
}
```

- Desktop fixed header is ~97 px tall → `110px` clears it with a small buffer.
- Mobile fixed header is ~80 px tall → `100px` clears it.
- On mobile, `#menu` also gets the offset because the Phase 3 stage is hidden
  and `#menu` lands directly on the menu-header.
- On desktop, `#menu` intentionally has **no** `scroll-margin-top` so normal
  `#menu` navigation still enters the Phase 3 story framework, as required.
- `scroll-margin-top` is respected by both `scrollIntoView()` and by the
  browser's native anchor navigation (`<a href="#…">`).

## 15. Verification — static checks

All run with the project's existing tooling, no installs.

| Check | Result |
|-------|--------|
| `node -c script.js` | exit 0 |
| `node --check docs/phase2/capture-evidence.mjs` | exit 0 |
| `node --check docs/phase3/capture-evidence.mjs` | exit 0 |
| `node docs/phase3/capture-evidence.mjs` | exit 0 (all assertions passed, zero browser errors) |
| `git diff --check` | no whitespace-only errors (only the standard LF→CRLF warnings) |
| `git status` (after changes) | only `index.html`, `script.js`, `style.css` modified, plus the untracked `docs/phase3/` tree |
| `git diff --name-only -- docs/phase2 assets AGENTS.md .cursor vendor` | empty (protected scope intact) |
| Duplicate IDs in `index.html` | none (`#menuContentStart` is the only added id) |
| Internal link targets (`href="#…"`) | all resolve; `#menuContentStart` is the new Skip target |
| `#menuContentStart` is focusable | yes — `tabindex="-1"` on the `.menu-header` |
| Skip link bypasses the decorative scene | yes — Skip targets `#menuContentStart` (the real header), not `#menu` |
| Normal `Menu` / `Explore` links still enter `#menu` | yes — all 13 `href="#…"` anchors other than the Skip link still target `#menu` / `#story` / `#moods` / `#locations` / `#contact` |
| Desktop trigger count | 1 |
| Mobile trigger count | 0 |
| Reduced-motion trigger count | 0 |
| Resize trigger sequence | 1 → 0 → 1 |
| `TODO` / `FIXME` / `XXX` / `console.log` / `debugger` in production files | only the 2 pre-existing location-card TODOs from Phase 0; none added by Phase 3 |
| Valid UTF-8 / no mojibake | clean |
| Temporary / debug files in repo root | none |
| Phase 2 files unchanged | confirmed (`docs/phase2/**` last touched at `209b05a`) |
| Assets unchanged | confirmed |
| Dependencies unchanged | confirmed (no `package.json` at project root; `docs/baseline/node_modules/playwright` reused) |
| Nothing staged, committed, or pushed | confirmed by `git status` (no staged changes) |

## 16. Verification — browser evidence (hardened capture)

Captured with the existing Playwright install at
`docs/baseline/node_modules/playwright`. Static HTTP server on port 8770, the same
shape as `docs/baseline/capture-screenshots.mjs` (no install, no new dependency).

Script: `docs/phase3/capture-evidence.mjs`. Output: `docs/phase3/evidence/browser/`.

### Readiness

`waitForReady(page)` throws (non-zero exit) if any of the following are not true
within 12 s of page load:
- `body.is-loaded` and `body.transition-done` are present.
- `#p3MenuStory`, `#menuContentStart`, `.p3-frame`, and `#menu .menu-header` are
  attached to the DOM (`state: 'attached'` is used for the decorative elements
  that are `display: none` on mobile / reduced-motion).
- A 600 ms settle follows for `ScrollTrigger.refresh()` after the intro reveal.

The `.catch(() => {})` that silently swallowed timeouts was removed.

### Per-scenario assertions

Every scenario runs `assert(name, condition, detail)` and pushes the result into
a global `assertions` array. A failure sets `allPassed = false`; the final report
includes the full list.

| Scenario | Assertions |
|----------|-----------|
| `desktop-entrance` | stage exists, stage is `display: flex`, frame exists, frame opacity > 0.5, exactly 1 `p3-menu-story` trigger, no horizontal overflow |
| `desktop-pinned` | exactly 1 trigger, trigger active, trigger progress within ±0.1 of 0.5, story is `position: fixed`, frame visible, no horizontal overflow |
| `desktop-menu` | menu header visible below the fixed header (`headerTop` in [0, 120]), pin no longer blocking, brand / rail / cart controls present, no horizontal overflow |
| `mobile-menu` | stage `display: none`, 0 triggers, menu header below the fixed header, heading not clipped (`titleTop` ≥ 80), no horizontal overflow |
| `reduced-motion` | stage `display: none`, 0 triggers, real menu header below the fixed header, heading not clipped, no decorative prototype rendered, no horizontal overflow |
| `desktop-reverse` | same progress 0.10 for entrance and restored states; forward 0.70 differs; restored matches entrance within tolerances (progress ≤ 0.02, opacity ≤ 0.02, transform ≤ 0.1); exactly 1 trigger; no duplicate/stuck pin; header visible; no horizontal overflow |
| `desktop-resize` | 1 → 0 → 1 trigger sequence |
| `menu-regression` | papa brand name set, latest rapid brand selection wins, category UI present, add-to-cart increases count, cart drawer opens, WhatsApp enabled with items, cart survives resize cycle |

### Browser errors

`pageerror`, `console.error`, and `requestfailed` are collected per page. Any
captured event sets `allPassed = false`. There is no broad external-resource ignore
list. The evidence runner installs one shared Playwright route that fulfills only
the known `fonts.googleapis.com/css2` stylesheet with HTTP 200 + empty CSS so
offline review environments do not fail on the production Google Fonts link; the
intentionally fulfilled request is not counted as an error. All other failures
remain fatal. The report includes a `googleFontsRoute` result confirming the route
was installed.

### Exit behavior

```text
exit 0  every scenario passed AND errors is empty
exit 1  any assertion failed, any browser error recorded, readiness failure,
       or any unexpected exception during capture
```

### Regenerated screenshots

| File | Viewport | Motion | State |
|------|----------|--------|-------|
| `01-desktop-scene-entrance.png` | 1440 x 900 | normal | scroll progress 0.10 — frame visible, early entrance state |
| `02-desktop-pinned-prototype.png` | 1440 x 900 | normal | scroll progress 0.5 — frame centered, mid-timeline |
| `03-desktop-menu-revealed.png` | 1440 x 900 | normal | `#menuContentStart` below fixed header — real menu heading fully visible |
| `04-mobile-menu-revealed.png` | 390 x 844 | normal | `#menu` with `scroll-margin-top` — heading not clipped |
| `05-reduced-motion-menu-visible.png` | 1440 x 900 | reduce | `#menu` with `scroll-margin-top` — heading not clipped, no stage |
| `06-desktop-reverse-restored.png` | 1440 x 900 | normal | after 0.10 → 0.70 → 0.10 — restored state at same progress as entrance |

After the final successful run, each PNG is validated for:
- file exists,
- valid PNG header (`89 50 4E 47 0D 0A 1A 0A`),
- exact expected viewport dimensions parsed from the IHDR chunk.

The final run reported `passed: true`, 0 `errors`, and exit code 0. No alternate,
debug, failed, or temporary screenshots were left behind.

## 17. Residual risks

- The desktop matchMedia is owned by a module-scoped `p3MenuStory` object. If a
  later phase replaces that controller, it must call `initMenuStoryFramework()`
  again (or `p3MenuStory.revert`) so the previous Phase 3 matchMedia is explicitly
  reverted before a new one is created.
- The story stage is 100 vh tall; on viewports shorter than 600 px the
  `min-height: 600px` keeps the frame visible. Real laptops (≥ 700 px) are fine.
- The decorative elements use `--terracotta`, `--olive-green`, `--healthy-green`,
  `--deep-black`, and `--coffee-cream`. Phase 4 will replace the prototype with
  character-specific artwork; the framework itself is palette-agnostic.
- The fixed-header offset is a hardcoded value. If the header's real height
  changes (e.g., a taller tagline or a wrapping layout), the offset will need
  to be re-measured. A `ponytail:` note was considered but the values are
  small, deterministic, and matched to the current header padding / content
  heights verified by the screenshots.

## 18. Remaining Phase 4 work (not in scope of Phase 3)

- Swap the neutral prototype for Papa's layered 2D artwork (body, head,
  serving-group, shadow, mobile fallback) from `assets/scenes/papa/`.
- Add Papa-specific ingredient sprites from `assets/scenes/papa/effects/`.
- Add the Papa-specific plate-tilt + arm-rotation angles (currently a placeholder
  rotation of 7° on the group and -12° on the plate).
- Move the decorative elements from neutral circles to the Papa ingredient set.
- Re-tune the `start` / `end` if the Papa art needs a longer scroll distance.
- Add the "Mama out, Papa in" hand-off (Papa is the first character, so this
  may not be needed; if the section transitions to Papa from the Moods section,
  consider an entrance color gradient).

---

**Phase 3 status:** Ready for review. Phase 4 not started.

