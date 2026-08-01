import { chromium } from '../baseline/node_modules/playwright/index.mjs';
import { createServer } from 'http';
import { readFileSync, existsSync, mkdirSync } from 'fs';
import { join, extname } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '../..');
const port = 8766;

const characterArg = process.argv.find((arg) => arg.startsWith('--character='));
const scopedCharacter = characterArg ? characterArg.split('=')[1] : null;
if (scopedCharacter && !['papa', 'mama', 'voya'].includes(scopedCharacter)) {
  console.error(`Invalid character: ${scopedCharacter}`);
  process.exit(1);
}

const mime = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
};

const server = createServer((req, res) => {
  let path = req.url.split('?')[0];
  if (path === '/') path = '/docs/phase2/reassembly-preview.html';
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
const characters = scopedCharacter ? [scopedCharacter] : ['papa', 'mama', 'voya'];
const viewports = {
  desktop: { width: 1440, height: 900 },
  mobile: { width: 390, height: 844 },
};

async function waitForPreviewReady(page, expected) {
  const errors = [];
  page.on('pageerror', (err) => errors.push(`pageerror: ${err.message}`));
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(`console: ${msg.text()}`);
  });
  page.on('requestfailed', (req) => {
    errors.push(`requestfailed: ${req.url()} ${req.failure()?.errorText || ''}`);
  });

  await page.goto(expected.url, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => {
    const status = document.getElementById('status');
    return status && status.dataset.ready === '1';
  }, null, { timeout: 15000 });

  const stageMeta = await page.evaluate((exp) => {
    const stage = document.querySelector('.stage');
    if (!stage) return { ok: false, reason: 'missing .stage' };
    if (stage.dataset.character !== exp.character) {
      return { ok: false, reason: `character ${stage.dataset.character} != ${exp.character}` };
    }
    if (stage.dataset.pose !== exp.pose && !(exp.pose === 'fallback' || exp.pose === 'reduced-motion')) {
      // fallback/reduced-motion render as neutral layers but keep pose dataset
    }
    if (stage.dataset.viewport !== exp.viewport) {
      return { ok: false, reason: `viewport ${stage.dataset.viewport} != ${exp.viewport}` };
    }
    const imgs = [...stage.querySelectorAll('img')];
    if (!imgs.length) return { ok: false, reason: 'no images in stage' };
    for (const img of imgs) {
      if (!img.complete || img.naturalWidth <= 0) {
        return { ok: false, reason: `image not loaded: ${img.alt || img.src}` };
      }
    }
    return {
      ok: true,
      pose: stage.dataset.pose,
      layer: stage.dataset.layer,
      imageCount: imgs.length,
      naturalWidths: imgs.map((img) => img.naturalWidth),
    };
  }, expected);

  if (!stageMeta.ok) {
    throw new Error(`Preview not ready (${expected.url}): ${stageMeta.reason}`);
  }
  if (errors.length) {
    throw new Error(`Preview errors for ${expected.url}: ${errors.join('; ')}`);
  }
  return stageMeta;
}

async function captureShot(page, outPath, expected) {
  await waitForPreviewReady(page, expected);
  const viewportEl = page.locator('.stage-viewport');
  const box = await viewportEl.boundingBox();
  const expectedSize = viewports[expected.viewport];
  if (!box || Math.round(box.width) !== expectedSize.width || Math.round(box.height) !== expectedSize.height) {
    throw new Error(
      `Stage viewport size mismatch for ${outPath}: got ${box && box.width}x${box && box.height}, expected ${expectedSize.width}x${expectedSize.height}`
    );
  }
  await viewportEl.screenshot({ path: outPath });
}

async function captureCharacter(character) {
  const outDir = join(__dirname, 'evidence', character, 'browser');
  mkdirSync(outDir, { recursive: true });

  const manifestPath = join(root, 'assets/scenes', character, 'manifest.json');
  if (!existsSync(manifestPath)) {
    throw new Error(`Missing manifest: ${manifestPath}`);
  }
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  if (manifest.character !== character) {
    throw new Error(`Manifest character mismatch for ${character}`);
  }
  for (const layer of manifest.layers) {
    const layerPath = join(root, 'assets/scenes', character, layer.file);
    if (!existsSync(layerPath)) {
      throw new Error(`Missing layer file: ${layerPath}`);
    }
  }
  const motionLayers = manifest.layers.filter((layer) => layer.motion);

  for (const [viewportName, viewport] of Object.entries(viewports)) {
    const page = await browser.newPage({ viewport });

    const captureQs = 'capture=1';

    await captureShot(page, join(outDir, `neutral_reconstruction_${viewportName}.png`), {
      url: `${baseUrl}/docs/phase2/reassembly-preview.html?${captureQs}&character=${character}&layer=all&pose=neutral&viewport=${viewportName}`,
      character,
      pose: 'neutral',
      viewport: viewportName,
    });

    // Static head evidence when head motion is blocked.
    const headLayer = manifest.layers.find((layer) => layer.id.endsWith('-head'));
    if (headLayer && !headLayer.motion) {
      await captureShot(page, join(outDir, `${headLayer.id}_static_${viewportName}.png`), {
        url: `${baseUrl}/docs/phase2/reassembly-preview.html?${captureQs}&character=${character}&layer=all&pose=neutral&viewport=${viewportName}`,
        character,
        pose: 'neutral',
        viewport: viewportName,
      });
    }

    for (const layer of motionLayers) {
      for (const pose of ['neutral', 'min', 'max']) {
        await captureShot(page, join(outDir, `${layer.id}_${pose}_${viewportName}.png`), {
          url: `${baseUrl}/docs/phase2/reassembly-preview.html?${captureQs}&character=${character}&layer=${layer.id}&pose=${pose}&viewport=${viewportName}`,
          character,
          pose,
          viewport: viewportName,
        });
      }
    }

    for (const pose of ['combined-min', 'combined-max']) {
      await captureShot(
        page,
        join(outDir, `combined_${pose.replace('combined-', '')}_${viewportName}.png`),
        {
          url: `${baseUrl}/docs/phase2/reassembly-preview.html?${captureQs}&character=${character}&layer=all&pose=${pose}&viewport=${viewportName}`,
          character,
          pose,
          viewport: viewportName,
        }
      );
    }

    for (const pose of ['fallback', 'reduced-motion']) {
      const filename = pose === 'fallback' ? `fallback_${viewportName}.png` : `reduced_motion_${viewportName}.png`;
      await captureShot(page, join(outDir, filename), {
        url: `${baseUrl}/docs/phase2/reassembly-preview.html?${captureQs}&character=${character}&pose=${pose}&viewport=${viewportName}`,
        character,
        pose,
        viewport: viewportName,
      });
    }

    await page.close();
  }

  return motionLayers.length;
}

let exitCode = 0;
try {
  const summary = {};
  for (const character of characters) {
    summary[character] = await captureCharacter(character);
  }
  console.log(JSON.stringify({ scopedCharacter, captured: summary }, null, 2));
} catch (error) {
  console.error(String(error && error.stack ? error.stack : error));
  exitCode = 1;
} finally {
  await browser.close();
  server.close();
}
process.exit(exitCode);
