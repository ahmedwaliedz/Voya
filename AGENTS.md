# VOYA

Static marketing site (HTML, CSS, vanilla JavaScript) for a fictional coffee and food brand. No build step, no package manager, no backend. Brand identity is 2D illustration; characters remain 2D.

## Stack

- Plain HTML, CSS, JavaScript
- GSAP and ScrollTrigger, vendored under `vendor/gsap/`
- No `package.json` at the project root; no Node toolchain is required to run the site

## Production paths

- `index.html`, `style.css`, `script.js`
- `assets/images/`, `assets/scenes/`

## Authoritative plan

`docs/VOYA_IMPLEMENTATION_PLAN_EN.md` is the source of truth for phased work.

## Commands

None defined. No install, run, lint, typecheck, or test command exists in the project. It is a static site without a build system. (`docs/baseline/package.json` is a Phase 0 capture-tooling manifest, not the project.)

## Vendored and generated paths

Do not edit manually:
- `vendor/gsap/`
- `docs/baseline/node_modules/`
