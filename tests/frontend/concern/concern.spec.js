import { expect, test } from "../support/test.js";

const PROFESSIONAL_SURVEY = "https://forms.gle/5UqVgzzxgkJS11Qj9";
const SOCIAL_SURVEY = "https://forms.gle/QV5kHc3STEFDFUYf9";

async function openConcernPage(page, baseURL, hostname = null) {
  const url = new URL(baseURL);
  if (hostname) {
    url.hostname = hostname;
  }
  url.pathname = "/concern";
  url.search = "";
  url.hash = "";

  await page.goto(url.toString(), { waitUntil: "domcontentloaded" });
  await expect(page.locator("#concern")).toBeVisible();
  return url;
}

async function clickSurvey(page) {
  const [popup] = await Promise.all([
    page.waitForEvent("popup"),
    page.locator(".concern-btn").click(),
  ]);
  return popup;
}

test.describe("Concern page", () => {
  test("renders the concern content and the professional survey link", async ({
    page,
    baseURL,
  }) => {
    await openConcernPage(page, baseURL);

    await expect(page.locator("#concern h2")).toHaveText("Concern");
    await expect(page.locator("#concern p")).toContainText(
      "If you have any feedback or thoughts to share about me"
    );

    const surveyLink = page.locator(".concern-button a");
    await expect(surveyLink).toHaveAttribute("href", PROFESSIONAL_SURVEY);
    await expect(surveyLink).toHaveAttribute("target", "_blank");

    const surveyButton = page.locator(".concern-btn");
    await expect(surveyButton).toBeVisible();
    await expect(surveyButton).toHaveText("Take the survey");
  });

  test("opens the professional survey form when the button is clicked", async ({
    page,
    baseURL,
  }) => {
    await openConcernPage(page, baseURL);

    const popup = await clickSurvey(page);
    await expect(popup).toHaveURL(PROFESSIONAL_SURVEY);
    await popup.close();
  });

  test("opens the social survey form on the social host", async ({
    page,
    baseURL,
  }) => {
    await openConcernPage(page, baseURL, "social.jpastack.local");

    await expect(page.locator(".concern-button a")).toHaveAttribute(
      "href",
      SOCIAL_SURVEY
    );

    const popup = await clickSurvey(page);
    await expect(popup).toHaveURL(SOCIAL_SURVEY);
    await popup.close();
  });

  test("activates the survey button from the keyboard", async ({
    page,
    baseURL,
  }) => {
    await openConcernPage(page, baseURL);

    const surveyButton = page.locator(".concern-btn");
    await surveyButton.focus();
    await expect(surveyButton).toBeFocused();

    const [popup] = await Promise.all([
      page.waitForEvent("popup"),
      page.keyboard.press("Enter"),
    ]);

    await expect(popup).toHaveURL(PROFESSIONAL_SURVEY);
    await popup.close();
  });
});

test.describe("Concern page mobile", () => {
  test.use({ viewport: { width: 480, height: 900 } });

  test("keeps the survey button visible and opens the form", async ({
    page,
    baseURL,
  }) => {
    await openConcernPage(page, baseURL);

    const surveyButton = page.locator(".concern-btn");
    await expect(surveyButton).toBeVisible();
    await expect(surveyButton).toHaveText("Take the survey");

    const fitsViewport = await page.evaluate(() => {
      const button = document.querySelector(".concern-btn");
      const rect = button.getBoundingClientRect();
      return (
        rect.left >= 0 &&
        rect.right <= window.innerWidth &&
        document.documentElement.scrollWidth <= window.innerWidth + 1
      );
    });
    expect(fitsViewport).toBe(true);

    const popup = await clickSurvey(page);
    await expect(popup).toHaveURL(PROFESSIONAL_SURVEY);
    await popup.close();
  });
});
