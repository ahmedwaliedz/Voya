# Phase 0 — Baseline Record

**Date:** 2026-07-31
**Git checkpoint:** Annotated tag `baseline/pre-implementation` (created with the Phase 0 baseline commit)
**Purpose:** Before/after comparison point for the VOYA scroll-story implementation.

---

## 1. Site Sections and User Flow

### Page structure (top → bottom)

| # | Section | ID | Purpose |
|---|---------|-----|---------|
| 1 | Page transition overlay | `#pageTransition` | GSAP intro animation (Coffee → Healthy → Comfort words) |
| 2 | Header | `#header` | Nav: Story, Brands, Menu, Locations, Contact + Cart |
| 3 | Hero | `#home` | Tagline, CTAs: Explore Menu, Order on WhatsApp |
| 4 | Marquee | — | Decorative scrolling brand words |
| 5 | Story | `#story` | Voya House brand narrative |
| 6 | Three Moods / Brands | `#moods` | Cards for VOYA, Papa Voya, Mama Voya → jump to menu |
| 7 | Menu | `#menu` | Brand switch, room intro, category chips, product rail |
| 8 | Locations | `#locations` | Two Al Ahly Sporting Club branches (maps TBD) |
| 9 | Footer / Contact | `#contact` | Phone, email, web, Instagram |
| 10 | Cart drawer | `#cartDrawer` | Slide-out order summary + WhatsApp checkout |
| 11 | Sticky order strip | `#orderStrip` | Appears when cart has items |
| 12 | Toast | `#toast` | Add-to-cart feedback |

### Primary user flows

1. **Browse → order:** Hero/Brands → Menu → pick brand → category → add items → Cart → WhatsApp
2. **Direct menu:** Header "Menu" or skip link → same menu flow
3. **Quick WhatsApp:** Hero "Order on WhatsApp" → opens `wa.me/201050000598` (empty message)
4. **Brand shortcut:** Mood card buttons call `switchToMenu('voya'|'papa'|'mama')` and scroll to `#menu`

---

## 2. Menu, Cart, and WhatsApp Behavior

### Menu data (single source of truth)

- Location: `script.js` → `menuData` object
- Brands: `voya` (11 categories), `papa` (1 category), `mama` (7 categories)
- Default brand on load: **voya**

### Brand switching

- `switchBrand(brand)` updates: brand tabs, room intro, featured image, category chips, product rail
- GSAP exit animation on cards (~280ms + stagger) before re-render when motion enabled
- **Known issue (Phase 1):** Rapid switching does not cancel in-flight transition timers; last click may not always win

### Category and products

- Horizontal category chips with scroll nav (‹ ›)
- Product rail: horizontal cards with name, optional desc, price, add/qty controls
- Event delegation on `#productRail` for add/increase/decrease

### Cart

- In-memory array: `{ name, price, qty }`
- `addToCart` / `updateQty` / `removeFromCart` → `updateCartUI()` + `updateRailCards()`
- Cart count in header; drawer with line items, qty controls, remove, total
- WhatsApp button disabled when cart empty
- Sticky order strip when items present and drawer closed
- Focus trap + Escape to close drawer

### WhatsApp ordering

- Function: `orderOnWhatsApp()`
- URL: `https://wa.me/201050000598?text={encoded message}`
- Message format:
  ```
  Hello Voya House, I want to order:

  {qty}x {name} - {line total} EGP
  ...

  Total: {total} EGP
  ```
- Opens via `window.open(..., '_blank')` — **no `noopener,noreferrer` on cart order link** (Phase 1 fix)
- Hero WhatsApp link already has `rel="noopener noreferrer"`

### Motion / GSAP

- Vendor: `vendor/gsap/gsap.min.js`, `vendor/gsap/ScrollTrigger.min.js`
- Page intro, hero parallax, scroll reveals, product card animations
- `prefers-reduced-motion: reduce` → static fallback via `showPageWithoutMotion()`
- 3.5s timeout fallback if intro does not complete

---

## 3. Known Content Issues (documented for Phase 1)

| Issue | Location | Current value |
|-------|----------|---------------|
| Spelling | `menuData.voya` | `Machiato` (×2), `Caramel Machiato`, `Ice Caramel Machiato` |
| Product name TBD | Other Drinks | `Humer Head` — confirm with brand |
| Encoding | — | No broken em-dash encoding found in current source files |

---

## 4. Asset Inventory (preserved originals)

| File | Role |
|------|------|
| `assets/images/logo-voya.png` | Brand logo |
| `assets/images/papa-healthy.png` | Papa featured / mood |
| `assets/images/mama-comfort.png` | Mama featured / mood |
| `assets/images/mama-pizza.png` | Mama illustration |
| `assets/images/voya-coffee.png` | Voya coffee illustration |
| `assets/images/voya-coffee-menu-generated.png` | Voya menu featured image |
| `assets/images/Voya-Menu.png` | Voya menu reference |
| `assets/images/story-family.png` | Story section |
| `assets/images/locations-storefront.png` | Locations section |

**Note:** All assets are included in the Phase 0 baseline commit; none were removed or altered during Phase 0.

---

## 5. Files Expected to Change (Phases 1–8)

| File / folder | Expected changes |
|---------------|------------------|
| `index.html` | Scroll scenes, layered character markup, menu structure |
| `style.css` | Scene layouts, character layers, mobile/reduced-motion |
| `script.js` | ScrollTrigger scenes, menu transition fixes, cart/WhatsApp |
| `assets/images/` | New layered SVG/PNG assets per character |
| `assets/scenes/` | (new) Scene-specific assets if organized separately |
| `docs/baseline/` | Baseline record and screenshots (this folder) |

**Unlikely to change:** `vendor/gsap/*` (pinned local copies)

---

## 6. Reference Screenshots

Stored in:

- `docs/baseline/screenshots/desktop/` — 1440×900
- `docs/baseline/screenshots/mobile/` — 390×844

Key captures: full page, hero, story, moods, menu (voya/papa/mama on desktop), locations, footer, cart drawer.

---

## 7. Console / Runtime Check

- Site served locally at `http://127.0.0.1:8765` for baseline capture
- GSAP loads from vendor; motion system initializes with fallback when reduced motion or missing GSAP
- See `capture-log.json` for any page errors captured during screenshot run

---

## 8. Acceptance Criteria Checklist

- [x] Clear before/after comparison point exists (this doc, screenshots, and git tag)
- [x] Baseline website runs (static server + GSAP vendor present)
- [x] Menu, cart, and order behavior documented
- [x] Original brand files preserved (not removed or altered)

## 9. Git Checkpoint

- **Tag:** `baseline/pre-implementation` (annotated)
- **Commit message:** `Establish Phase 0 baseline before scroll-story implementation`
- **Recover baseline:** `git checkout baseline/pre-implementation`

---

**Phase 0 status:** Ready for review
