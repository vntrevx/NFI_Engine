import { existsSync } from "node:fs";
import net from "node:net";
import { join } from "node:path";

export function browserLaunchEnv(repoRoot) {
  const localLibDir =
    process.env.NFI_BROWSER_QA_LIB_DIR ??
    join(repoRoot, ".omo/tools/browser-libs/root/usr/lib/x86_64-linux-gnu");
  const fontConfig =
    process.env.NFI_BROWSER_QA_FONTCONFIG ?? join(repoRoot, ".omo/tools/browser-libs/fonts.conf");
  const env = { ...process.env };
  if (existsSync(localLibDir)) {
    const existing = process.env.LD_LIBRARY_PATH;
    env.LD_LIBRARY_PATH = existing ? `${localLibDir}:${existing}` : localLibDir;
  }
  if (existsSync(fontConfig)) {
    env.FONTCONFIG_FILE = fontConfig;
  }
  return env;
}

export async function freePort() {
  const server = net.createServer();
  await new Promise((resolvePromise, rejectPromise) => {
    server.once("error", rejectPromise);
    server.listen(0, "127.0.0.1", resolvePromise);
  });
  const address = server.address();
  await new Promise((resolvePromise) => server.close(resolvePromise));
  if (!address || typeof address === "string") {
    throw new Error("could not allocate free port");
  }
  return address.port;
}

export function isLocalUrl(rawUrl, baseUrl = null) {
  if (
    (baseUrl && rawUrl.startsWith(baseUrl)) ||
    rawUrl.startsWith("data:") ||
    rawUrl.startsWith("blob:") ||
    rawUrl === "about:blank"
  ) {
    return true;
  }
  try {
    const url = new URL(rawUrl);
    return ["127.0.0.1", "localhost"].includes(url.hostname);
  } catch {
    return false;
  }
}

export async function onceExit(process, timeoutMs) {
  if (process.exitCode !== null) {
    return;
  }
  await Promise.race([
    new Promise((resolvePromise) => process.once("exit", resolvePromise)),
    sleep(timeoutMs).then(() => {
      process.kill("SIGKILL");
    }),
  ]);
}

export async function waitForPortClosed(port) {
  const deadline = Date.now() + 5000;
  while (Date.now() < deadline) {
    if (await portIsClosed(port)) {
      return;
    }
    await sleep(100);
  }
  throw new Error(`port ${port} is still open`);
}

export function resolveChromiumExecutable(repoRoot) {
  const candidates = [
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
    process.env.CHROME_BIN,
    join(process.env.HOME ?? "", ".cache/ms-playwright/chromium-1223/chrome-linux64/chrome"),
    join(process.env.HOME ?? "", ".cache/ms-playwright/chromium-1200/chrome-linux64/chrome"),
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ].filter(Boolean);
  const found = candidates.find((candidate) => existsSync(candidate));
  if (!found) {
    throw new Error(
      "Chromium executable not found. Set PLAYWRIGHT_CHROMIUM_EXECUTABLE or run `npx playwright install chromium`.",
    );
  }
  return found;
}

export function sleep(ms) {
  return new Promise((resolvePromise) => {
    setTimeout(resolvePromise, ms);
  });
}

async function portIsClosed(port) {
  return await new Promise((resolvePromise) => {
    const socket = net.createConnection({ port, host: "127.0.0.1" });
    socket.once("connect", () => {
      socket.destroy();
      resolvePromise(false);
    });
    socket.once("error", () => resolvePromise(true));
  });
}
