import { test as base, expect } from "@playwright/test";
import { installMockSite } from "./mock-site.js";

export const test = base.extend({
  mockSite: [
    async ({ context, baseURL }, use) => {
      await installMockSite(context, { baseURL });
      await use();
    },
    { auto: true },
  ],
});

export { expect };
