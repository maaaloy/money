// Рендер сцен в видео: Playwright снимает кадры scenes/index.html, ffmpeg кодирует.
//   node tools/render.mjs preview 1.5 20 64      — PNG отдельных кадров в render/preview/
//   node tools/render.mjs video [воркеров=4]      — render/video.mp4 (без звука) + render/timeline.json
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const { chromium } = createRequire(import.meta.url)('playwright');
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const FPS = 30;
const { words } = JSON.parse(readFileSync(`${ROOT}/audio/words.json`, 'utf8'));
const voiceEnd = words[words.length - 1].e;
const [mode = 'video', ...args] = process.argv.slice(2);
mkdirSync(`${ROOT}/render/preview`, { recursive: true });

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', (e) => { console.error('page error:', e.message); process.exit(1); });
  await page.goto(`file://${ROOT}/scenes/index.html`);
  await page.evaluate(() => document.fonts.ready);
  const total = await page.evaluate(([w, v]) => window.setup(w, v), [words, voiceEnd]);
  return { page, total };
}

const browser = await chromium.launch();
if (mode === 'preview') {
  const { page } = await openPage(browser);
  for (const t of args.map(Number)) {
    await page.evaluate((t) => window.renderAt(t), t);
    await page.screenshot({ path: `${ROOT}/render/preview/t${t.toFixed(1)}.png` });
  }
} else {
  const workers = Number(args[0] || 4);
  const { page, total } = await openPage(browser);
  const timeline = await page.evaluate(() => SC.map((s) => ({ t0: s.t0, t1: s.t1, K: s.K })));
  writeFileSync(`${ROOT}/render/timeline.json`, JSON.stringify({ total, voiceEnd, scenes: timeline }, null, 1));
  await page.close();
  const frames = Math.ceil(total * FPS);
  const per = Math.ceil(frames / workers);
  let done = 0;
  await Promise.all([...Array(workers)].map(async (_, w) => {
    const { page } = await openPage(browser);
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', `${ROOT}/render/part${w}.mp4`],
      { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = w * per; f < Math.min(frames, (w + 1) * per); f++) {
      await page.evaluate((t) => window.renderAt(t), f / FPS);
      const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
      if (++done % 300 === 0) console.log(`${done}/${frames}`);
    }
    ff.stdin.end();
    await new Promise((r) => ff.on('close', r));
  }));
  writeFileSync(`${ROOT}/render/parts.txt`, [...Array(workers)].map((_, w) => `file 'part${w}.mp4'`).join('\n'));
  await new Promise((r) => spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', `${ROOT}/render/parts.txt`,
    '-c', 'copy', `${ROOT}/render/video.mp4`], { stdio: 'inherit' }).on('close', r));
  console.log(`готово: ${frames} кадров, ${total.toFixed(2)} с`);
}
await browser.close();
