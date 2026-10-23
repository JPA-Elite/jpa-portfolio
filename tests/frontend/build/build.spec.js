import { expect, test } from "../support/test.js";

const PAGE_PATH = "/build";
const DATE_FIELD = '.dtp-field[data-type="date"]';
const TIME_FIELD = '.dtp-field[data-type="time"]';
const SUCCESS_MESSAGE =
  "Your booking request has been sent successfully! We will contact you shortly.";
const NETWORK_MESSAGE =
  "Network error. Please check your connection and try again.";
const GENERIC_MESSAGE = "An error occurred. Please try again.";

const SERVICES = [
  "Website Development",
  "Web Applications",
  "Mobile Apps",
  "API & Backend",
  "UI/UX Design",
  "E-commerce",
  "Website Redesign",
  "Consultation",
  "Others",
];

const FORM_VALUES = {
  name: "Mock Client",
  email: "client@example.com",
  message: "I need a deterministic build.",
  service: "Web Applications",
  time: "10:00",
  timeLabel: "10:00 AM",
};

async function openBuildPage(page) {
  await page.goto(PAGE_PATH, { waitUntil: "domcontentloaded" });
  await expect(page.locator("#booking")).toBeVisible();
  await expect(page.locator("#bookingForm")).toBeVisible();
}

async function futureDateString(page) {
  return page.evaluate(() => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const tomorrow = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1);
    return `${tomorrow.getFullYear()}-${String(tomorrow.getMonth() + 1).padStart(2, "0")}-${String(tomorrow.getDate()).padStart(2, "0")}`;
  });
}

async function selectFutureDate(page) {
  const input = page.locator(`${DATE_FIELD} .dtp-input`);
  const dropdown = page.locator(`${DATE_FIELD} .dtp-dropdown`);
  const hidden = page.locator(`${DATE_FIELD} .dtp-hidden`);

  await input.click();
  await expect(dropdown).toHaveClass(/open/);

  const targetDate = await futureDateString(page);
  const target = page.locator(`${DATE_FIELD} .dtp-day[data-date="${targetDate}"]`);

  if ((await target.count()) === 0) {
    await page.locator(`${DATE_FIELD} .dtp-nav-btn`).nth(1).click();
    await expect(dropdown).toHaveClass(/open/);
    await page.locator(`${DATE_FIELD} .dtp-day[data-date]`).first().click();
  } else {
    await expect(target).toBeEnabled();
    await target.click();
  }

  const selectedDate = await hidden.inputValue();
  expect(selectedDate).not.toBe("");
  await expect(dropdown).not.toHaveClass(/open/);
  await expect(input).not.toHaveValue("");
  return selectedDate;
}

async function selectTime(page, value = FORM_VALUES.time) {
  const input = page.locator(`${TIME_FIELD} .dtp-input`);
  const dropdown = page.locator(`${TIME_FIELD} .dtp-dropdown`);
  const hidden = page.locator(`${TIME_FIELD} .dtp-hidden`);
  const slot = page.locator(`${TIME_FIELD} .dtp-time-slot[data-value="${value}"]`);

  await input.click();
  await expect(dropdown).toHaveClass(/open/);
  await expect(slot).not.toHaveClass(/past/);
  await slot.click();

  await expect(dropdown).not.toHaveClass(/open/);
  await expect(hidden).toHaveValue(value);
  await expect(input).toHaveValue(FORM_VALUES.timeLabel);
}

async function fillBookingForm(page, { service = FORM_VALUES.service } = {}) {
  await page.locator("#name").fill(FORM_VALUES.name);
  await page.locator("#email").fill(FORM_VALUES.email);
  await selectFutureDate(page);
  await selectTime(page);
  await page.locator("#message").fill(FORM_VALUES.message);

  if (service) {
    await page.locator(`.service-card[data-service="${service}"]`).click();
  }

  await expect(page.locator("#submitBtn")).toBeEnabled();
}

test.describe("Build page", () => {
  test("renders the booking header, services, fields and initial disabled submit", async ({
    page,
  }) => {
    await openBuildPage(page);

    await expect(page.locator(".booking-header h2")).toHaveText(
      "Build a Session"
    );
    await expect(page.locator(".booking-header p")).toHaveText(
      "Schedule your appointment below."
    );
    await expect(page.locator(".booking-services-title")).toHaveText(
      "What service do you need?"
    );

    const cards = page.locator(".service-card");
    await expect(cards).toHaveCount(SERVICES.length);
    await expect(page.locator(".service-card-desc")).toHaveCount(
      SERVICES.length
    );

    for (let index = 0; index < SERVICES.length; index += 1) {
      await expect(cards.nth(index)).toHaveAttribute(
        "data-service",
        SERVICES[index]
      );
      await expect(cards.nth(index).locator(".service-card-title")).toHaveText(
        SERVICES[index]
      );
      await expect(cards.nth(index)).not.toHaveClass(/selected/);
    }

    await expect(cards.first().locator(".service-card-desc")).toContainText(
      "Custom websites"
    );
    await expect(page.locator("#serviceInput")).toHaveValue("");

    await expect(page.locator("#name")).toHaveAttribute("maxlength", "50");
    await expect(page.locator("#message")).toHaveAttribute("maxlength", "500");
    await expect(page.locator("#nameCount")).toHaveText("0");
    await expect(page.locator("#messageCount")).toHaveText("0");
    await expect(page.locator(".required-star")).toHaveCount(5);

    const submit = page.locator("#submitBtn");
    await expect(submit).toBeDisabled();
    await expect(page.locator("#submitText")).toHaveText("Submit Build");
    await expect(page.locator("#bookingStatus")).toHaveText("");
  });

  test("selects exactly one service card and stores its value", async ({
    page,
  }) => {
    await openBuildPage(page);

    const cards = page.locator(".service-card");
    for (let index = 0; index < SERVICES.length; index += 1) {
      await cards.nth(index).click();
      await expect(cards.nth(index)).toHaveClass(/selected/);
      await expect(page.locator(".service-card.selected")).toHaveCount(1);
      await expect(page.locator("#serviceInput")).toHaveValue(SERVICES[index]);
    }

    await expect(cards.last()).toHaveClass(/selected/);
    await expect(cards.first()).not.toHaveClass(/selected/);
  });

  test("validates every required field and email formatting", async ({
    page,
  }) => {
    await openBuildPage(page);

    const submit = page.locator("#submitBtn");
    const emailMessage = page.locator("#emailMsg");

    await expect(submit).toBeDisabled();

    await page.locator("#name").fill(FORM_VALUES.name);
    await expect(page.locator("#nameCount")).toHaveText(
      String(FORM_VALUES.name.length)
    );
    await expect(submit).toBeDisabled();

    await page.locator("#email").fill("not-an-email");
    await expect(emailMessage).toHaveText("Invalid email format");
    await expect(emailMessage).toHaveCSS("color", "rgb(231, 76, 60)");
    await expect(submit).toBeDisabled();

    await page.locator("#email").fill(FORM_VALUES.email);
    await expect(emailMessage).toHaveText("");
    await expect(submit).toBeDisabled();

    await page.locator("#message").fill(FORM_VALUES.message);
    await expect(page.locator("#messageCount")).toHaveText(
      String(FORM_VALUES.message.length)
    );
    await expect(submit).toBeDisabled();

    const selectedDate = await selectFutureDate(page);
    expect(selectedDate).not.toBe("");
    await expect(submit).toBeDisabled();

    await selectTime(page);
    await expect(submit).toBeEnabled();

    await page.locator("#name").fill("   ");
    await expect(submit).toBeDisabled();

    await page.locator("#name").fill(FORM_VALUES.name);
    await expect(submit).toBeEnabled();

    await page.locator("#message").fill("");
    await expect(submit).toBeDisabled();

    await page.locator("#message").fill(FORM_VALUES.message);
    await expect(submit).toBeEnabled();

    await page.locator("#email").fill("broken@");
    await expect(submit).toBeDisabled();
    await expect(emailMessage).toHaveText("Invalid email format");

    await page.locator("#email").fill(FORM_VALUES.email);
    await expect(emailMessage).toHaveText("");
    await expect(submit).toBeEnabled();
  });

  test("navigates the date picker and links date and time values", async ({
    page,
  }) => {
    await openBuildPage(page);

    const dateInput = page.locator(`${DATE_FIELD} .dtp-input`);
    const dateDropdown = page.locator(`${DATE_FIELD} .dtp-dropdown`);
    const dateHidden = page.locator(`${DATE_FIELD} .dtp-hidden`);
    const timeInput = page.locator(`${TIME_FIELD} .dtp-input`);
    const timeDropdown = page.locator(`${TIME_FIELD} .dtp-dropdown`);
    const timeHidden = page.locator(`${TIME_FIELD} .dtp-hidden`);
    const navButtons = page.locator(`${DATE_FIELD} .dtp-nav-btn`);

    await dateInput.click();
    await expect(dateDropdown).toHaveClass(/open/);

    const monthLabel = page.locator(`${DATE_FIELD} .dtp-calendar-month`);
    const currentMonth = await page.evaluate(() =>
      new Intl.DateTimeFormat("en-US", { month: "long", year: "numeric" }).format(
        new Date()
      )
    );
    await expect(monthLabel).toHaveText(currentMonth);
    await expect(navButtons.nth(1)).toBeEnabled();
    await expect(
      page.locator(`${DATE_FIELD} .dtp-day.other-month`).first()
    ).toBeDisabled();

    await navButtons.nth(1).click();
    await expect(dateDropdown).toHaveClass(/open/);
    await expect(page.locator(`${DATE_FIELD} .dtp-calendar-month`)).not.toHaveText(
      currentMonth
    );
    await expect(navButtons.nth(0)).toBeEnabled();

    await navButtons.nth(0).click();
    await expect(page.locator(`${DATE_FIELD} .dtp-calendar-month`)).toHaveText(
      currentMonth
    );

    await navButtons.nth(0).click();
    await expect(page.locator(`${DATE_FIELD} .dtp-calendar-month`)).not.toHaveText(
      currentMonth
    );
    await expect(navButtons.nth(0)).toBeDisabled();

    await navButtons.nth(1).click();
    await expect(page.locator(`${DATE_FIELD} .dtp-calendar-month`)).toHaveText(
      currentMonth
    );
    await expect(navButtons.nth(0)).toBeEnabled();

    await selectTime(page);
    await expect(timeHidden).toHaveValue(FORM_VALUES.time);
    await expect(timeInput).toHaveValue(FORM_VALUES.timeLabel);

    await timeInput.click();
    await expect(timeDropdown).toHaveClass(/open/);
    await expect(
      page.locator(`${TIME_FIELD} .dtp-time-slot`)
    ).toHaveCount(33);

    await dateInput.click();
    await expect(dateDropdown).toHaveClass(/open/);
    await expect(timeDropdown).not.toHaveClass(/open/);
    const targetDate = await futureDateString(page);
    const target = page.locator(
      `${DATE_FIELD} .dtp-day[data-date="${targetDate}"]`
    );
    if ((await target.count()) === 0) {
      await navButtons.nth(1).click();
      await page.locator(`${DATE_FIELD} .dtp-day[data-date]`).first().click();
    } else {
      await target.click();
    }

    const selectedDate = await dateHidden.inputValue();
    expect(selectedDate).not.toBe("");
    await expect(dateInput).not.toHaveValue("");
  });

  test("submits the full payload, shows success and resets every control", async ({
    page,
    mockSite,
  }) => {
    mockSite.booking.delayMs = 400;
    await openBuildPage(page);
    await fillBookingForm(page);

    const selectedDate = await page.locator(`${DATE_FIELD} .dtp-hidden`).inputValue();
    const submit = page.locator("#submitBtn");

    await submit.click();
    await expect(submit).toBeDisabled();
    await expect(page.locator("#submitText")).toHaveText("Sending...");
    await expect(page.locator("#submitIcon")).toHaveAttribute(
      "name",
      "hourglass-outline"
    );

    const status = page.locator("#bookingStatus");
    await expect(status).toHaveText(SUCCESS_MESSAGE);
    await expect(status).toHaveClass(/booking-status--success/);

    await expect.poll(() => mockSite.booking.requests.length).toBe(1);
    expect(mockSite.booking.requests[0]).toEqual({
      name: FORM_VALUES.name,
      email: FORM_VALUES.email,
      preferred_date: selectedDate,
      preferred_time: FORM_VALUES.time,
      message: FORM_VALUES.message,
      service: FORM_VALUES.service,
      hcaptcha_token: "",
    });

    await expect(page.locator("#name")).toHaveValue("");
    await expect(page.locator("#email")).toHaveValue("");
    await expect(page.locator("#message")).toHaveValue("");
    await expect(page.locator(`${DATE_FIELD} .dtp-input`)).toHaveValue("");
    await expect(page.locator(`${TIME_FIELD} .dtp-input`)).toHaveValue("");
    await expect(page.locator(`${DATE_FIELD} .dtp-hidden`)).toHaveValue("");
    await expect(page.locator(`${TIME_FIELD} .dtp-hidden`)).toHaveValue("");
    await expect(page.locator("#nameCount")).toHaveText("0");
    await expect(page.locator("#messageCount")).toHaveText("0");
    await expect(page.locator("#serviceInput")).toHaveValue("");
    await expect(page.locator(".service-card.selected")).toHaveCount(0);
    await expect(submit).toBeDisabled();
    await expect(page.locator("#submitText")).toHaveText("Submit Build");
    await expect(page.locator("#submitIcon")).toHaveAttribute(
      "name",
      "paper-plane-outline"
    );
  });

  test("shows server and fallback errors, preserves input and clears on selection", async ({
    page,
    mockSite,
  }) => {
    await openBuildPage(page);
    await fillBookingForm(page);

    mockSite.booking.mode = "error";
    mockSite.booking.errorMessage = "Mock booking rejection.";
    await page.locator("#submitBtn").click();

    const status = page.locator("#bookingStatus");
    await expect(status).toHaveText("Mock booking rejection.");
    await expect(status).toHaveClass(/booking-status--error/);
    await expect(page.locator("#submitBtn")).toBeEnabled();
    await expect(page.locator("#name")).toHaveValue(FORM_VALUES.name);
    await expect(page.locator("#email")).toHaveValue(FORM_VALUES.email);
    await expect(page.locator("#message")).toHaveValue(FORM_VALUES.message);
    await expect(
      page.locator(`.service-card[data-service="${FORM_VALUES.service}"]`)
    ).toHaveClass(/selected/);

    mockSite.booking.mode = "empty-error";
    await page.locator("#submitBtn").click();
    await expect(status).toHaveText(GENERIC_MESSAGE);
    await expect(status).toHaveClass(/booking-status--error/);

    await page.locator('.service-card[data-service="Consultation"]').click();
    await expect(status).toHaveText("");
    await expect(status).toHaveClass("booking-status");
    await expect(
      page.locator('.service-card[data-service="Consultation"]')
    ).toHaveClass(/selected/);
  });

  test("reports a network failure and keeps the form ready for another try", async ({
    page,
    mockSite,
  }) => {
    await openBuildPage(page);
    await fillBookingForm(page);

    mockSite.booking.mode = "network";
    await page.locator("#submitBtn").click();

    const status = page.locator("#bookingStatus");
    await expect(status).toHaveText(NETWORK_MESSAGE);
    await expect(status).toHaveClass(/booking-status--error/);
    await expect(page.locator("#submitBtn")).toBeEnabled();
    await expect(page.locator("#submitText")).toHaveText("Submit Build");
    await expect(page.locator("#name")).toHaveValue(FORM_VALUES.name);
    await expect(page.locator("#message")).toHaveValue(FORM_VALUES.message);
    expect(mockSite.booking.requests).toHaveLength(1);
  });

  test("shows the rate-limit countdown and restores submission after it ends", async ({
    page,
    mockSite,
  }) => {
    mockSite.booking.mode = "rate-limit";
    mockSite.booking.retryAfterSeconds = 2;

    await openBuildPage(page);
    await fillBookingForm(page);
    await page.locator("#submitBtn").click();

    const status = page.locator("#bookingStatus");
    const countdown = page.locator(".booking-retry-countdown");
    const submit = page.locator("#submitBtn");

    await expect(status).toHaveClass(/booking-status--error/);
    await expect(status).toContainText("maximum of 10 booking requests");
    await expect(countdown).toContainText("Retry in");
    await expect(submit).toBeDisabled();

    await expect(countdown).toHaveCount(0, { timeout: 6000 });
    await expect(submit).toBeEnabled();
    await expect(page.locator("#submitText")).toHaveText("Submit Build");
  });
});

test.describe("Build page mobile", () => {
  test.use({ viewport: { width: 480, height: 900 } });

  test("keeps every control reachable and completes a booking", async ({
    page,
    mockSite,
  }) => {
    await openBuildPage(page);

    await expect(page.locator(".booking-header h2")).toBeVisible();
    await expect(page.locator(".service-card")).toHaveCount(SERVICES.length);

    const layoutFits = await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll(".service-card"));
      return (
        document.documentElement.scrollWidth <= window.innerWidth + 1 &&
        cards.every((card) => {
          const rect = card.getBoundingClientRect();
          return rect.left >= 0 && rect.right <= window.innerWidth;
        })
      );
    });
    expect(layoutFits).toBe(true);

    await expect(page.locator(".service-card-desc").first()).toBeHidden();
    await expect(page.locator(".booking-services-grid")).toHaveCSS(
      "display",
      "flex"
    );

    await page.locator(`${DATE_FIELD} .dtp-input`).click();
    const dateDropdown = page.locator(`${DATE_FIELD} .dtp-dropdown`);
    await expect(dateDropdown).toHaveClass(/open/);
    const dateFits = await dateDropdown.evaluate((element) => {
      const rect = element.getBoundingClientRect();
      return rect.left >= 0 && rect.right <= window.innerWidth;
    });
    expect(dateFits).toBe(true);
    await page.locator(`${DATE_FIELD} .dtp-input`).click();

    await fillBookingForm(page);
    await page.locator("#submitBtn").click();

    await expect(page.locator("#bookingStatus")).toHaveText(SUCCESS_MESSAGE);
    await expect(page.locator("#bookingStatus")).toHaveClass(
      /booking-status--success/
    );
    await expect(page.locator("#submitBtn")).toBeDisabled();
    await expect.poll(() => mockSite.booking.requests.length).toBe(1);
  });
});
