import { afterEach, describe, expect, it, vi } from "vitest";

describe("api client", () => {
  afterEach(() => {
    delete process.env.UMI_APP_API_BASE_URL;
    vi.resetModules();
  });

  it("uses the default API base URL when no env override is set", async () => {
    delete process.env.UMI_APP_API_BASE_URL;
    vi.resetModules();

    const { default: client } = await import("../src/api/client");

    expect(client.defaults.baseURL).toBe("/api/v1");
  });

  it("uses the configured API base URL override", async () => {
    process.env.UMI_APP_API_BASE_URL = "https://example.test/api";
    vi.resetModules();

    const { default: client } = await import("../src/api/client");

    expect(client.defaults.baseURL).toBe("https://example.test/api");
  });
});
