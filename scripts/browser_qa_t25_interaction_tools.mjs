export async function clickForState(page, buttonSelector, stateSelector, path) {
  const before = await readText(page, stateSelector);
  const fetch = await waitForFetch(page, path, async () => {
    await page.locator(buttonSelector).click();
  });
  await page.waitForFunction(
    ({ selector, previous }) => {
      const current = document.querySelector(selector)?.textContent?.trim() || "";
      return current !== "" && current !== previous;
    },
    { selector: stateSelector, previous: before },
  );
  const after = await readText(page, stateSelector);
  return {
    before: before.replace(/\s+/g, " ").trim().slice(0, 180),
    after: after.replace(/\s+/g, " ").trim().slice(0, 180),
    changed: after !== "" && after !== before,
    fetch,
  };
}

export async function postRuntimeCommand(page, baseUrl, csrfToken, command) {
  const response = await page.request.post(`${baseUrl}/api/v1/runtime/control`, {
    headers: {
      "content-type": "application/json",
      "x-nfi-csrf-token": csrfToken,
    },
    data: { command },
  });
  return {
    command,
    posted: response.status() > 0,
    status: response.status(),
    ok: response.ok(),
  };
}

export async function readText(page, selector) {
  return (await page.locator(selector).innerText()).trim();
}

export async function responseSummary(response, path) {
  return {
    path,
    method: response.request().method(),
    status: response.status(),
    ok: response.ok(),
  };
}

export function trimEvidenceText(text, redact) {
  return redact(text).replace(/\s+/g, " ").trim().slice(0, 180);
}

export async function waitForFetch(page, path, action) {
  const responsePromise = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return url.pathname === path && response.request().resourceType() === "fetch";
  });
  await action();
  const response = await responsePromise;
  return responseSummary(response, path);
}
