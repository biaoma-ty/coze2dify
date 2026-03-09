import path from "node:path";
import { expect, test } from "@playwright/test";

type BrowserError = {
  kind: "console" | "pageerror";
  text: string;
  locationUrl?: string;
};

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function normalizeBaseUrl(value: string): string {
  return value.replace(/\/$/, "");
}

function formatBrowserError(error: BrowserError): string {
  if (!error.locationUrl) {
    return `[${error.kind}] ${error.text}`;
  }

  return `[${error.kind}] ${error.text} (${error.locationUrl})`;
}

function isIgnorableWorkflowError(error: BrowserError): boolean {
  if (error.kind !== "console") {
    return false;
  }

  // Dify 1.13 self-hosted emits these during editor bootstrap even when the
  // migrated workflow opens correctly, so keep them out of the smoke signal.
  if (error.text.startsWith("Failed to fetch plan info: TypeError: Failed to fetch")) {
    return true;
  }

  return error.text.includes("400 (BAD REQUEST)")
    && error.locationUrl?.includes("/console/api/datasets/retrieval-setting") === true;
}

function trackBrowserErrors(page: import("@playwright/test").Page, errors: BrowserError[]): void {
  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push({
        kind: "console",
        text: message.text(),
        locationUrl: message.location().url,
      });
    }
  });
  page.on("pageerror", (error) => {
    errors.push({
      kind: "pageerror",
      text: error.message,
    });
  });
}

test("migrates a fixture into Dify and opens the workflow editor without browser errors", async ({ browser }) => {
  const appBaseUrl = normalizeBaseUrl(requiredEnv("E2E_APP_URL"));
  const difyBaseUrl = normalizeBaseUrl(requiredEnv("E2E_DIFY_URL"));
  const difyDatabaseUrl = requiredEnv("E2E_DIFY_DB_URL");
  const difyEmail = requiredEnv("E2E_DIFY_EMAIL");
  const difyPassword = requiredEnv("E2E_DIFY_PASSWORD");
  const fixturePath = process.env.E2E_FIXTURE_PATH || path.resolve(__dirname, "../../e2e/fixtures/minimal-workflow.json");

  const browserErrors: BrowserError[] = [];
  const context = await browser.newContext();
  context.on("page", (page) => trackBrowserErrors(page, browserErrors));

  const page = await context.newPage();
  trackBrowserErrors(page, browserErrors);

  await page.goto(`${appBaseUrl}/`, { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "Import Coze Workflow" })).toBeVisible();

  await page.locator("#file-input").setInputFiles(fixturePath);
  await page.waitForURL(/\/diff\/\d+$/, { timeout: 60_000 });
  await expect(page.getByRole("heading", { name: "Conversion Preview" })).toBeVisible({ timeout: 60_000 });

  const conversionMatch = page.url().match(/\/diff\/(\d+)$/);
  expect(conversionMatch).not.toBeNull();
  const conversionId = conversionMatch![1];

  await page.getByRole("button", { name: "Continue to Export →" }).click();
  await page.waitForURL(new RegExp(`/result/${conversionId}$`), { timeout: 60_000 });
  await expect(page.getByRole("heading", { name: "Export Result" })).toBeVisible({ timeout: 60_000 });

  const writeResponse = await page.request.post(`${appBaseUrl}/api/v1/convert/${conversionId}/write-to-dify`, {
    data: { db_url: difyDatabaseUrl },
    timeout: 60_000,
  });
  const writePayload = await writeResponse.text();
  expect(writeResponse.ok(), writePayload).toBeTruthy();

  const writeResult = JSON.parse(writePayload) as { app_id?: string; mode?: string; status?: string };
  expect(writeResult.status).toBe("written");
  expect(writeResult.mode).toBe("create");
  expect(writeResult.app_id).toBeTruthy();
  const appId = writeResult.app_id!;

  await page.goto(`${difyBaseUrl}/signin`, { waitUntil: "domcontentloaded" });
  await expect(page.locator("input[type='email']")).toBeVisible({ timeout: 60_000 });
  await page.locator("input[type='email']").fill(difyEmail);
  await page.locator("input[type='password']").fill(difyPassword);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL((url) => !url.pathname.startsWith("/signin"), { timeout: 60_000 });
  browserErrors.length = 0;

  const draftResponsePromise = page.waitForResponse(
    (response) =>
      response.request().method() === "GET"
      && response.status() === 200
      && response.url().includes(`/apps/${appId}/workflows/draft`),
    { timeout: 60_000 },
  );

  await page.goto(`${difyBaseUrl}/app/${appId}/workflow`, { waitUntil: "domcontentloaded" });
  await page.waitForURL(new RegExp(`/app/${appId}/workflow(?:\\?.*)?$`), { timeout: 60_000 });
  await expect(page.getByRole("button", { name: "Publish" })).toBeVisible({ timeout: 60_000 });

  const draftResponse = await draftResponsePromise;
  const draft = await draftResponse.json() as { graph?: { nodes?: unknown[] } };
  expect(Array.isArray(draft.graph?.nodes)).toBeTruthy();
  expect((draft.graph?.nodes || []).length).toBeGreaterThan(0);

  await page.waitForTimeout(2_000);

  const unexpectedBrowserErrors = browserErrors
    .filter((error) => !isIgnorableWorkflowError(error))
    .map((error) => formatBrowserError(error));

  expect(
    unexpectedBrowserErrors,
    browserErrors.map((error) => formatBrowserError(error)).join("\n"),
  ).toEqual([]);
  await context.close();
});
