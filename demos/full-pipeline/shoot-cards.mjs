import { chromium } from 'playwright';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
for (const k of ['title', 'end']) {
  await p.goto(`file://${process.cwd()}/card.html?${Date.now()}#${k === 'end' ? 'end' : 'title'}`);
  await p.waitForTimeout(400);
  await p.screenshot({ path: `${k}.png` });
}
await b.close();
