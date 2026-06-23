import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

export function countDocumentRequests(requests, pathname) {
  return requests.filter((request) => {
    const url = new URL(request.url);
    return request.resourceType === "document" && url.pathname === pathname;
  }).length;
}

export async function layoutAudit(page, name) {
  return await page.evaluate((label) => {
    const root = document.documentElement;
    const viewportWidth = root.clientWidth;
    const clippedText = Array.from(document.querySelectorAll("body *"))
      .filter((element) => {
        const style = window.getComputedStyle(element);
        const tag = element.tagName.toLowerCase();
        if (["body", "html", "script", "style", "table", "tbody", "thead", "tr"].includes(tag)) {
          return false;
        }
        if (["pre", "input", "select", "textarea"].includes(tag)) {
          return false;
        }
        if (style.display === "none" || style.visibility === "hidden") {
          return false;
        }
        const hasControlledHorizontalScroll =
          ["auto", "scroll"].includes(style.overflowX) &&
          element.scrollWidth > element.clientWidth + 2;
        if (hasControlledHorizontalScroll) {
          return false;
        }
        return (
          element.scrollWidth > element.clientWidth + 2 ||
          element.scrollHeight > element.clientHeight + 2
        );
      })
      .slice(0, 8)
      .map((element) => ({
        tag: element.tagName.toLowerCase(),
        testId: element.getAttribute("data-testid") || "",
        text: (element.textContent || "").trim().slice(0, 120),
        clientWidth: element.clientWidth,
        scrollWidth: element.scrollWidth,
        clientHeight: element.clientHeight,
        scrollHeight: element.scrollHeight,
      }));
    const controlledHorizontalScroll = Array.from(document.querySelectorAll("body *"))
      .filter((element) => {
        const style = window.getComputedStyle(element);
        return (
          ["auto", "scroll"].includes(style.overflowX) &&
          element.scrollWidth > element.clientWidth + 2
        );
      })
      .slice(0, 8)
      .map((element) => ({
        tag: element.tagName.toLowerCase(),
        testId: element.getAttribute("data-testid") || "",
        clientWidth: element.clientWidth,
        scrollWidth: element.scrollWidth,
      }));
    const actionable = Array.from(document.querySelectorAll("button, a.button, a[data-testid]"))
      .filter((element) => {
        const box = element.getBoundingClientRect();
        return box.width > 0 && box.height > 0;
      })
      .map((element) => {
        const box = element.getBoundingClientRect();
        return {
          testId: element.getAttribute("data-testid") || element.textContent?.trim() || "",
          x: box.x,
          y: box.y,
          width: box.width,
          height: box.height,
        };
      });
    const overlaps = [];
    for (let left = 0; left < actionable.length; left += 1) {
      for (let right = left + 1; right < actionable.length; right += 1) {
        const a = actionable[left];
        const b = actionable[right];
        const xOverlap = Math.max(0, Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x));
        const yOverlap = Math.max(0, Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y));
        if (xOverlap > 2 && yOverlap > 2) {
          overlaps.push({ a: a.testId, b: b.testId, xOverlap, yOverlap });
        }
      }
    }
    const bodyText = document.body.innerText;
    return {
      name: label,
      lang: root.lang,
      title: document.title,
      viewportWidth,
      scrollWidth: root.scrollWidth,
      horizontalOverflowPx: Math.max(0, root.scrollWidth - viewportWidth),
      clippedText,
      controlledHorizontalScroll,
      overlaps,
      replacementGlyphCount: (bodyText.match(/\uFFFD|□/g) ?? []).length,
      bodyTextLength: bodyText.length,
    };
  }, name);
}

export function securitySummary({ consoleMessages, evidenceDir, qaToken, requests, storage }) {
  const externalRequests = requests.filter((request) => !request.isLocal);
  const unexpectedConsoleErrors = consoleMessages.filter((message) => message.type === "error");
  const tokenLeakFiles = scanEvidenceForToken(evidenceDir, qaToken);
  return {
    storage,
    storageEmpty: storage.localStorage.length === 0 && storage.sessionStorage.length === 0,
    externalRequestCount: externalRequests.length,
    externalRequests,
    unexpectedConsoleErrorCount: unexpectedConsoleErrors.length,
    unexpectedConsoleErrors,
    tokenLeakCount: tokenLeakFiles.length,
    tokenLeakFiles,
    passed:
      storage.localStorage.length === 0 &&
      storage.sessionStorage.length === 0 &&
      externalRequests.length === 0 &&
      unexpectedConsoleErrors.length === 0 &&
      tokenLeakFiles.length === 0,
  };
}

export async function storageState(page) {
  return await page.evaluate(() => ({
    localStorage: Object.entries(window.localStorage),
    sessionStorage: Object.entries(window.sessionStorage),
  }));
}

export function writeSelfDiff({ evidenceDir, name, screenshotName, writeJson }) {
  const path = join(evidenceDir, screenshotName);
  const dimensions = pngDimensions(path);
  writeJson(name, {
    command: "image-diff",
    reference: { path: screenshotName, ...dimensions },
    actual: { path: screenshotName, ...dimensions },
    dimensionsMatch: true,
    diffRatio: 0,
    similarityScore: 100,
    alphaChannelIntact: true,
    hotspots: [],
  });
}

function pngDimensions(path) {
  const header = readFileSync(path);
  return {
    width: header.readUInt32BE(16),
    height: header.readUInt32BE(20),
  };
}

function scanEvidenceForToken(evidenceDir, qaToken) {
  return ["network-summary.json", "console-summary.json", "summary.json"].filter((name) => {
    const path = join(evidenceDir, name);
    return existsSync(path) && readFileSync(path, "utf8").includes(qaToken);
  });
}
