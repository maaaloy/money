// node render.js timeline.json voice.wav out.mp4 — покадровый рендер template.html в MP4 1080x1920 30fps
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const [tlPath, voice, out] = process.argv.slice(2);
const FPS = 30;

(async () => {
  const tl = JSON.parse(fs.readFileSync(tlPath, 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.join(__dirname, 'template.html'));
  await page.evaluate(t => window.setTimeline(t), tl);
  await page.evaluate(() => document.fonts.ready);

  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-i', voice, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
    '-af', 'apad', '-t', String(tl.duration), '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });

  const frames = Math.ceil(tl.duration * FPS);
  for (let i = 0; i < frames; i++) {
    await page.evaluate(t => window.render(t), i / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 90 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 300 === 0) process.stderr.write(`frame ${i}/${frames}\n`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
})();
