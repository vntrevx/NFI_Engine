export async function captureMobileViews(page, baseUrl, { layout, screenshot }) {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.locator('[data-testid="home-root"]').waitFor();
  await waitForRuntimeState(page, "stopped");
  const homeMobileLayout = await layout(page, "home-mobile");
  await screenshot(page, "home-mobile.png");

  await page.goto(`${baseUrl}/settings`, { waitUntil: "networkidle" });
  await page.locator('[data-testid="settings-root"]').waitFor();
  await waitForRuntimeState(page, "stopped");
  const settingsMobileLayout = await layout(page, "settings-mobile");
  await screenshot(page, "settings-mobile.png");
  return { layouts: [homeMobileLayout, settingsMobileLayout] };
}

export async function exerciseHomeControls(page, baseUrl, { layout, record, screenshot }) {
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.locator('[data-testid="home-root"]').waitFor();
  await waitForRuntimeState(page, "stopped");
  const initialState = await runtimeControlText(page);
  const initialHealth = await runtimeHealthText(page);
  const initialBotState = await botStateText(page);
  await page.locator('[data-testid="start-button"]').click();
  await waitForRuntimeState(page, "running");
  const afterStartBotState = await botStateText(page);
  await page.locator('[data-testid="pause-button"]').click();
  await waitForRuntimeState(page, "paused");
  const afterPauseBotState = await botStateText(page);
  const afterPauseRuntime = await runtimeControlPayload(page);
  const finalHealth = await runtimeHealthText(page);
  const pageLayout = await layout(page, "home-desktop");
  await screenshot(page, "home-desktop.png");
  record("home-controls", {
    initialState,
    initialHealth,
    initialBotState,
    afterStartBotState,
    afterPauseBotState,
    finalHealth,
  });
  return {
    initialState,
    initialHealth,
    initialBotState,
    afterStartBotState,
    afterPauseBotState,
    afterPauseRuntime,
    finalHealth,
    layout: pageLayout,
    passed:
      initialState === "stopped" &&
      afterStartBotState === "running" &&
      afterPauseBotState === "paused" &&
      afterPauseRuntime.state === "paused" &&
      afterPauseRuntime.new_entries_allowed === false,
  };
}

export async function exerciseSettingsControls(page, baseUrl, { layout, record, screenshot }) {
  await page.goto(`${baseUrl}/settings`, { waitUntil: "networkidle" });
  await page.locator('[data-testid="settings-root"]').waitFor();
  await waitForRuntimeState(page, "paused");
  const initialSettingsState = await runtimeControlText(page);
  await screenshot(page, "settings-paused-desktop.png");
  await page.locator('[data-testid="resume-button"]').click();
  await waitForRuntimeState(page, "running");
  const afterResume = await runtimeControlPayload(page);
  await page.locator('[data-testid="stop-button"]').click();
  await waitForRuntimeState(page, "stopped");
  const afterStop = await runtimeControlPayload(page);
  const pageLayout = await layout(page, "settings-flow-desktop");
  await screenshot(page, "settings-stopped-desktop.png");
  record("settings-controls", { initialSettingsState, afterResume, afterStop });
  return {
    initialSettingsState,
    afterResume,
    afterStop,
    layout: pageLayout,
    passed:
      initialSettingsState === "paused" &&
      afterResume.state === "running" &&
      afterResume.new_entries_allowed === true &&
      afterStop.state === "stopped" &&
      afterStop.new_entries_allowed === false,
  };
}

export async function runtimeControlPayload(page) {
  return await page.evaluate(async () => {
    const response = await fetch("/api/v1/runtime/control", { credentials: "same-origin" });
    return await response.json();
  });
}

export async function storageState(page) {
  return await page.evaluate(() => ({
    localStorage: Object.entries(window.localStorage),
    sessionStorage: Object.entries(window.sessionStorage),
  }));
}

async function waitForRuntimeState(page, state) {
  await page.waitForFunction((expected) => {
    const text = document.querySelector('[data-testid="runtime-control-state"]')?.textContent ?? "";
    return text.trim() === expected;
  }, state);
}

async function runtimeControlText(page) {
  return (await page.locator('[data-testid="runtime-control-state"]').innerText()).trim();
}

async function runtimeHealthText(page) {
  return (await page.locator('[data-testid="runtime-health-state"]').innerText()).trim();
}

async function botStateText(page) {
  return (await page.locator('[data-testid="bot-state"] strong').innerText()).trim();
}
