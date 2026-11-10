// Рендер оформления канала: node shoot.cjs → banner.png, avatar.png, watermark.png
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 2560, height: 1440 } });
  await p.goto(`file://${__dirname}/brand.html`);
  await p.evaluate(() => document.fonts.ready);
  await p.locator('#banner').screenshot({ path: `${__dirname}/banner.png` });
  await p.locator('#avatar').screenshot({ path: `${__dirname}/avatar.png` });
  await p.locator('#mark').screenshot({ path: `${__dirname}/watermark.png`, omitBackground: true });
  await b.close();
})();
