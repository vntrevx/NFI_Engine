import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export async function exerciseLifecyclePanel(page, baseUrl, runtimeDir) {
  await page.goto(`${baseUrl}/settings`, { waitUntil: "networkidle" });
  await page.locator('[data-testid="settings-root"]').waitFor();
  await page.locator('[data-testid="data-lifecycle-inspect-button"]').click();
  await page.waitForFunction(() =>
    document
      .querySelector('[data-testid="data-lifecycle-footprint-state"]')
      ?.textContent?.includes("sqlite"),
  );
  const footprintText = await page
    .locator('[data-testid="data-lifecycle-footprint-state"]')
    .innerText();
  await page.locator('[data-testid="data-lifecycle-export-button"]').click();
  await page.waitForFunction(() =>
    document
      .querySelector('[data-testid="data-lifecycle-export-state"]')
      ?.textContent?.includes("EXPORT_READY data-export-"),
  );
  const exportText = await page.locator('[data-testid="data-lifecycle-export-state"]').innerText();
  await page.locator('[data-testid="data-lifecycle-retention-days"]').fill("0");
  await page.locator('[data-testid="data-lifecycle-dry-run-button"]').click();
  await page.waitForFunction(() =>
    document.querySelector('[data-testid="data-lifecycle-preview-token"]')?.value,
  );
  const previewToken = await page
    .locator('[data-testid="data-lifecycle-preview-token"]')
    .inputValue();
  const dryRunText = await page.locator('[data-testid="data-lifecycle-prune-state"]').innerText();
  const oldLogBeforeApply = existsSync(join(runtimeDir, "logs", "old.log"));
  await page.locator('[data-testid="data-lifecycle-apply-button"]').click();
  await page.waitForFunction(() =>
    document
      .querySelector('[data-testid="data-lifecycle-prune-state"]')
      ?.textContent?.includes("deleted=5"),
  );
  const applyText = await page.locator('[data-testid="data-lifecycle-prune-state"]').innerText();
  const oldLogAfterApply = existsSync(join(runtimeDir, "logs", "old.log"));
  return {
    footprintText,
    exportText,
    dryRunText,
    applyText,
    previewTokenLength: previewToken.length,
    oldLogBeforeApply,
    oldLogAfterApply,
    passed:
      footprintText.includes("sqlite") &&
      exportText.includes("EXPORT_READY data-export-") &&
      dryRunText.includes("ACCEPTED") &&
      previewToken.length > 0 &&
      oldLogBeforeApply &&
      applyText.includes("ACCEPTED") &&
      applyText.includes("deleted=5") &&
      !oldLogAfterApply,
  };
}

export function qaConfig(port, runtimeDir) {
  return `engine:
  environment: local
  live_trading: false
exchange:
  name: simulator
  trading_mode: spot
  testnet: true
database:
  url: sqlite+aiosqlite:///${join(runtimeDir, "engine.sqlite3")}
api:
  host: 127.0.0.1
  port: ${port}
  csrf_enabled: true
ui:
  enabled: true
  read_only: false
notifications:
  jsonl_path: ${join(runtimeDir, "evidence", "notifications.jsonl")}
`;
}

export function seedRuntime(runtimeDir) {
  mkdirSync(join(runtimeDir, "logs"), { recursive: true });
  mkdirSync(join(runtimeDir, "backups"), { recursive: true });
  mkdirSync(join(runtimeDir, "support-bundles"), { recursive: true });
  mkdirSync(join(runtimeDir, "evidence"), { recursive: true });
  writeFileSync(join(runtimeDir, "logs", "engine.log"), "fresh-log");
  writeFileSync(join(runtimeDir, "logs", "old.log"), "old-log");
  writeFileSync(join(runtimeDir, "backups", "backup.zip"), "backup-data");
  writeFileSync(join(runtimeDir, "support-bundles", "support.zip"), "support-data");
  writeFileSync(join(runtimeDir, "evidence", "operator.json"), "evidence-data");
}
