import { expect, test, type Page } from "@playwright/test";

const demoRoutes = [
  ["/dashboard", "Good morning, Rafiq."],
  ["/risks", "Risk register"],
  ["/approvals", "Approvals"],
  ["/signals", "Signals"],
  ["/sources", "Sources"],
  ["/reports", "Reports"],
  ["/graph", "Supply-chain graph"],
  ["/search", "Evidence search"],
  ["/evals", "Evaluations"],
  ["/audit", "Audit trail"],
] as const;

async function loginAsAnalyst(page: Page) {
  await page.goto("/login");
  await page.getByRole("button", { name: /Rafiq Hasan/ }).click();
  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Good morning, Rafiq.");
}

test("analyst can navigate the full risk-intelligence workspace", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));

  await loginAsAnalyst(page);

  for (const [route, heading] of demoRoutes) {
    await page.goto(route);
    await expect(page.getByRole("heading", { level: 1 })).toContainText(heading);
  }

  await expect(page.getByText("Audit access requires an admin")).toBeVisible();
  expect(pageErrors).toEqual([]);
});

test("risk detail shows evidence, score, and remediation actions", async ({ page }) => {
  await loginAsAnalyst(page);
  await page.goto("/risks");
  await page.locator("tbody tr").first().click();
  await expect(page).toHaveURL(/\/risks\/[0-9a-f-]+/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Cotton origin documentation");
  await expect(page.getByRole("heading", { name: "Score breakdown" })).toBeVisible();
  await expect(page.getByText("Evidence", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Suggested remediation")).toBeVisible();
});

test("admin can verify the hash-chained audit trail", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: /Ayesha Rahman/ }).click();
  await expect(page).toHaveURL(/\/dashboard/);
  await page.goto("/audit");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Audit trail");
  await expect(page.getByText("Chain valid")).toBeVisible();
  await expect(page.getByText("SHA-256 hash chain")).toBeVisible();
});

test("evidence search returns cited source chunks", async ({ page }) => {
  await loginAsAnalyst(page);
  await page.goto("/search");
  await page.getByPlaceholder(/Search regulations/).fill("forced labour");
  await page.getByRole("button", { name: /Search evidence/ }).click();
  await expect(page.locator("article").first()).toBeVisible();
  await expect(page.getByText(/results for/)).toBeVisible();
});
