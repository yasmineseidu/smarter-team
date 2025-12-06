import { test, expect } from "@playwright/test";

test.describe("Health Checks", () => {
  test("backend health endpoint returns healthy", async ({ request }) => {
    const response = await request.get("http://localhost:8000/health");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe("healthy");
    expect(body.version).toBeDefined();
  });

  test("backend root endpoint returns API info", async ({ request }) => {
    const response = await request.get("http://localhost:8000/");
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.name).toBe("Smarter Team API");
    expect(body.version).toBeDefined();
    expect(body.docs).toBe("/docs");
  });

  test("frontend home page loads", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Smarter Team" })).toBeVisible();
    await expect(page.getByText("Multi-Agent AI Agency Automation")).toBeVisible();
  });

  test("frontend has navigation links", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("link", { name: /dashboard/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /documentation/i })).toBeVisible();
  });
});
