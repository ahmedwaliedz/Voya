import { chromium } from '../baseline/node_modules/playwright/index.mjs';
import { createServer } from 'http';
import { readFileSync, existsSync, mkdirSync, writeFileSync } from 'fs';
import { join, extname, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '../..');
const port = 8767;
const mime = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
};

const html = `<!doctype html>
<html><head><meta charset="utf-8"><style>
html,body{margin:0;background:#ddd4c4;overflow:hidden}
.stage-viewport{display:flex;align-items:center;justify-content:center;background:
  linear-gradient(45deg,#ddd4c4 25%,#cfc4b0 25%,#cfc4b0 50%,#ddd4c4 50%,#ddd4c4 75%,#cfc4b0 75%,#cfc4b0);
  background-size:24px 24px}
img{max-width:92%;max-height:92%;object-fit:contain;display:block}
</style></head>
<body>
<div class="stage-viewport" id="vp"><img id="house" alt="house static"></div>
<script>
const params=new URLSearchParams(location.search);
const w=Number(params.get('w')||1440), h=Number(params.get('h')||900);
const vp=document.getElementById('vp');
vp.style.width=w+'px'; vp.style.height=h+'px';
const img=document.getElementById('house');
img.onload=()=>{ document.body.dataset.ready='1'; };
img.onerror=()=>{ document.body.dataset.ready='0'; document.body.dataset.error='image load failed'; };
img.src='/assets/scenes/house/house-static.png';
</script>
</body></html>`;

const previewPath = join(__dirname, '_house-fit-preview.html');
writeFileSync(previewPath, html, 'utf8');

const server = createServer((req, res) => {
  let path = req.url.split('?')[0];
  if (path === '/' || path.endsWith('house-fit-preview.html')) {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(readFileSync(previewPath));
    return;
  }
  const filePath = join(root, path.replace(/^\//, ''));
  if (!existsSync(filePath)) {
    res.writeHead(404);
    res.end('Not found');
    return;
  }
  res.writeHead(200, { 'Content-Type': mime[extname(filePath)] || 'application/octet-stream' });
  res.end(readFileSync(filePath));
});

await new Promise((resolve) => server.listen(port, resolve));
const browser = await chromium.launch();
const outDir = join(__dirname, 'evidence', 'house', 'browser');
mkdirSync(outDir, { recursive: true });
const viewports = { desktop: { width: 1440, height: 900 }, mobile: { width: 390, height: 844 } };

try {
  for (const [name, size] of Object.entries(viewports)) {
    const page = await browser.newPage({ viewport: size });
    const errors = [];
    page.on('pageerror', (err) => errors.push(err.message));
    page.on('requestfailed', (req) => errors.push(`requestfailed ${req.url()}`));
    await page.goto(`http://127.0.0.1:${port}/docs/phase2/_house-fit-preview.html?w=${size.width}&h=${size.height}`, {
      waitUntil: 'networkidle',
    });
    await page.waitForFunction(() => document.body.dataset.ready === '1', null, { timeout: 10000 });
    if (errors.length) throw new Error(errors.join('; '));
    const box = await page.locator('.stage-viewport').boundingBox();
    if (!box || Math.round(box.width) !== size.width || Math.round(box.height) !== size.height) {
      throw new Error(`viewport mismatch ${box && box.width}x${box && box.height}`);
    }
    await page.locator('.stage-viewport').screenshot({ path: join(outDir, `house_fit_${name}.png`) });
    await page.close();
  }
  console.log(JSON.stringify({ captured: { house: Object.keys(viewports).length }, outDir }, null, 2));
} finally {
  await browser.close();
  server.close();
}
