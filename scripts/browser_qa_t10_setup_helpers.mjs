import { join } from "node:path";

export async function expectStatus(response, expected, label) {
  if (!response || response.status() !== expected) {
    throw new Error(`${label} expected HTTP ${expected}, got ${response?.status() ?? "none"}`);
  }
}

export async function pageLayoutAudit(page, name) {
  const audit = await page.evaluate(() => ({
    lang: document.documentElement.lang,
    viewportWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
    title: document.title,
  }));
  return {
    name,
    ...audit,
    horizontalOverflowPx: Math.max(0, audit.scrollWidth - audit.viewportWidth),
  };
}

export async function screenshot(page, name, { evidenceDir, record, screenshots }) {
  const path = join(evidenceDir, name);
  await page.screenshot({ path, fullPage: true });
  screenshots.push(name);
  record("screenshot", { name });
}
