import { test as base, expect } from "@playwright/test";
import { installMockSite } from "./mock-site.js";

export const test = base.extend({
  mockSite: [
    async ({ context, baseURL }, use) => {
      const state = await installMockSite(context, { baseURL });
      await use(state);
    },
    { auto: true },
  ],
});

export { expect };
