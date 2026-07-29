// Record two real browser clients playing the delivered game over
// WebSockets — as two iframes in one 1280x720 page, so both boards
// share one recording clock and their sync is visible truthfully.
// Usage: node record-gameplay.mjs <repo-dir> <out-dir> [port]
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { renameSync } from 'node:fs';
import { join } from 'node:path';

const [repo, outDir, portArg] = process.argv.slice(2);
if (!repo || !outDir) { console.error('usage: node record-gameplay.mjs <repo> <out-dir> [port]'); process.exit(1); }
const port = portArg || '8340';

const server = spawn('node', ['.'], {
  cwd: repo, env: { ...process.env, PORT: port, HOST: '127.0.0.1' }, stdio: 'ignore',
});
const stop = () => { try { server.kill(); } catch {} };
process.on('exit', stop);
await new Promise(r => setTimeout(r, 1800));

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 1280, height: 720 },
  recordVideo: { dir: outDir, size: { width: 1280, height: 720 } },
});
const page = await ctx.newPage();
await page.setContent(`<!doctype html><style>
  body { margin:0; display:flex; height:100vh; background:#eef1f6; }
  iframe { flex:1; border:0; height:100%; }
  iframe:first-child { border-right: 2px solid #cbd2dd; }
</style>
<iframe id="px" src="http://127.0.0.1:${port}/"></iframe>
<iframe id="po" src="http://127.0.0.1:${port}/"></iframe>`);
await page.waitForTimeout(3000);

const x = page.frameLocator('#px');
const o = page.frameLocator('#po');
const sq = (f, i) => f.locator(`[data-index="${i}"]`).click();
const beat = () => page.waitForTimeout(1400);

// A real game on one clock: X takes the top row.
await sq(x, 0); await beat();
await sq(o, 4); await beat();
await sq(x, 1); await beat();
await sq(o, 5); await beat();
await sq(x, 2); await page.waitForTimeout(3000);   // the win, savored

// New game, both boards reset together.
await x.locator('#reset, .reset').first().click();
await page.waitForTimeout(2200);
await sq(x, 4); await beat();
await sq(o, 8); await beat();
await page.waitForTimeout(1800);

const videoPath = await page.video().path();
await ctx.close();
renameSync(videoPath, join(outDir, 'gameplay.webm'));
console.log('video:', join(outDir, 'gameplay.webm'));
await browser.close();
stop();
