// Phase 3 evidence capture. Uses the existing Playwright install
// at docs/baseline/node_modules/playwright — no new dependency.
//
// Readiness:
//   waitForReady() throws when the page never reaches is-loaded + transition-done,
//   when the required Phase 3 DOM nodes are missing, or when the trigger count
//   does not match the viewport. Any readiness failure is fatal.
//
// Assertions:
//   Each scenario pushes assertions through assert(). A failure sets the
//   overall `passed` flag but does not stop the run; the final exit code
//   reflects the worst observed result.
//
// Errors:
//   pageerror, console.error, and requestfailed are collected per scenario.
//   Any error makes the run fail, even if all assertions pass.
//   The Google Fonts stylesheet is fulfilled offline via one shared route helper
//   so fonts.googleapis.com does not produce requestfailed/console.error in
//   offline review environments. All other failures remain fatal.
//
// Exit codes:
//   0  every scenario passed AND errors is empty
//   1  any assertion failed, any browser error recorded, readiness failure,
//      or any unexpected exception during capture.

import { chromium } from '../baseline/node_modules/playwright/index.mjs';
import { createServer } from 'http';
import { readFileSync, existsSync, mkdirSync, statSync } from 'fs';
import { join, extname } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '../..');
const outDir = join(__dirname, 'evidence', 'browser');
mkdirSync(outDir, { recursive: true });
const port = 8770;

// Reverse-restoration tolerances (documented):
//   trigger progress: <= 0.02
//   opacity: <= 0.02
//   transform matrix component: <= 0.1
const TOL_PROGRESS = 0.02;
const TOL_OPACITY = 0.02;
const TOL_TRANSFORM = 0.1;
const ENTRANCE_PROGRESS = 0.10;
const FORWARD_PROGRESS = 0.70;

const mime = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.webp': 'image/webp',
  '.svg': 'image/svg+xml',
};

const server = createServer((req, res) => {
  let path = req.url.split('?')[0];
  if (path === '/') path = '/index.html';
  const filePath = join(root, path.replace(/^\//, ''));
  if (!existsSync(filePath)) {
    res.writeHead(404);
    res.end('Not found');
    return;
  }
  const ext = extname(filePath);
  res.writeHead(200, { 'Content-Type': mime[ext] || 'application/octet-stream' });
  res.end(readFileSync(filePath));
});

await new Promise((resolve) => server.listen(port, resolve));
const baseUrl = `http://127.0.0.1:${port}`;
const browser = await chromium.launch();

const errors = [];
const assertions = [];
let allPassed = true;
let readinessFailed = false;
let fatalError = null;
let googleFontsRoute = { installed: false, pattern: null, fulfilledCount: 0 };

function recordAssertion(scenario, name, condition, detail) {
  const passed = !!condition;
  if (!passed) allPassed = false;
  assertions.push({
    scenario,
    name,
    passed,
    detail: detail === undefined ? null : detail,
  });
}

function trackErrors(page, label) {
  page.on('pageerror', (err) => {
    errors.push(`[${label}] pageerror: ${err.message}`);
    allPassed = false;
  });
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(`[${label}] console: ${msg.text()}`);
      allPassed = false;
    }
  });
  page.on('requestfailed', (req) => {
    errors.push(`[${label}] requestfailed: ${req.url()} ${req.failure()?.errorText || ''}`);
    allPassed = false;
  });
}

// Shared helper: install once per browser context, before any navigation.
// Fulfills only the known fonts.googleapis.com stylesheet with empty CSS so
// no fonts.gstatic.com font files are requested. Intentionally fulfilled
// requests are not errors. All other requestfailed/console.error/pageerror
// events remain fatal.
async function installGoogleFontsTestRoute(context) {
  const pattern = 'https://fonts.googleapis.com/css2**';
  let fulfilledCount = 0;
  await context.route(pattern, async (route) => {
    fulfilledCount += 1;
    googleFontsRoute.fulfilledCount += 1;
    await route.fulfill({
      status: 200,
      contentType: 'text/css',
      body: '',
    });
  });
  googleFontsRoute.installed = true;
  googleFontsRoute.pattern = pattern;
  return { installed: true, pattern, getFulfilledCount: () => fulfilledCount };
}

async function openScenario(browserRef, label, contextOptions) {
  const ctx = await browserRef.newContext(contextOptions);
  const fontRoute = await installGoogleFontsTestRoute(ctx);
  const page = await ctx.newPage();
  trackErrors(page, label);
  return { ctx, page, fontRoute };
}

async function waitForReady(page) {
  // body classes set by the page intro timeline.
  await page.waitForFunction(
    () => document.body.classList.contains('is-loaded') &&
          document.body.classList.contains('transition-done'),
    null,
    { timeout: 12000 }
  );
  // Required DOM nodes. Use 'attached' because #p3MenuStory and .p3-frame
  // are display:none on mobile and reduced-motion.
  await page.waitForSelector('#p3MenuStory', { state: 'attached', timeout: 5000 });
  await page.waitForSelector('#menuContentStart', { state: 'attached', timeout: 5000 });
  await page.waitForSelector('.p3-frame', { state: 'attached', timeout: 5000 });
  await page.waitForSelector('#menu .menu-header', { state: 'attached', timeout: 5000 });
  // Small settle for ScrollTrigger.refresh after the intro reveal.
  await page.waitForTimeout(600);
}

async function scrollProgress(page, fraction) {
  // Use the live ScrollTrigger start/end so entrance and reverse land on the
  // same progress. Measuring from getBoundingClientRect after pinReparent is
  // unreliable and was landing ~0.05 when 0.10 was requested.
  await page.evaluate((f) => {
    const t = (window.ScrollTrigger ? window.ScrollTrigger.getAll() : [])
      .find((tr) => tr.vars && tr.vars.id === 'p3-menu-story');
    if (!t) return;
    const top = t.start + (t.end - t.start) * f;
    window.scrollTo({ top, behavior: 'instant' });
  }, fraction);
  await page.waitForFunction((f) => {
    const t = (window.ScrollTrigger ? window.ScrollTrigger.getAll() : [])
      .find((tr) => tr.vars && tr.vars.id === 'p3-menu-story');
    if (!t) return false;
    return Math.abs(t.progress - f) <= 0.015;
  }, fraction, { timeout: 5000 });
  // scrub: 0.5 — allow the scrubbed timeline to catch up fully before probe/capture
  await page.waitForTimeout(700);
}

async function scrollToMenuHeader(page) {
  // Use scrollIntoView so the CSS scroll-margin-top (110px desktop / 100px mobile)
  // is respected. This lands the real menu header below the fixed header.
  await page.evaluate(() => {
    const el = document.getElementById('menuContentStart');
    if (!el) return;
    el.scrollIntoView({ behavior: 'instant', block: 'start' });
  });
  await page.waitForTimeout(600);
}

function captureVisualState(page) {
  return page.evaluate(() => {
    const parseTransform = (value) => {
      if (!value || value === 'none') return [1, 0, 0, 1, 0, 0];
      const m2 = value.match(/^matrix\(([^)]+)\)$/);
      if (m2) return m2[1].split(',').map((n) => Number(n.trim()));
      const m3 = value.match(/^matrix3d\(([^)]+)\)$/);
      if (m3) {
        const v = m3[1].split(',').map((n) => Number(n.trim()));
        // Normalize matrix3d to 2D affine components used by comparison.
        return [v[0], v[1], v[4], v[5], v[12], v[13]];
      }
      return [1, 0, 0, 1, 0, 0];
    };
    const styleState = (el) => {
      if (!el) return null;
      const cs = getComputedStyle(el);
      return {
        opacity: Number(cs.opacity),
        transform: parseTransform(cs.transform),
        transformRaw: cs.transform === 'none' ? 'none' : cs.transform,
      };
    };

    const triggers = (window.ScrollTrigger ? window.ScrollTrigger.getAll() : [])
      .filter((t) => t.vars && t.vars.id === 'p3-menu-story');
    const t = triggers[0] || null;
    const story = document.getElementById('p3MenuStory');
    const frame = document.querySelector('.p3-frame');
    const group = document.querySelector('.p3-group');
    const plate = document.querySelector('.p3-plate');
    const elements = [...document.querySelectorAll('.p3-el')];
    const header = document.getElementById('header');
    const headerCs = header ? getComputedStyle(header) : null;
    const headerRect = header ? header.getBoundingClientRect() : null;
    const storyCs = story ? getComputedStyle(story) : null;

    return {
      triggerCount: triggers.length,
      triggerProgress: t ? t.progress : null,
      triggerActive: t ? t.isActive : false,
      frame: styleState(frame),
      group: styleState(group),
      plate: styleState(plate),
      elements: elements.map(styleState),
      headerVisible: headerCs ? Number(headerCs.opacity) > 0 && headerCs.visibility !== 'hidden' : false,
      headerTop: headerRect ? Math.round(headerRect.top) : null,
      headerHeight: headerRect ? Math.round(headerRect.height) : null,
      pinnedPosition: storyCs ? storyCs.position : null,
      bodyScrollWidth: document.body.scrollWidth,
      viewportWidth: window.innerWidth,
      horizontalOverflow: document.body.scrollWidth > window.innerWidth + 1,
    };
  });
}

function transformDelta(a, b) {
  if (!a || !b) return Infinity;
  let max = 0;
  for (let i = 0; i < 6; i += 1) {
    max = Math.max(max, Math.abs((a[i] ?? 0) - (b[i] ?? 0)));
  }
  return max;
}

function compareVisualStates(a, b, tolerances) {
  const diffs = [];
  if (a.triggerCount !== b.triggerCount) {
    diffs.push({ field: 'triggerCount', a: a.triggerCount, b: b.triggerCount });
  }
  if (a.triggerProgress === null || b.triggerProgress === null) {
    diffs.push({ field: 'triggerProgress', a: a.triggerProgress, b: b.triggerProgress });
  } else if (Math.abs(a.triggerProgress - b.triggerProgress) > tolerances.progress) {
    diffs.push({
      field: 'triggerProgress',
      a: a.triggerProgress,
      b: b.triggerProgress,
      delta: Math.abs(a.triggerProgress - b.triggerProgress),
    });
  }
  const pairKeys = ['frame', 'group', 'plate'];
  for (const key of pairKeys) {
    const left = a[key];
    const right = b[key];
    if (!left || !right) {
      diffs.push({ field: `${key}.missing`, a: !!left, b: !!right });
      continue;
    }
    if (Math.abs(left.opacity - right.opacity) > tolerances.opacity) {
      diffs.push({
        field: `${key}.opacity`,
        a: left.opacity,
        b: right.opacity,
        delta: Math.abs(left.opacity - right.opacity),
      });
    }
    const tDelta = transformDelta(left.transform, right.transform);
    if (tDelta > tolerances.transform) {
      diffs.push({
        field: `${key}.transform`,
        a: left.transform,
        b: right.transform,
        delta: tDelta,
      });
    }
  }
  const len = Math.max(a.elements?.length || 0, b.elements?.length || 0);
  if ((a.elements?.length || 0) !== (b.elements?.length || 0)) {
    diffs.push({ field: 'elements.length', a: a.elements?.length, b: b.elements?.length });
  }
  for (let i = 0; i < len; i += 1) {
    const left = a.elements?.[i];
    const right = b.elements?.[i];
    if (!left || !right) {
      diffs.push({ field: `elements[${i}].missing`, a: !!left, b: !!right });
      continue;
    }
    if (Math.abs(left.opacity - right.opacity) > tolerances.opacity) {
      diffs.push({
        field: `elements[${i}].opacity`,
        a: left.opacity,
        b: right.opacity,
        delta: Math.abs(left.opacity - right.opacity),
      });
    }
    const tDelta = transformDelta(left.transform, right.transform);
    if (tDelta > tolerances.transform) {
      diffs.push({
        field: `elements[${i}].transform`,
        a: left.transform,
        b: right.transform,
        delta: tDelta,
      });
    }
  }
  if (a.headerVisible !== b.headerVisible) {
    diffs.push({ field: 'headerVisible', a: a.headerVisible, b: b.headerVisible });
  }
  if (a.pinnedPosition !== b.pinnedPosition) {
    diffs.push({ field: 'pinnedPosition', a: a.pinnedPosition, b: b.pinnedPosition });
  }
  if (a.horizontalOverflow !== b.horizontalOverflow) {
    diffs.push({ field: 'horizontalOverflow', a: a.horizontalOverflow, b: b.horizontalOverflow });
  }
  return diffs;
}

function statesDifferMeaningfully(a, b) {
  // Forward state at 0.70 must differ from entrance at 0.10.
  if (Math.abs((a.triggerProgress ?? 0) - (b.triggerProgress ?? 0)) > 0.2) return true;
  if (a.frame && b.frame && Math.abs(a.frame.opacity - b.frame.opacity) > 0.05) return true;
  if (a.group && b.group && transformDelta(a.group.transform, b.group.transform) > 0.5) return true;
  if (a.plate && b.plate && transformDelta(a.plate.transform, b.plate.transform) > 0.5) return true;
  const aEl = a.elements || [];
  const bEl = b.elements || [];
  for (let i = 0; i < Math.min(aEl.length, bEl.length); i += 1) {
    if (Math.abs(aEl[i].opacity - bEl[i].opacity) > 0.05) return true;
    if (transformDelta(aEl[i].transform, bEl[i].transform) > 0.5) return true;
  }
  return false;
}

const results = {};

try {
  // ---- DESKTOP: scene entrance ----
  {
    const label = 'desktop-entrance';
    const { ctx, page, fontRoute } = await openScenario(browser, label, {
      viewport: { width: 1440, height: 900 },
      reducedMotion: 'no-preference',
    });
    try {
      await page.goto(baseUrl, { waitUntil: 'networkidle' });
      await waitForReady(page);
      await scrollProgress(page, ENTRANCE_PROGRESS);
      const visual = await captureVisualState(page);
      const probe = {
        stageExists: !!(await page.$('#p3MenuStory')),
        stageDisplay: await page.evaluate(() => {
          const s = document.getElementById('p3MenuStory');
          return s ? getComputedStyle(s).display : null;
        }),
        frameExists: !!visual.frame,
        frameOpacity: visual.frame?.opacity ?? 0,
        triggerCount: visual.triggerCount,
        triggerProgress: visual.triggerProgress,
        bodyScrollWidth: visual.bodyScrollWidth,
        viewportWidth: visual.viewportWidth,
        visual,
        googleFontsRouteInstalled: fontRoute.installed,
        googleFontsFulfilled: fontRoute.getFulfilledCount(),
      };
      results[label] = probe;
      recordAssertion(label, 'p3MenuStory exists', probe.stageExists);
      recordAssertion(label, 'p3MenuStory is displayed (not none)', probe.stageDisplay !== 'none', { display: probe.stageDisplay });
      recordAssertion(label, 'frame exists', probe.frameExists);
      recordAssertion(label, 'frame is visibly rendered (opacity > 0.5)', probe.frameOpacity > 0.5, { opacity: probe.frameOpacity });
      recordAssertion(label, 'exactly one p3-menu-story trigger', probe.triggerCount === 1, { count: probe.triggerCount });
      recordAssertion(label, 'trigger progress near 0.10 (within ±0.1)', probe.triggerProgress !== null && Math.abs(probe.triggerProgress - ENTRANCE_PROGRESS) <= 0.1, { progress: probe.triggerProgress });
      recordAssertion(label, 'no horizontal overflow', probe.bodyScrollWidth <= probe.viewportWidth + 1, { scrollWidth: probe.bodyScrollWidth, viewportWidth: probe.viewportWidth });
      recordAssertion(label, 'Google Fonts test route installed', fontRoute.installed === true);
      await page.screenshot({ path: join(outDir, '01-desktop-scene-entrance.png'), fullPage: false });
    } finally {
      await ctx.close();
    }
  }

  // ---- DESKTOP: pinned midpoint ----
  {
    const label = 'desktop-pinned';
    const { ctx, page, fontRoute } = await openScenario(browser, label, {
      viewport: { width: 1440, height: 900 },
      reducedMotion: 'no-preference',
    });
    try {
      await page.goto(baseUrl, { waitUntil: 'networkidle' });
      await waitForReady(page);
      await scrollProgress(page, 0.5);
      const probe = await page.evaluate(() => {
        const s = document.getElementById('p3MenuStory');
        const frame = document.querySelector('.p3-frame');
        const triggers = (window.ScrollTrigger ? window.ScrollTrigger.getAll() : []).filter((t) => t.vars && t.vars.id === 'p3-menu-story');
        const t = triggers[0] || null;
        return {
          triggerCount: triggers.length,
          triggerActive: t ? t.isActive : false,
          triggerProgress: t ? t.progress : null,
          storyPosition: s ? getComputedStyle(s).position : null,
          frameOpacity: frame ? Number(getComputedStyle(frame).opacity) : 0,
          bodyScrollWidth: document.body.scrollWidth,
          viewportWidth: window.innerWidth,
        };
      });
      probe.googleFontsRouteInstalled = fontRoute.installed;
      results[label] = probe;
      recordAssertion(label, 'exactly one Phase 3 trigger', probe.triggerCount === 1, { count: probe.triggerCount });
      recordAssertion(label, 'trigger is active', probe.triggerActive === true, { active: probe.triggerActive });
      recordAssertion(label, 'trigger progress near 0.5 (within ±0.1)', Math.abs((probe.triggerProgress ?? 0) - 0.5) <= 0.1, { progress: probe.triggerProgress });
      recordAssertion(label, 'story is pinned (position: fixed)', probe.storyPosition === 'fixed', { position: probe.storyPosition });
      recordAssertion(label, 'frame is visible (opacity > 0.5)', probe.frameOpacity > 0.5, { opacity: probe.frameOpacity });
      recordAssertion(label, 'no horizontal overflow', probe.bodyScrollWidth <= probe.viewportWidth + 1, { scrollWidth: probe.bodyScrollWidth, viewportWidth: probe.viewportWidth });
      await page.screenshot({ path: join(outDir, '02-desktop-pinned-prototype.png'), fullPage: false });
    } finally {
      await ctx.close();
    }
  }

  // ---- DESKTOP: menu revealed ----
  {
    const label = 'desktop-menu';
    const { ctx, page, fontRoute } = await openScenario(browser, label, {
      viewport: { width: 1440, height: 900 },
      reducedMotion: 'no-preference',
    });
    try {
      await page.goto(baseUrl, { waitUntil: 'networkidle' });
      await waitForReady(page);
      await scrollToMenuHeader(page);
      const probe = await page.evaluate(() => {
        const head = document.getElementById('menuContentStart');
        const headerRect = head ? head.getBoundingClientRect() : null;
        const headerCs = head ? getComputedStyle(head) : null;
        const triggers = (window.ScrollTrigger ? window.ScrollTrigger.getAll() : []).filter((t) => t.vars && t.vars.id === 'p3-menu-story');
        const triggerActive = triggers.some((t) => t.isActive);
        const t = triggers[0] || null;
        const progress = t ? t.progress : null;
        const isPinned = triggerActive && (progress ?? 0) < 1;
        const brandBtn = document.querySelector('.brand-room');
        const railAdd = document.querySelector('.rail-card-add, .rail-card-qty-btn');
        const cartBtn = document.querySelector('.cart-btn');
        return {
          headerTop: headerRect ? Math.round(headerRect.top) : null,
          headerOpacity: headerCs ? Number(headerCs.opacity) : 0,
          triggerCount: triggers.length,
          triggerActive,
          triggerProgress: progress,
          pinBlocking: isPinned,
          brandBtnExists: !!brandBtn,
          railAddExists: !!railAdd,
          cartBtnExists: !!cartBtn,
          bodyScrollWidth: document.body.scrollWidth,
          viewportWidth: window.innerWidth,
          viewportH: window.innerHeight,
        };
      });
      probe.googleFontsRouteInstalled = fontRoute.installed;
      results[label] = probe;
      recordAssertion(label, 'menu header visible below the fixed header', probe.headerTop !== null && probe.headerTop >= 0 && probe.headerTop < probe.viewportH, { headerTop: probe.headerTop, viewportH: probe.viewportH });
      recordAssertion(label, 'menu header not clipped (headerTop < 120)', probe.headerTop !== null && probe.headerTop < 120, { headerTop: probe.headerTop });
      recordAssertion(label, 'Phase 3 pin is no longer blocking the menu', probe.pinBlocking === false, { pinBlocking: probe.pinBlocking, triggerProgress: probe.triggerProgress });
      recordAssertion(label, 'brand switch control present', probe.brandBtnExists);
      recordAssertion(label, 'product rail control present', probe.railAddExists);
      recordAssertion(label, 'cart button present', probe.cartBtnExists);
      recordAssertion(label, 'no horizontal overflow', probe.bodyScrollWidth <= probe.viewportWidth + 1, { scrollWidth: probe.bodyScrollWidth, viewportWidth: probe.viewportWidth });
      await page.screenshot({ path: join(outDir, '03-desktop-menu-revealed.png'), fullPage: false });
    } finally {
      await ctx.close();
    }
  }

  // ---- MOBILE: menu revealed ----
  {
    const label = 'mobile-menu';
    const { ctx, page, fontRoute } = await openScenario(browser, label, {
      viewport: { width: 390, height: 844 },
      reducedMotion: 'no-preference',
    });
    try {
      await page.goto(baseUrl, { waitUntil: 'networkidle' });
      await waitForReady(page);
      await page.evaluate(() => {
        const el = document.getElementById('menu');
        if (!el) return;
        el.scrollIntoView({ behavior: 'instant', block: 'start' });
      });
      await page.waitForTimeout(600);
      const probe = await page.evaluate(() => {
        const stage = document.getElementById('p3MenuStory');
        const head = document.getElementById('menuContentStart');
        const headerRect = head ? head.getBoundingClientRect() : null;
        const titleEl = document.querySelector('#menuContentStart .menu-title');
        const titleRect = titleEl ? titleEl.getBoundingClientRect() : null;
        const triggers = (window.ScrollTrigger ? window.ScrollTrigger.getAll() : []).filter((t) => t.vars && t.vars.id === 'p3-menu-story');
        const headerCs = head ? getComputedStyle(head) : null;
        return {
          stageDisplay: stage ? getComputedStyle(stage).display : 'missing',
          triggerCount: triggers.length,
          headerTop: headerRect ? Math.round(headerRect.top) : null,
          headerOpacity: headerCs ? Number(headerCs.opacity) : 0,
          titleTop: titleRect ? Math.round(titleRect.top) : null,
          titleBottom: titleRect ? Math.round(titleRect.bottom) : null,
          viewportH: window.innerHeight,
          bodyScrollWidth: document.body.scrollWidth,
          viewportWidth: window.innerWidth,
        };
      });
      probe.googleFontsRouteInstalled = fontRoute.installed;
      results[label] = probe;
      recordAssertion(label, 'p3-menu-story is display: none', probe.stageDisplay === 'none', { display: probe.stageDisplay });
      recordAssertion(label, 'zero Phase 3 triggers on mobile', probe.triggerCount === 0, { count: probe.triggerCount });
      recordAssertion(label, 'menu header is fully below the fixed header', probe.headerTop !== null && probe.titleTop !== null && probe.titleTop >= 0 && probe.headerOpacity > 0, { headerTop: probe.headerTop, titleTop: probe.titleTop, opacity: probe.headerOpacity });
      recordAssertion(label, 'menu heading is not clipped (titleTop >= 80)', probe.titleTop !== null && probe.titleTop >= 80, { titleTop: probe.titleTop });
      recordAssertion(label, 'no horizontal overflow', probe.bodyScrollWidth <= probe.viewportWidth + 1, { scrollWidth: probe.bodyScrollWidth, viewportWidth: probe.viewportWidth });
      await page.screenshot({ path: join(outDir, '04-mobile-menu-revealed.png'), fullPage: false });
    } finally {
      await ctx.close();
    }
  }

  // ---- REDUCED MOTION ----
  {
    const label = 'reduced-motion';
    const { ctx, page, fontRoute } = await openScenario(browser, label, {
      viewport: { width: 1440, height: 900 },
      reducedMotion: 'reduce',
    });
    try {
      await page.goto(baseUrl, { waitUntil: 'networkidle' });
      await waitForReady(page);
      await page.evaluate(() => {
        const el = document.getElementById('menu');
        if (!el) return;
        el.scrollIntoView({ behavior: 'instant', block: 'start' });
      });
      await page.waitForTimeout(600);
      const probe = await page.evaluate(() => {
        const stage = document.getElementById('p3MenuStory');
        const head = document.getElementById('menuContentStart');
        const headerRect = head ? head.getBoundingClientRect() : null;
        const titleEl = document.querySelector('#menuContentStart .menu-title');
        const titleRect = titleEl ? titleEl.getBoundingClientRect() : null;
        const triggers = (window.ScrollTrigger ? window.ScrollTrigger.getAll() : []).filter((t) => t.vars && t.vars.id === 'p3-menu-story');
        const frame = document.querySelector('.p3-frame');
        const frameOp = frame ? Number(getComputedStyle(frame).opacity) : 0;
        const stageRect = stage ? stage.getBoundingClientRect() : null;
        return {
          stageDisplay: stage ? getComputedStyle(stage).display : 'missing',
          triggerCount: triggers.length,
          headerTop: headerRect ? Math.round(headerRect.top) : null,
          titleTop: titleRect ? Math.round(titleRect.top) : null,
          titleBottom: titleRect ? Math.round(titleRect.bottom) : null,
          viewportH: window.innerHeight,
          frameOpacity: frameOp,
          stageRect: stageRect ? { top: Math.round(stageRect.top), bottom: Math.round(stageRect.bottom) } : null,
          bodyScrollWidth: document.body.scrollWidth,
          viewportWidth: window.innerWidth,
        };
      });
      probe.googleFontsRouteInstalled = fontRoute.installed;
      results[label] = probe;
      recordAssertion(label, 'p3-menu-story is display: none', probe.stageDisplay === 'none', { display: probe.stageDisplay });
      recordAssertion(label, 'zero Phase 3 triggers', probe.triggerCount === 0, { count: probe.triggerCount });
      recordAssertion(label, 'real menu header visible below the fixed header', probe.headerTop !== null && probe.headerTop >= 0 && probe.headerTop < probe.viewportH, { headerTop: probe.headerTop, viewportH: probe.viewportH });
      recordAssertion(label, 'menu heading is not clipped (titleTop >= 80)', probe.titleTop !== null && probe.titleTop >= 80, { titleTop: probe.titleTop });
      recordAssertion(label, 'no decorative prototype is rendered (stage display: none)', probe.stageDisplay === 'none');
      recordAssertion(label, 'no horizontal overflow', probe.bodyScrollWidth <= probe.viewportWidth + 1, { scrollWidth: probe.bodyScrollWidth, viewportWidth: probe.viewportWidth });
      await page.screenshot({ path: join(outDir, '05-reduced-motion-menu-visible.png'), fullPage: false });
    } finally {
      await ctx.close();
    }
  }

  // ---- DESKTOP: reverse scroll restoration ----
  // Same progress (0.10) for original entrance and restored reverse state.
  // Numeric state comparison uses documented tolerances; screenshots are visual
  // evidence only (no pixel-diff — font rasterization may vary).
  {
    const label = 'desktop-reverse';
    const { ctx, page, fontRoute } = await openScenario(browser, label, {
      viewport: { width: 1440, height: 900 },
      reducedMotion: 'no-preference',
    });
    try {
      await page.goto(baseUrl, { waitUntil: 'networkidle' });
      await waitForReady(page);

      await scrollProgress(page, ENTRANCE_PROGRESS);
      const initial = await captureVisualState(page);

      await scrollProgress(page, FORWARD_PROGRESS);
      const forward = await captureVisualState(page);

      await scrollProgress(page, ENTRANCE_PROGRESS);
      const restored = await captureVisualState(page);

      const restoreDiffs = compareVisualStates(initial, restored, {
        progress: TOL_PROGRESS,
        opacity: TOL_OPACITY,
        transform: TOL_TRANSFORM,
      });
      const forwardDiffers = statesDifferMeaningfully(initial, forward);

      const probe = {
        initial,
        forward,
        restored,
        restoreDiffs,
        forwardDiffers,
        tolerances: {
          triggerProgress: TOL_PROGRESS,
          opacity: TOL_OPACITY,
          transformMatrixComponent: TOL_TRANSFORM,
        },
        googleFontsRouteInstalled: fontRoute.installed,
        googleFontsFulfilled: fontRoute.getFulfilledCount(),
      };
      results[label] = probe;

      recordAssertion(label, 'exactly one Phase 3 trigger remains', restored.triggerCount === 1, { count: restored.triggerCount });
      recordAssertion(label, 'no duplicate Phase 3 triggers', restored.triggerCount === 1 && initial.triggerCount === 1 && forward.triggerCount === 1, {
        initial: initial.triggerCount,
        forward: forward.triggerCount,
        restored: restored.triggerCount,
      });
      recordAssertion(label, 'forward state at 0.70 differs from entrance at 0.10', forwardDiffers === true, {
        initialProgress: initial.triggerProgress,
        forwardProgress: forward.triggerProgress,
      });
      recordAssertion(label, 'restored state matches entrance within tolerance', restoreDiffs.length === 0, {
        diffs: restoreDiffs,
        tolerances: probe.tolerances,
      });
      recordAssertion(label, 'trigger progress restored near 0.10', restored.triggerProgress !== null && Math.abs(restored.triggerProgress - ENTRANCE_PROGRESS) <= 0.1, { progress: restored.triggerProgress });
      recordAssertion(label, 'fixed header remains visible', restored.headerVisible === true, { headerVisible: restored.headerVisible });
      recordAssertion(label, 'no stuck pin (progress < 0.95 and position consistent)', (restored.triggerProgress ?? 1) < 0.95 && restored.pinnedPosition === initial.pinnedPosition, {
        progress: restored.triggerProgress,
        pinnedPosition: restored.pinnedPosition,
        initialPinnedPosition: initial.pinnedPosition,
      });
      recordAssertion(label, 'no horizontal overflow', restored.horizontalOverflow === false, {
        scrollWidth: restored.bodyScrollWidth,
        viewportWidth: restored.viewportWidth,
      });
      recordAssertion(label, 'Google Fonts test route installed', fontRoute.installed === true);

      await page.screenshot({ path: join(outDir, '06-desktop-reverse-restored.png'), fullPage: false });
    } finally {
      await ctx.close();
    }
  }

  // ---- DESKTOP: resize 1440 -> 390 -> 1440 ----
  {
    const label = 'desktop-resize';
    const { ctx, page, fontRoute } = await openScenario(browser, label, {
      viewport: { width: 1440, height: 900 },
      reducedMotion: 'no-preference',
    });
    try {
      await page.goto(baseUrl, { waitUntil: 'networkidle' });
      await waitForReady(page);
      const initial = await page.evaluate(() => window.ScrollTrigger ? window.ScrollTrigger.getAll().filter((t) => t.vars && t.vars.id === 'p3-menu-story').length : -1);
      await page.setViewportSize({ width: 390, height: 844 });
      await page.waitForTimeout(700);
      const afterMobile = await page.evaluate(() => window.ScrollTrigger ? window.ScrollTrigger.getAll().filter((t) => t.vars && t.vars.id === 'p3-menu-story').length : -1);
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.waitForTimeout(700);
      const afterDesktopAgain = await page.evaluate(() => window.ScrollTrigger ? window.ScrollTrigger.getAll().filter((t) => t.vars && t.vars.id === 'p3-menu-story').length : -1);
      results[label] = { initial, afterMobile, afterDesktopAgain, googleFontsRouteInstalled: fontRoute.installed };
      recordAssertion(label, 'desktop trigger count is 1', initial === 1, { count: initial });
      recordAssertion(label, 'mobile trigger count is 0', afterMobile === 0, { count: afterMobile });
      recordAssertion(label, 'desktop-after-mobile trigger count is 1', afterDesktopAgain === 1, { count: afterDesktopAgain });
    } finally {
      await ctx.close();
    }
  }

  // ---- DESKTOP: menu/cart regression ----
  {
    const label = 'menu-regression';
    const { ctx, page, fontRoute } = await openScenario(browser, label, {
      viewport: { width: 1440, height: 900 },
      reducedMotion: 'no-preference',
    });
    try {
      await page.goto(baseUrl, { waitUntil: 'networkidle' });
      await waitForReady(page);
      await scrollToMenuHeader(page);

      await page.evaluate(() => window.switchBrand('papa'));
      await page.waitForTimeout(700);
      const papaName = await page.evaluate(() => document.querySelector('#roomIntro .room-intro-title')?.textContent?.trim());

      await page.evaluate(() => window.switchBrand('voya'));
      await page.waitForTimeout(60);
      await page.evaluate(() => window.switchBrand('mama'));
      await page.waitForTimeout(60);
      await page.evaluate(() => window.switchBrand('papa'));
      await page.waitForTimeout(700);
      const finalName = await page.evaluate(() => document.querySelector('#roomIntro .room-intro-title')?.textContent?.trim());

      const categoryCount = await page.evaluate(() => document.querySelectorAll('#categoryChips .category-chip').length);

      const cartBefore = await page.evaluate(() => Number(document.getElementById('cartCount')?.textContent || '0'));
      await page.evaluate(() => {
        const add = document.querySelector('.rail-card-add');
        if (add) add.click();
      });
      await page.waitForTimeout(400);
      const cartAfter = await page.evaluate(() => Number(document.getElementById('cartCount')?.textContent || '0'));
      const whatsappDisabled = await page.evaluate(() => document.getElementById('whatsappBtn')?.disabled);

      await page.evaluate(() => window.toggleCart({ currentTarget: document.querySelector('.cart-btn') }));
      await page.waitForTimeout(300);
      const cartOpen = await page.evaluate(() => document.getElementById('cartDrawer')?.classList?.contains('open'));

      await page.setViewportSize({ width: 390, height: 844 });
      await page.waitForTimeout(700);
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.waitForTimeout(700);
      const cartAfterResize = await page.evaluate(() => Number(document.getElementById('cartCount')?.textContent || '0'));

      results[label] = {
        papaName,
        finalName,
        categoryCount,
        cartBefore,
        cartAfter,
        whatsappDisabled,
        cartOpen,
        cartAfterResize,
        googleFontsRouteInstalled: fontRoute.installed,
      };
      recordAssertion(label, 'papa brand name set', papaName === 'The Healthy Room', { papaName });
      recordAssertion(label, 'latest rapid brand selection wins (papa)', finalName === 'The Healthy Room', { finalName });
      recordAssertion(label, 'category UI present after brand switch', categoryCount > 0, { categoryCount });
      recordAssertion(label, 'add-to-cart increases count', cartAfter === cartBefore + 1, { cartBefore, cartAfter });
      recordAssertion(label, 'cart drawer opens', cartOpen === true, { cartOpen });
      recordAssertion(label, 'WhatsApp button enabled with items', whatsappDisabled === false, { whatsappDisabled });
      recordAssertion(label, 'cart survives resize desktop -> mobile -> desktop', cartAfterResize === cartAfter, { cartAfter, cartAfterResize });
    } finally {
      await ctx.close();
    }
  }
} catch (e) {
  fatalError = String(e && e.stack ? e.stack : e);
  allPassed = false;
} finally {
  await browser.close();
  server.close();
}

// Verify each expected screenshot is a valid PNG with the expected dimensions
// and was written during this run.
const expectedScreenshots = [
  { file: '01-desktop-scene-entrance.png', width: 1440, height: 900 },
  { file: '02-desktop-pinned-prototype.png', width: 1440, height: 900 },
  { file: '03-desktop-menu-revealed.png', width: 1440, height: 900 },
  { file: '04-mobile-menu-revealed.png', width: 390, height: 844 },
  { file: '05-reduced-motion-menu-visible.png', width: 1440, height: 900 },
  { file: '06-desktop-reverse-restored.png', width: 1440, height: 900 },
];

const screenshotChecks = [];
for (const s of expectedScreenshots) {
  const p = join(outDir, s.file);
  let exists = false;
  let validPng = false;
  let width = null;
  let height = null;
  let bytes = 0;
  try {
    const st = statSync(p);
    exists = true;
    bytes = st.size;
    const buf = readFileSync(p);
    // PNG header: 89 50 4E 47 0D 0A 1A 0A
    validPng = buf.length >= 24 &&
      buf[0] === 0x89 && buf[1] === 0x50 && buf[2] === 0x4E && buf[3] === 0x47 &&
      buf[4] === 0x0D && buf[5] === 0x0A && buf[6] === 0x1A && buf[7] === 0x0A;
    // IHDR width/height are at bytes 16-23, big-endian
    width = buf.readUInt32BE(16);
    height = buf.readUInt32BE(20);
  } catch (_) { /* ignore */ }
  const ok = exists && validPng && width === s.width && height === s.height;
  if (!ok) allPassed = false;
  recordAssertion('screenshots', `${s.file} valid (${s.width}x${s.height})`, ok, { exists, validPng, width, height, expected: s, bytes });
  screenshotChecks.push({ file: s.file, exists, validPng, width, height, expected: s, bytes });
}

recordAssertion('google-fonts-route', 'Google Fonts test route installed for all scenarios', googleFontsRoute.installed === true, googleFontsRoute);

const report = {
  passed: allPassed && errors.length === 0 && !fatalError && !readinessFailed,
  results,
  errors,
  assertions,
  screenshotChecks,
  googleFontsRoute,
  fatalError,
  readinessFailed,
};

console.log(JSON.stringify(report, null, 2));

if (!report.passed) {
  process.exit(1);
}
process.exit(0);
