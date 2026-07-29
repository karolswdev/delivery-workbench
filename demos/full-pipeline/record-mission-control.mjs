// Record Mission Control while the live program run ticks.
// Usage: node record-mission-control.mjs <repo-dir> <run-id> <out-dir> <done-file> [port]
// Records the run page, reloading periodically, until done-file exists
// (the live tape writes .tmp/supervise.json when supervise returns) or 30 min.
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { renameSync } from 'node:fs';
import { join } from 'node:path';
import { existsSync } from 'node:fs';

const [repo, runId, outDir, doneFile, portArg] = process.argv.slice(2);
if (!repo || !runId || !outDir || !doneFile) {
  console.error('usage: node record-mission-control.mjs <repo> <run-id> <out-dir> <done-file> [port]');
  process.exit(1);
}
const port = portArg || '8399';
const base = `http://127.0.0.1:${port}`;

const server = spawn(`${repo}/.githooks/dw-workbench`, ['--root', repo, '--port', port], { stdio: 'ignore' });
const stop = () => { try { server.kill(); } catch {} };
process.on('exit', stop);
await new Promise(r => setTimeout(r, 2500));

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 1280, height: 720 },
  recordVideo: { dir: outDir, size: { width: 1280, height: 720 } },
});
const page = await ctx.newPage();

await page.goto(`${base}/#/programs`);
await page.waitForTimeout(3500);
await page.goto(`${base}/#/programs/${runId}`);
await page.waitForTimeout(3000);

const deadline = Date.now() + 30 * 60 * 1000;
while (!existsSync(doneFile) && Date.now() < deadline) {
  for (let i = 0; i < 6; i++) { await page.mouse.wheel(0, 140); await page.waitForTimeout(400); }
  await page.waitForTimeout(4000);
  await page.reload();
  await page.waitForTimeout(3000);
}
// One last look at the finished run.
await page.reload();
await page.waitForTimeout(5000);
for (let i = 0; i < 8; i++) { await page.mouse.wheel(0, 140); await page.waitForTimeout(350); }

const videoPath = await page.video().path();
await ctx.close();
renameSync(videoPath, join(outDir, 'mission-control.webm'));
console.log('video:', join(outDir, 'mission-control.webm'));
await browser.close();
stop();
