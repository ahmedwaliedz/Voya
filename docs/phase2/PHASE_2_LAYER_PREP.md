# Phase 2 — Illustration Layer Preparation

**Date:** 2026-08-01
**Phase skill:** `.cursor/skills/voya-illustration-layer-prep/SKILL.md`
**Phase start commit:** `17bef48`
**Status:** Phase 2 complete — ready for final external review. Phase 3 not started.

---

## 1. Approved temporary sources

| Asset | Path |
|-------|------|
| Papa | `assets/images/temporary/papa-temp-clean.png` |
| Mama | `assets/images/temporary/mama-temp-clean.png` |
| Voya | `assets/images/temporary/voya-temp-clean.png` |
| House | `assets/images/temporary/house-temp-clean.png` |

Do not use marketing images, `story-family.png`, or rejected crops for Phase 2.

### Protection baselines

| Baseline | Path |
|----------|------|
| Papa-gate Mama/Voya snapshot (historical) | `docs/phase2/.papa-gate-baseline.json` |
| Papa approved | `docs/phase2/.papa-approved-baseline.json` |
| Mama approved | `docs/phase2/.mama-approved-baseline.json` |
| Voya approved | `docs/phase2/.voya-approved-baseline.json` |

---

## 2. Papa layer contract

| Layer | Group | Motion |
|-------|-------|--------|
| `papa-shadow` | shadow | none |
| `papa-body` | body | static |
| `papa-head` | head | **static** (blocked) |
| `papa-serving-group` | serving | **±2°** |

Serving group = both arms, hands, plate, all neutral food.

Neutral RGBA vs approved source: **0** differing pixels.
Terra: **Approved**.

Effect sprites (Phase 4 only, not in neutral): `assets/scenes/papa/effects/` — grilled-protein, broccoli, grains, salad, tomato.

---

## 3. Mama layer contract

| Layer | Group | Motion |
|-------|-------|--------|
| `mama-shadow` | shadow | none |
| `mama-body` | body | static |
| `mama-head` | head | **static** (blocked) |
| `mama-serving-group` | serving | **blocked** (semantic group kept) |

Serving group = interlocked arms, hands, pizza.
Internal serving rotation tested ±3/±2/±1; no clean non-zero range under opaque-only underpaint (best ±1 left 111 torso holes). Semantic group retained for whole-character transforms.

Neutral RGBA vs approved source: **0** differing pixels.
Terra: **Approved**.

---

## 4. Voya layer contract

| Layer | Group | Motion |
|-------|-------|--------|
| `voya-shadow` | shadow | none |
| `voya-body` | body | static (includes backpack, skateboard, free arm) |
| `voya-head` | head | **static** (blocked) |
| `voya-cup-group` | serving | **±3°** (pivot ~28% / 10% at sleeve attachment) |

Cup group = cup + holding hand (interlocked; neck/face excluded).
Shirt/sleeve fills stay on body; cup keeps cream hand/cup plus thin hugging outlines only.
Localized solid dark shirt underpaint fills motion gaps under opaque cup interiors at the sleeve joint (no cream underpaint, no new outline strokes).

Neutral RGBA vs approved source: **0** differing pixels.
Terra: **Approved** (cup-joint endpoints clean at ±3° after exclusive-mask + shirt-stump fix).

---

## 5. House static asset

| Item | Value |
|------|-------|
| Source | `assets/images/temporary/house-temp-clean.png` |
| Static asset | `assets/scenes/house/house-static.png` |
| Type | Single static 2D background |
| Magenta | 0 |
| Transparent background | yes |
| Fake 3D split | no |
| Raster branding text | no (later HTML/SVG overlay) |

Fit evidence: `docs/phase2/evidence/house/browser/house_fit_{desktop,mobile}.png`.

---

## 6. Fallback and reduced motion

Character preview fits scene canvas into 1440×900 and 390×844.
Fallback and reduced-motion both render layered neutral. Verifier requires pixel equality.

---

## 7. Scoped commands

```text
python docs/phase2/prepare-layers.py --character <papa|mama|voya>
node docs/phase2/capture-evidence.mjs --character=<papa|mama|voya>
python docs/phase2/verify-phase2.py --character <papa|mama|voya>
node docs/phase2/capture-house-evidence.mjs
python docs/phase2/verify-phase2.py --all
```

Unscoped generator/verifier runs exit non-zero. `--all` required for full regeneration/verification.

---

## 8. Gate status

| Gate | Status |
|------|--------|
| Papa | Automated PASS + Terra Approved + user approved |
| Mama | Automated PASS + Terra Approved |
| Voya | Automated PASS + Terra Approved |
| House static prep | Validated + fit evidence |
| Phase 2 complete | **Yes — ready for final external review** |
