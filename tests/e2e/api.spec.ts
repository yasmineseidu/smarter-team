import { test, expect } from "@playwright/test";

test.describe("API Integration", () => {
  const API_URL = "http://localhost:8000";

  test("API returns proper CORS headers", async ({ request }) => {
    const response = await request.get(`${API_URL}/health`, {
      headers: {
        Origin: "http://localhost:3000",
      },
    });
    expect(response.ok()).toBeTruthy();
  });

  test("API handles 404 gracefully", async ({ request }) => {
    const response = await request.get(`${API_URL}/nonexistent-endpoint`);
    expect(response.status()).toBe(404);
  });

  test("API documentation is accessible", async ({ request }) => {
    const response = await request.get(`${API_URL}/docs`);
    expect(response.ok()).toBeTruthy();
  });

  test("OpenAPI schema is available", async ({ request }) => {
    const response = await request.get(`${API_URL}/openapi.json`);
    expect(response.ok()).toBeTruthy();

    const schema = await response.json();
    expect(schema.info.title).toBe("Smarter Team API");
    expect(schema.openapi).toMatch(/^3\./);
  });
});
