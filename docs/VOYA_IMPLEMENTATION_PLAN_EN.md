# VOYA Website Implementation and Review Plan

## 1. Purpose

This document is the source of truth for implementing and reviewing the VOYA website improvements.

After completing any phase, review it to confirm that:

- Every required item was implemented.
- The result follows the approved VOYA identity.
- Motion and interactions behave as specified.
- Mobile usability, accessibility, and performance remain acceptable.
- Existing menu, cart, and WhatsApp ordering behavior was not broken.

## 2. Core Decisions

- Keep all VOYA characters **2D** to preserve the original brand identity.
- Animate arms, hands, plates, and cups as separate **2D layers**.
- Use rotation, perspective, scale, shadows, and parallax to create depth.
- Keep menu items as real HTML so they remain readable, clickable, accessible, and connected to the cart.
- Use the existing stack: **HTML, CSS, JavaScript, GSAP, and ScrollTrigger**.
- Do not add Three.js, Blender models, or true 3D characters in the core implementation.
- Build a shorter and simpler mobile experience instead of shrinking the desktop animation.
- Approve Papa as the reference implementation before building Mama and Voya Coffee.

## 3. Overall Status

| Phase | Status | Review Result |
|---|---|---|
| 0. Establish the baseline | Accepted | — |
| 1. Clean up the current website | Accepted | — |
| 2. Prepare illustration assets | Accepted | — |
| 3. Build the menu story framework | Ready for review | — |
| 4. Build the Papa scene | Not started | — |
| 5. Build the Mama scene | Not started | — |
| 6. Build Voya Coffee and the House ending | Not started | — |
| 7. Mobile and accessibility pass | Not started | — |
| 8. Performance and final QA | Not started | — |

Allowed status values: `Not started`, `In progress`, `Ready for review`, `Accepted`, `Changes required`.

---

# Phase 0: Establish the Baseline

## Goal

Record the current website state before implementation so regressions can be identified reliably.

## Tasks

- Create a clear Git checkpoint before development starts.
- Record the existing sections and user flow.
- Record the current menu, cart, and WhatsApp behavior.
- Capture reference screenshots of the important sections on desktop and mobile.
- Identify the main files expected to change.
- Preserve all original identity and illustration files.

## Deliverables

- A recoverable baseline version.
- Desktop and mobile “before” screenshots.
- A short list of existing functionality.

## Acceptance Criteria

- [ ] A clear before/after comparison point exists.
- [ ] The baseline website runs without visible JavaScript errors.
- [ ] Existing menu, cart, and order behavior is documented.
- [ ] Original brand files have not been removed or altered.

## Review Checks

- Inspect Git status and the baseline checkpoint.
- Run the existing website.
- Verify desktop and mobile reference screenshots.
- Confirm that the current user flow is documented.

---

# Phase 1: Clean Up the Current Website

## Goal

Fix small, high-impact issues before adding the new scroll-driven experience.

## Content Tasks

- Correct `Machiato` to `Macchiato` where appropriate.
- Confirm and correct the intended `Humer Head` product name.
- Standardize product names, category names, and price formatting.
- Fix broken encoding characters such as `â€”`.
- Ensure source files are saved as UTF-8.

## Usability Tasks

- Standardize the primary button styles and states.
- Clarify the main flow: explore brand, open menu, add item, open cart, order.
- Improve small-text readability, contrast, spacing, and line length.
- Make hover and keyboard focus states clearly visible.

## Menu Tasks

- Prevent stale content when users switch rapidly between Papa, Mama, and Voya.
- Cancel the active transition before starting a new one.
- Ensure the latest user selection always wins.
- Keep a single source of truth for menu and cart data.

## WhatsApp Tasks

- Open the WhatsApp order link with `noopener,noreferrer` protection.
- Confirm that the generated message contains the correct products, quantities, and total.

## Acceptance Criteria

- [ ] No known product-name errors remain.
- [ ] No broken encoding characters appear.
- [ ] Rapid brand/category switching never renders stale data.
- [ ] Primary actions are clear and visually consistent.
- [ ] Keyboard focus is visible.
- [ ] Cart totals and the WhatsApp message are correct.
- [ ] No new console errors appear.

## Review Checks

- Compare product text with approved content.
- Stress-test rapid brand and category switching.
- Test one product, multiple products, quantity changes, and removal.
- Test the final WhatsApp link and message.
- Review desktop, mobile, and keyboard behavior.

---

# Phase 2: Prepare Illustration Assets

## Goal

Convert the original illustrations into web-ready animation layers without changing the character designs.

## Required Layers Per Character

- Base body or pose.
- Head, only if independent movement is needed.
- Movable arm.
- Hand, if it needs independent movement.
- Plate or cup.
- Food, ingredients, coffee beans, or steam elements.
- Shadow layer.
- Simplified mobile alternative when required.

## Asset Rules

- Prefer SVG for suitable vector artwork.
- Use optimized transparent WebP or PNG only when SVG is unsuitable.
- Remove unnecessary transparent space around assets.
- Use clear, consistent filenames and layer names.
- Optimize file size without visible quality loss.
- Preserve the original face, glasses, proportions, line weight, and color treatment.

## Motion Boundaries

- Do not redesign faces, glasses, or body proportions.
- Do not generate guessed viewing angles for the characters.
- Keep character limb movement restrained and consistent with the illustration style.
- Allow plates, cups, ingredients, and steam to move more freely.

## Acceptance Criteria

- [ ] Reassembled layers match the original illustration.
- [ ] No gaps, seams, or clipped edges appear between layers.
- [ ] Arm, plate, and cup transform origins feel natural.
- [ ] Assets remain sharp on high-density displays.
- [ ] File sizes are suitable for web delivery.
- [ ] Papa has every asset required for the first complete scene.

## Review Checks

- Compare reassembled characters with the originals.
- Inspect image quality and file sizes.
- Test transform origins with a minimal motion prototype.
- Confirm that asset naming and organization are usable in code.

---

# Phase 3: Build the Menu Story Framework

## Goal

Build the shared scroll-scene structure once before adding character-specific details.

## Required Sequence

1. Enter the character scene.
2. Pin the scene for a controlled scroll distance.
3. Animate the arm and plate or cup.
4. Release ingredients or visual elements.
5. Guide those elements toward the menu categories.
6. Reveal the usable HTML menu.
7. End the scene and transition to the next character.

## Technical Tasks

- Use ScrollTrigger for scroll-linked scene progress.
- Use one clear GSAP timeline per scene.
- Avoid duplicate triggers after resize or reinitialization.
- Refresh measurements correctly after responsive layout changes.
- Reuse the existing menu data instead of duplicating it for animation.
- Keep the existing cart and ordering state as the single source of truth.
- Do not hijack native scrolling or trap the user in a scene.
- Keep menus usable when animation is unavailable.

## Acceptance Criteria

- [ ] A basic scene prototype works without final artwork.
- [ ] Pinning starts and ends without a page jump.
- [ ] Scrolling upward reverses the scene correctly.
- [ ] Resizing does not duplicate or break triggers.
- [ ] The menu remains interactive after the reveal.
- [ ] No unnecessary dependency was added.

## Review Checks

- Inspect ScrollTrigger creation, refresh, and cleanup.
- Test downward scroll, upward scroll, fast scroll, and resize.
- Confirm that the animation uses existing menu/cart data.
- Check for page jumps, stuck pins, and accidental blank space.

---

# Phase 4: Build the Papa Scene

## Goal

Create Papa as the complete reference scene. Do not start Mama until this scene is reviewed and accepted.

## Scene Requirements

### Papa Entrance

- Transition the background to Soft Ivory with Healthy Green and Olive Green accents.
- Reveal Papa holding the plate.
- Show a short headline and description connected to his healthy-food personality.
- Keep the entrance calm, clear, and consistent with the premium brand tone.

### Plate Motion

- Rotate Papa’s arm around a natural joint.
- Tilt the plate progressively with scroll.
- Add depth with rotation, scale, perspective, and shadow.
- Keep Papa visually faithful to the original artwork.

### Ingredient Release

- Use a restrained set of approximately four to six ingredients.
- Give the elements varied but controlled paths.
- Do not cover Papa’s face, important text, or controls.
- Visually guide the elements toward menu categories or cards.

### Menu Reveal

- Reveal the Papa Menu title and categories.
- Display readable products and prices.
- Keep add-to-cart actions fully functional.
- Stop distracting background movement while the user interacts with the menu.

## Acceptance Criteria

- [ ] Papa matches the original brand illustration.
- [ ] Arm and plate movement feels natural.
- [ ] The motion is controlled by scroll rather than autoplay video.
- [ ] Ingredients do not create visual clutter.
- [ ] The correct Papa menu data appears.
- [ ] Papa products can be added to the cart.
- [ ] Reverse scrolling restores the scene correctly.
- [ ] Mobile and reduced-motion alternatives exist.
- [ ] Performance is smooth on a mid-range device.

## Approval Gate

Approve all of the following before starting Mama:

- Motion style.
- Scroll distance and pacing.
- Plate tilt amount.
- Ingredient count.
- Menu reveal behavior.
- Mobile simplification.

## Review Checks

- Compare implementation with the required sequence.
- Inspect layer quality and transform origins.
- Verify Papa menu and cart behavior.
- Test desktop, mobile, fast scroll, and reverse scroll.

---

# Phase 5: Build the Mama Scene

## Goal

Reuse the accepted scene framework while giving Mama a distinct visual personality.

## Scene Requirements

- Transition from Papa green tones to Soft Peach and Terracotta.
- Move Papa out and Mama in smoothly.
- Use Mama’s plate, lid, or serving action as the central movement.
- Prefer opening a lid or revealing food instead of repeating Papa’s exact falling-plate motion.
- Release elements associated with comfort or home-style food.
- Reveal the correct Mama menu data.

## Acceptance Criteria

- [ ] The Papa-to-Mama transition is clear and smooth.
- [ ] Mama matches the original brand illustration.
- [ ] The accepted framework is reused without unnecessary duplicated logic.
- [ ] Mama’s motion is meaningfully different from Papa’s.
- [ ] Correct Mama products and prices appear.
- [ ] Mama products can be added to the cart.
- [ ] The mobile version remains clear and usable.

## Review Checks

- Review the transition between both characters.
- Confirm simple reuse of the approved scene framework.
- Verify colors, content, motion, menu, and cart behavior.
- Switch repeatedly between Papa and Mama and check for stale state.

---

# Phase 6: Build Voya Coffee and the House Ending

## Goal

Complete the menu journey and connect all three experiences under Voya House.

## Voya Coffee Scene

- Transition to Coffee Cream and Deep Black.
- Reveal the Voya character or primary coffee element.
- Animate the cup or steam instead of repeating a falling plate.
- Use coffee beans or steam paths to introduce menu categories.
- Reveal the correct drinks and products.

## Voya House Ending

- Bring Papa, Mama, and Voya together visually.
- State clearly that Voya House is the umbrella identity for all three experiences.
- Provide a clear route back to each menu.
- Provide a clear cart or checkout action.
- End the story without adding another long pinned sequence.

## Acceptance Criteria

- [ ] Coffee motion suits the product and does not repeat the plate scene.
- [ ] Voya Coffee products work with the shared cart.
- [ ] The ending explains the relationship to Voya House.
- [ ] Users can return to any menu without confusion.
- [ ] The final cart/order action is clear.
- [ ] The complete experience does not feel excessively long.

## Review Checks

- Confirm that every scene is distinct but follows one visual system.
- Verify all menus while switching between characters.
- Review the clarity of the Voya House ending.
- Evaluate total scroll length and checkout usability.

---

# Phase 7: Mobile and Accessibility Pass

## Goal

Provide a fast and usable experience on mobile and for users who prefer reduced motion.

## Mobile Tasks

- Reduce scroll duration for each character.
- Reduce the number of simultaneous moving elements.
- Simplify arm, plate, cup, and ingredient motion.
- Prevent elements from leaving the viewport or covering text.
- Present menus as touch-friendly cards or accordions where appropriate.
- Keep controls large enough for comfortable touch interaction.
- Never force users to wait for animation before accessing a menu.

## Accessibility Tasks

- Support `prefers-reduced-motion`.
- Keep content and menus available when motion is disabled.
- Add useful alternative text to meaningful images.
- Hide purely decorative layers from assistive technology.
- Preserve a logical keyboard navigation order.
- Ensure visible focus and sufficient contrast.
- Ensure pinned scenes do not block keyboard navigation.

## Acceptance Criteria

- [ ] No accidental horizontal scrolling exists.
- [ ] Text and controls do not overlap on small screens.
- [ ] Menus work with touch and keyboard input.
- [ ] Reduced Motion shows simple transitions or immediate content.
- [ ] Core content remains available without animation.
- [ ] Touch targets are comfortably sized.

## Review Checks

- Test several phone and tablet viewport sizes.
- Test portrait and relevant landscape layouts.
- Test touch, keyboard, and Reduced Motion.
- Disable motion and confirm that all menus remain usable.

---

# Phase 8: Performance and Final QA

## Goal

Confirm that the final experience is stable, responsive, and ready to publish.

## Performance Tasks

- Optimize SVG and raster assets.
- Lazy-load scene assets when useful.
- Prefer animating `transform` and `opacity`.
- Avoid properties that repeatedly trigger layout.
- Reduce expensive blur and shadow effects on mobile.
- Pause or remove off-screen animation work.
- Remove unused code and assets.

## Functional Tests

- Navigate through every section.
- Scroll down and back up through every scene.
- Switch rapidly between menus and categories.
- Add, remove, and change product quantities.
- Open and close the cart.
- Generate and open the WhatsApp order.
- Refresh at different page positions.
- Resize the viewport and change device orientation.

## Target Browsers

- Current Chrome.
- Current Edge.
- Safari on iPhone, when available.
- A current Android browser.

## Acceptance Criteria

- [ ] No visible JavaScript errors remain.
- [ ] No assets are missing.
- [ ] Scenes do not duplicate or overlap after resize.
- [ ] Menu, cart, and order behavior works after using every scene.
- [ ] Performance is acceptable on a mid-range mobile device.
- [ ] No major layout shift occurs while assets load.
- [ ] Reduced Motion works correctly.
- [ ] No critical issue exists in target browsers.

## Review Checks

- Perform a complete desktop and mobile visual review.
- Inspect console and network behavior.
- Check loading and animation smoothness on realistic hardware.
- Repeat the complete ordering flow.
- Compare the final result with the identity documents and baseline screenshots.

---

# 4. 2D and 3D Responsibility Matrix

| Element | Implementation |
|---|---|
| Papa, Mama, and Voya characters | Original 2D artwork |
| Arms and hands | Separate 2D layers with controlled transform origins |
| Plates and cups | 2D layers with perspective, rotation, scale, and shadow |
| Ingredients, beans, and steam | 2D elements with motion paths and visual depth |
| Menu cards and controls | Real HTML and CSS |
| Backgrounds and decorative graphics | CSS and SVG |
| Shadows and parallax | CSS and GSAP effects |
| True 3D models | Not required in the current scope |

# 5. Approved Tools

- Illustrator or Figma for preparing illustration layers.
- SVG and optimized WebP for final assets.
- GSAP and ScrollTrigger for motion and scroll control.
- CSS transforms for perspective and depth.
- Existing HTML and JavaScript for menu, cart, and order behavior.

Do not add Three.js or another animation library unless a verified requirement cannot be met with the existing stack.

# 6. How to Request a Phase Review

Use this request after completing a phase:

> Review Phase X from `VOYA_IMPLEMENTATION_PLAN_EN.md`. Inspect the implementation visually, functionally, and technically. Compare it against every acceptance criterion. Do not modify any files before reporting the review findings.

The review result must be one of:

- **Accepted:** All essential requirements are complete.
- **Accepted with minor notes:** The phase can proceed; remaining items are non-blocking.
- **Changes required:** Missing or incorrect items must be fixed before proceeding.
- **Incomplete:** A core part is missing or cannot be tested.

# 7. Required Review Report Format

Every phase review must include:

1. Overall phase result.
2. Correctly completed requirements.
3. Missing requirements.
4. Incorrect or materially different implementation.
5. Visual, functional, technical, accessibility, and performance issues.
6. Desktop and mobile test results.
7. Required changes ordered by severity.
8. A clear decision: proceed to the next phase or fix the current phase first.

# 8. Scope-Control Rules

- Do not convert the characters into full 3D models.
- Do not alter the identity of the characters to make animation easier.
- Do not rebuild the website with a new framework without a proven need.
- Do not add dependencies when GSAP, CSS, and the current code can meet the requirement.
- Do not start Mama before Papa is accepted.
- Do not sacrifice menu usability for animation.
- Do not approve desktop without testing mobile.
- Defer ideas that do not directly support the menu journey or ordering flow.

# 9. Definition of Done

The project is complete when:

- All three characters are a clear part of the menu journey.
- Scroll scenes work smoothly on desktop and mobile.
- Character artwork still matches the original identity.
- Every menu remains accessible without relying on animation alone.
- Cart and WhatsApp ordering work correctly.
- Reduced Motion is supported.
- No critical errors or visible performance problems remain.
- Every phase has passed its acceptance criteria.
