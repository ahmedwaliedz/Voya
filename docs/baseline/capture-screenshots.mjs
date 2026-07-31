import { chromium } from 'playwright';
import { createServer } from 'http';
import { readFileSync, existsSync } from 'fs';
import { join, extname } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '../..');
const port = 8765;

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
const sections = [
  { name: '01-hero', selector: '#home' },
  { name: '02-story', selector: '#story' },
  { name: '03-moods', selector: '#moods' },
  { name: '04-menu-voya', selector: '#menu' },
  { name: '05-locations', selector: '#locations' },
  { name: '06-footer', selector: '#contact' },
];

async function capture(viewport, folder, suffix = '') {
  const page = await browser.newPage({ viewport });
  await page.goto(baseUrl, { waitUntil: 'networkidle' });
  await page.waitForTimeout(4000);

  await page.screenshot({
    path: join(__dirname, 'screenshots', folder, `00-full-page${suffix}.png`),
    fullPage: true,
  });

  for (const { name, selector } of sections) {
    const el = page.locator(selector);
    if (await el.count()) {
      await el.scrollIntoViewIfNeeded();
      await page.waitForTimeout(600);
      await el.screenshot({
        path: join(__dirname, 'screenshots', folder, `${name}${suffix}.png`),
      });
    }
  }

  if (folder === 'desktop') {
    await page.locator('button.brand-room--papa').click();
    await page.waitForTimeout(900);
    await page.locator('#menu').screenshot({
      path: join(__dirname, 'screenshots', folder, '04-menu-papa.png'),
    });

    await page.locator('button.brand-room--mama').click();
    await page.waitForTimeout(900);
    await page.locator('#menu').screenshot({
      path: join(__dirname, 'screenshots', folder, '04-menu-mama.png'),
    });

    await page.locator('.rail-card-add').first().click();
    await page.waitForTimeout(400);
    await page.locator('#cartDrawer').screenshot({
      path: join(__dirname, 'screenshots', folder, '07-cart-drawer.png'),
    });
  }

  const errors = [];
  page.on('pageerror', (err) => errors.push(err.message));
  await page.close();
  return errors;
}

const desktopErrors = await capture({ width: 1440, height: 900 }, 'desktop');
const mobileErrors = await capture({ width: 390, height: 844 }, 'mobile');

await browser.close();
server.close();

console.log(JSON.stringify({ desktopErrors, mobileErrors }, null, 2));
