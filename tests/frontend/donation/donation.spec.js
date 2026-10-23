import { expect, test } from "../support/test.js";

const PAGE_PATH = "/donation";

const PAYMENTS = [
  {
    tab: "gcash",
    label: "GCash",
    title: "GCash",
    details: ["Joshua P. Algadipe", "DWQM4TK3JDO0AS2Q3"],
    image: "gcash_qr.jpg",
    alt: "GCash QR Code",
  },
  {
    tab: "paymaya",
    label: "PayMaya",
    title: "PayMaya",
    details: ["Joshua P. Algadipe", "639319127640"],
    image: "paymaya_qr.jpg",
    alt: "PayMaya QR Code",
  },
  {
    tab: "maribank",
    label: "MariBank",
    title: "MariBank",
    details: ["Joshua P. Algadipe", "19681554191"],
    image: "maribank_qr.jpg",
    alt: "MariBank QR Code",
  },
  {
    tab: "tonik",
    label: "Tonik Bank",
    title: "Tonik Bank",
    details: ["Joshua P. Algadipe", "6083215190005"],
    image: "tonikbank_qr.jpg",
    alt: "Tonik Bank QR Code",
  },
  {
    tab: "ownbank",
    label: "OwnBank",
    title: "OwnBank",
    details: ["Joshua P. Algadipe", "2024091400000976"],
    image: "ownbank_qr.jpg",
    alt: "OwnBank QR Code",
  },
];

async function openDonationPage(page) {
  await page.goto(PAGE_PATH, { waitUntil: "domcontentloaded" });
  await expect(page.locator("#donation")).toBeVisible();
}

function tab(page, payment) {
  return page.locator(`.payment-tab[data-tab="${payment.tab}"]`);
}

function panel(page, payment) {
  return page.locator(`#panel-${payment.tab}`);
}

async function expectActivePayment(page, payment) {
  await expect(tab(page, payment)).toHaveClass(/active/);
  await expect(page.locator(".payment-tab.active")).toHaveCount(1);
  await expect(page.locator(".payment-panel.active")).toHaveCount(1);
  await expect(panel(page, payment)).toHaveClass(/active/);
  await expect(panel(page, payment)).toBeVisible();
  await expect(panel(page, payment).locator(".panel-header h3")).toHaveText(
    payment.title
  );
  await expect(panel(page, payment).locator(".panel-badge")).toHaveText(
    "QR Code"
  );
  await expect(panel(page, payment).locator(".qr-image")).toHaveAttribute(
    "alt",
    payment.alt
  );
  await expect(panel(page, payment).locator(".qr-image")).toHaveAttribute(
    "src",
    new RegExp(`${payment.image.replace(".", "\\.")}$`)
  );

  const info = panel(page, payment).locator(".info-item span");
  await expect(info).toHaveCount(payment.details.length);
  for (let index = 0; index < payment.details.length; index += 1) {
    await expect(info.nth(index)).toHaveText(payment.details[index]);
  }

  for (const other of PAYMENTS) {
    if (other.tab !== payment.tab) {
      await expect(tab(page, other)).not.toHaveClass(/active/);
      await expect(panel(page, other)).not.toHaveClass(/active/);
      await expect(panel(page, other)).toBeHidden();
    }
  }
}

async function openQrModal(page, payment) {
  await tab(page, payment).click();
  const qr = panel(page, payment).locator(".qr-container");
  await qr.scrollIntoViewIfNeeded();
  await qr.click();
  await expect(page.locator("#qrModal")).toBeVisible();
}

async function closeQrModalWithButton(page) {
  await page.locator(".qr-modal-close").click();
  await expect(page.locator("#qrModal")).toBeHidden();
  await expect
    .poll(() => page.evaluate(() => document.body.style.overflow))
    .toBe("");
}

test.describe("Donation page", () => {
  test("renders the donation copy, five payment tabs and the default GCash panel", async ({
    page,
  }) => {
    await openDonationPage(page);

    await expect(page.locator(".donation-header h2")).toHaveText("Donation");
    await expect(page.locator(".donation-header p")).toContainText(
      "Could you kindly consider sending me a heartfelt gift?"
    );
    await expect(page.locator(".donation-header p")).toContainText(
      "scanning the GCash QR code"
    );

    const tabs = page.locator(".payment-tab");
    await expect(tabs).toHaveCount(PAYMENTS.length);
    for (let index = 0; index < PAYMENTS.length; index += 1) {
      await expect(tabs.nth(index)).toHaveAttribute(
        "data-tab",
        PAYMENTS[index].tab
      );
      await expect(
        tabs.nth(index).locator(".payment-tab-label")
      ).toHaveText(PAYMENTS[index].label);
      await expect(tabs.nth(index).locator(".payment-tab-icon")).toBeVisible();
    }

    await expect(page.locator(".payment-panel")).toHaveCount(PAYMENTS.length);
    await expect(page.locator(".panel-badge")).toHaveCount(PAYMENTS.length);
    await expect(page.locator(".qr-image")).toHaveCount(PAYMENTS.length);
    await expectActivePayment(page, PAYMENTS[0]);
  });

  test("switches between every payment tab and its details", async ({ page }) => {
    await openDonationPage(page);

    for (const payment of PAYMENTS) {
      await tab(page, payment).click();
      await expectActivePayment(page, payment);
    }
  });

  test("switches payment tabs with the keyboard", async ({ page }) => {
    await openDonationPage(page);

    const payMaya = tab(page, PAYMENTS[1]);
    await payMaya.focus();
    await expect(payMaya).toBeFocused();
    await page.keyboard.press("Enter");
    await expectActivePayment(page, PAYMENTS[1]);

    const ownBank = tab(page, PAYMENTS[4]);
    await ownBank.focus();
    await expect(ownBank).toBeFocused();
    await page.keyboard.press("Space");
    await expectActivePayment(page, PAYMENTS[4]);
  });

  test("opens every QR image in the modal with the matching source", async ({
    page,
  }) => {
    await openDonationPage(page);

    const modal = page.locator("#qrModal");
    const modalImage = page.locator("#qrModalImage");

    for (const payment of PAYMENTS) {
      await openQrModal(page, payment);

      const source = await panel(page, payment)
        .locator(".qr-image")
        .getAttribute("src");
      const resolvedSource = new URL(source, page.url()).href;
      await expect(modalImage).toHaveAttribute("src", resolvedSource);
      await expect(modalImage).toHaveAttribute("alt", "QR Code Preview");
      await expect
        .poll(() =>
          modalImage.evaluate((image) => image.complete && image.naturalWidth > 0)
        )
        .toBe(true);
      await expect
        .poll(() => page.evaluate(() => document.body.style.overflow))
        .toBe("hidden");

      await closeQrModalWithButton(page);
    }
  });

  test("closes the QR modal from the close button or the backdrop only", async ({
    page,
  }) => {
    await openDonationPage(page);
    await openQrModal(page, PAYMENTS[0]);

    await page.locator(".qr-modal-content img").click();
    await expect(page.locator("#qrModal")).toBeVisible();
    await expect
      .poll(() => page.evaluate(() => document.body.style.overflow))
      .toBe("hidden");

    await page.locator("#qrModal").click({ position: { x: 5, y: 5 } });
    await expect(page.locator("#qrModal")).toBeHidden();
    await expect
      .poll(() => page.evaluate(() => document.body.style.overflow))
      .toBe("");

    await openQrModal(page, PAYMENTS[2]);
    await closeQrModalWithButton(page);
  });
});

test.describe("Donation page mobile", () => {
  test.use({ viewport: { width: 480, height: 900 } });

  test("wraps all payment tabs, keeps them reachable and opens the QR modal", async ({
    page,
  }) => {
    await openDonationPage(page);

    await expect(page.locator(".payment-tab")).toHaveCount(PAYMENTS.length);

    const layoutFits = await page.evaluate(() => {
      const tabs = Array.from(document.querySelectorAll(".payment-tab"));
      return (
        document.documentElement.scrollWidth <= window.innerWidth + 1 &&
        tabs.every((item) => {
          const rect = item.getBoundingClientRect();
          return rect.left >= 0 && rect.right <= window.innerWidth;
        })
      );
    });
    expect(layoutFits).toBe(true);

    for (const payment of PAYMENTS) {
      await tab(page, payment).click();
      await expectActivePayment(page, payment);
    }

    await openQrModal(page, PAYMENTS[3]);

    const modalFits = await page.locator(".qr-modal-content").evaluate((element) => {
      const rect = element.getBoundingClientRect();
      return rect.left >= 0 && rect.right <= window.innerWidth;
    });
    expect(modalFits).toBe(true);
    await expect(page.locator(".qr-modal-close")).toBeVisible();

    await closeQrModalWithButton(page);
    await expect(page.locator("#donation")).toBeVisible();
  });
});
