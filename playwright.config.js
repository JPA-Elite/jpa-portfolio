import { defineConfig, devices } from "@playwright/test";

const port = Number(process.env.PLAYWRIGHT_PORT || "4173");
const baseURL =
  process.env.PLAYWRIGHT_BASE_URL || `http://professional.jpastack.local:${port}`;

const hostResolverRules = [
  "MAP professional.jpastack.local 127.0.0.1",
  "MAP jpastack.local 127.0.0.1",
  "MAP admin.jpastack.local 127.0.0.1",
].join(", ");

export default defineConfig({
  testDir: "./tests/frontend",
  testMatch: "**/*.spec.js",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30000,
  expect: {
    timeout: 7000,
  },
  reporter: [["list"]],
  globalTeardown: "./tests/frontend/global-teardown.js",
  use: {
    baseURL,
    headless: true,
    trace: "off",
    screenshot: "off",
    video: "off",
  },
  webServer: {
    command: "python tests/frontend/mock_server.py",
    port,
    reuseExistingServer: false,
    stdout: "ignore",
    stderr: "ignore",
    env: { ...process.env, PLAYWRIGHT_MOCK_PORT: String(port) },
    timeout: 120000,
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        launchOptions: {
          args: [`--host-resolver-rules=${hostResolverRules}`],
        },
      },
    },
  ],
});
