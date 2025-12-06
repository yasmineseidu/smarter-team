import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import Home from "@/app/page";

describe("Home Page", () => {
  it("renders the main heading", () => {
    render(<Home />);
    expect(screen.getByText("Smarter Team")).toBeDefined();
  });

  it("renders the description", () => {
    render(<Home />);
    expect(screen.getByText("Multi-Agent AI Agency Automation")).toBeDefined();
  });

  it("renders the dashboard link", () => {
    render(<Home />);
    const dashboardLink = screen.getByRole("link", { name: /dashboard/i });
    expect(dashboardLink).toBeDefined();
    expect(dashboardLink.getAttribute("href")).toBe("/dashboard");
  });

  it("renders the documentation link", () => {
    render(<Home />);
    const docsLink = screen.getByRole("link", { name: /documentation/i });
    expect(docsLink).toBeDefined();
    expect(docsLink.getAttribute("href")).toBe("/docs");
  });
});
