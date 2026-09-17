import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const outDir = path.dirname(fileURLToPath(import.meta.url));
await mkdir(outDir, { recursive: true });

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1280, height: 720 },
  recordVideo: { dir: outDir, size: { width: 1280, height: 720 } },
});
const page = await context.newPage();
await page.goto("http://127.0.0.1:8080/preview", { waitUntil: "networkidle" });
await page.waitForTimeout(17500);
const video = page.video();
await context.close();
if (video) {
  const dest = path.join(outDir, "jev-memory-selector.webm");
  await video.saveAs(dest);
  await video.delete();
  console.log(dest);
}
await browser.close();
