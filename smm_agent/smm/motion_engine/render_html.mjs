// Frame-exact renderer for AI-authored designs.
// usage: node render_html.mjs <design.html> <out_dir> <fps> [<duration_override>]
// The design is a full HTML page sized 1080x1920. It must expose window.__duration (seconds) and either
//   window.__tl  : a PAUSED GSAP timeline, and/or
//   CSS / Web Animations (the engine pauses them and sets currentTime).
// For each frame the engine seeks every timeline to t and screenshots with a transparent background,
// writing frame_00000.png ... plus text.json: every visible text string per sampled second (for exact
// fact verification - the pixels come from the browser font engine, so DOM text == on-screen text).
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [, , designPath, outDir, fpsArg, durArg] = process.argv;
const fps = Number(fpsArg || 30);
fs.mkdirSync(outDir, { recursive: true });
const exe = process.env.CHROMIUM_PATH || undefined;
const browser = await chromium.launch({ executablePath: exe, args: ['--font-render-hinting=none', '--disable-lcd-text'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
const errors = [];
page.on('pageerror', e => errors.push(String(e)));
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
await page.goto(pathToFileURL(path.resolve(designPath)).href, { waitUntil: 'load' });
await page.evaluate(async () => { await document.fonts.ready; });
await page.addStyleTag({ content: '*{caret-color:transparent!important}' });
const duration = Number(durArg) || await page.evaluate(() => window.__duration);
if (!duration || !(duration > 0)) { console.error('design must set window.__duration'); process.exit(2); }
// Typography hygiene, not style: a price, phone or number+unit must never break across lines ("22 / 100 ₸").
// Same rule as smm/textutil.py UNBREAKABLE; re-applied every frame in case the timeline changes text.
await page.evaluate(() => {
  window.__glue = () => {
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = w.nextNode())) {
      if (node.parentElement && /^(SCRIPT|STYLE)$/.test(node.parentElement.tagName)) continue;
      const s0 = node.textContent;
      const s = s0.replace(/\+?\d[\d ]{6,}\d/g, m => m.replace(/ /g, '\u00A0'))
                  .replace(/(\d) (?=\d{3}(?!\d))/g, '$1\u00A0')
                  .replace(/(\d) (?=(₸|тг|тенге|%|шт|кг|дн|мес))/g, '$1\u00A0');
      if (s !== s0) node.textContent = s;
    }
  };
  window.__glue();
});
await page.evaluate(() => {
  if (window.gsap) { gsap.ticker.lagSmoothing(0); gsap.globalTimeline.pause(); }
  for (const a of document.getAnimations()) a.pause();
});
const n = Math.round(duration * fps);
const texts = [];
for (let i = 0; i < n; i++) {
  const t = i / fps;
  await page.evaluate((t) => {
    if (window.__tl) window.__tl.seek(t, false);
    if (window.gsap) gsap.globalTimeline.seek(t, false);
    for (const a of document.getAnimations()) a.currentTime = t * 1000;
    if (window.__onSeek) window.__onSeek(t);
    window.__glue();
  }, t);
  await page.screenshot({ path: path.join(outDir, `frame_${String(i).padStart(5, '0')}.png`), omitBackground: true });
  if (i % fps === 0 || i === n - 1) {
    const visible = await page.evaluate(() => {
      const out = [];
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        const s = node.textContent.replace(/\s+/g, ' ').trim();
        if (!s) continue;
        const el = node.parentElement; const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
        const op = parseFloat(cs.opacity);
        let o = el, eff = 1; while (o) { eff *= parseFloat(getComputedStyle(o).opacity); o = o.parentElement; }
        if (cs.visibility !== 'hidden' && cs.display !== 'none' && eff > 0.05 && r.width > 0 && r.height > 0 &&
            r.bottom > 0 && r.right > 0 && r.top < 1920 && r.left < 1080)
          out.push({ text: s, box: [Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)], opacity: +eff.toFixed(2), font: cs.fontFamily.split(',')[0], size: cs.fontSize });
      }
      return out;
    });
    texts.push({ t: +t.toFixed(2), visible });
  }
}
fs.writeFileSync(path.join(outDir, 'text.json'), JSON.stringify({ duration, fps, frames: n, errors, texts }, null, 1));
await browser.close();
console.log(JSON.stringify({ frames: n, duration, errors: errors.length }));
