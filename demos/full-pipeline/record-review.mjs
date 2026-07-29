// Record the Workbench browser review of the setup proposal + program bundle.
// Usage: node record-review.mjs <repo-dir> <out-dir> [port]
// Spawns dw-workbench against the demo repo, records one 1280x720 video
// covering the adoption review and the Program Studio bundle review.
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { renameSync } from 'node:fs';
import { join } from 'node:path';

const [repo, outDir, portArg] = process.argv.slice(2);
if (!repo || !outDir) { console.error('usage: node record-review.mjs <repo> <out-dir> [port]'); process.exit(1); }
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

const glide = async (px) => {
  for (let i = 0; i < px / 120; i++) { await page.mouse.wheel(0, 120); await page.waitForTimeout(350); }
};

// The delivery overview.
await page.goto(`${base}/`);
await page.waitForTimeout(3500);

// Roadmap changes: the adoption review of the inert proposal.
await page.goto(`${base}/?proposal_file=.tmp/proposal.json#/edit/adoption_review`);
await page.waitForTimeout(4000);
await glide(1400);
await page.waitForTimeout(1500);

// Program Studio: the generated program as one linked bundle.
await page.goto(`${base}/?proposal_file=.tmp/proposal.json#/program-studio/bundle`);
await page.waitForTimeout(4000);
await glide(1800);
await page.waitForTimeout(2000);

const videoPath = await page.video().path();
await ctx.close();
renameSync(videoPath, join(outDir, 'review.webm'));
console.log('video:', join(outDir, 'review.webm'));
await browser.close();
stop();
