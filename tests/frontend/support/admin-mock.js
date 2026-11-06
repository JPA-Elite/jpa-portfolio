const ADMIN_IMAGE = "/static/images/cert1.webp";
const ADMIN_VIDEO = "https://example.com/admin-mock-video.mp4";
const ADMIN_IP = "mock-playwright-ip";

const BOOTSTRAP_CSS = `
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;overflow:auto;outline:0;z-index:1055}
.modal.show{display:block!important}
.modal-dialog{position:relative;width:auto;margin:.5rem;pointer-events:none}
.modal-dialog.modal-lg{max-width:800px}
.modal-dialog.modal-xl{max-width:1140px}
@media (min-width:576px){.modal-dialog{max-width:500px;margin:1.75rem auto}}
.modal-content{position:relative;display:flex;flex-direction:column;width:100%;pointer-events:auto;background:#fff;border:1px solid rgba(0,0,0,.2);border-radius:.3rem;padding:1rem}
.modal-backdrop{position:fixed;top:0;left:0;z-index:1050;width:100vw;height:100vh;background-color:#000}
.modal-backdrop.show{opacity:.5}
.modal-open{overflow:hidden}
`;

const BOOTSTRAP_STUB = `(() => {
  if (window.bootstrap && window.bootstrap.Modal) return;

  const backdrops = new WeakMap();

  class Modal {
    constructor(element, options = {}) {
      if (!element) throw new Error("Modal element is required");
      this._element = element;
      this._options = options;
      this._isShown = false;
      this._element.__bootstrapModal = this;
      this._element.addEventListener("click", (event) => {
        const dismiss = event.target.closest("[data-bs-dismiss='modal'],[data-dismiss='modal']");
        if (dismiss && this._element.contains(dismiss)) {
          event.preventDefault();
          this.hide();
        }
      });
    }

    static getInstance(element) {
      return element ? element.__bootstrapModal || null : null;
    }

    static getOrCreateInstance(element, options) {
      return Modal.getInstance(element) || new Modal(element, options);
    }

    show() {
      if (this._isShown) return;
      this._element.dispatchEvent(new Event("show.bs.modal", { bubbles: true }));
      this._element.classList.add("show");
      this._element.style.display = "block";
      this._element.removeAttribute("aria-hidden");
      this._element.setAttribute("aria-modal", "true");
      document.body.classList.add("modal-open");
      const backdrop = document.createElement("div");
      backdrop.className = "modal-backdrop fade show";
      document.body.appendChild(backdrop);
      backdrops.set(this._element, backdrop);
      this._isShown = true;
      this._element.dispatchEvent(new Event("shown.bs.modal", { bubbles: true }));
    }

    hide() {
      if (!this._isShown) return;
      this._element.dispatchEvent(new Event("hide.bs.modal", { bubbles: true }));
      this._element.classList.remove("show");
      this._element.style.display = "none";
      this._element.setAttribute("aria-hidden", "true");
      this._element.removeAttribute("aria-modal");
      const backdrop = backdrops.get(this._element);
      if (backdrop) backdrop.remove();
      backdrops.delete(this._element);
      if (!document.querySelector(".modal.show")) {
        document.body.classList.remove("modal-open");
      }
      this._isShown = false;
      this._element.dispatchEvent(new Event("hidden.bs.modal", { bubbles: true }));
    }

    toggle() {
      if (this._isShown) this.hide();
      else this.show();
    }

    dispose() {
      this.hide();
      delete this._element.__bootstrapModal;
    }
  }

  const passive = {
    show() {},
    hide() {},
    toggle() {},
    dispose() {},
  };

  window.bootstrap = {
    Modal,
    Dropdown: {
      getInstance() { return null; },
      getOrCreateInstance() { return { ...passive }; },
    },
    Collapse: {
      getInstance() { return null; },
      getOrCreateInstance() { return { ...passive }; },
    },
    Tooltip: {
      getInstance() { return null; },
      getOrCreateInstance() { return { ...passive }; },
    },
    Popover: {
      getInstance() { return null; },
      getOrCreateInstance() { return { ...passive }; },
    },
  };

  const closeDropdowns = (exceptMenu) => {
    document.querySelectorAll(".dropdown-menu.show").forEach((menu) => {
      if (menu === exceptMenu) return;
      menu.classList.remove("show");
      const toggle = menu.closest(".dropdown")?.querySelector("[data-bs-toggle='dropdown']");
      if (toggle) toggle.setAttribute("aria-expanded", "false");
    });
  };

  document.addEventListener("click", (event) => {
    const dropdownToggle = event.target.closest("[data-bs-toggle='dropdown']");
    if (dropdownToggle) {
      event.preventDefault();
      const menu = dropdownToggle.closest(".dropdown")?.querySelector(".dropdown-menu");
      if (menu) {
        const willOpen = !menu.classList.contains("show");
        closeDropdowns(menu);
        menu.classList.toggle("show", willOpen);
        dropdownToggle.setAttribute("aria-expanded", String(willOpen));
      }
      return;
    }

    const dropdownItem = event.target.closest(".dropdown-menu a,.dropdown-menu button");
    if (dropdownItem) {
      closeDropdowns();
      return;
    }

    closeDropdowns();

    const toggle = event.target.closest("[data-bs-toggle='modal']");
    if (toggle) {
      const selector = toggle.getAttribute("data-bs-target") || toggle.getAttribute("href");
      const target = selector ? document.querySelector(selector) : null;
      if (target) {
        event.preventDefault();
        Modal.getOrCreateInstance(target).show();
      }
      return;
    }

    const alertButton = event.target.closest("[data-dismiss='alert'],[data-bs-dismiss='alert']");
    if (alertButton) {
      const alert = alertButton.closest(".alert");
      if (alert) alert.remove();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeDropdowns();
  });
})();`;

const ADMINLTE_STUB = `(() => {
  if (window.__playwrightAdminLte) return;
  window.__playwrightAdminLte = true;

  document.addEventListener("click", (event) => {
    const sidebarToggle = event.target.closest("[data-lte-toggle='sidebar']");
    if (sidebarToggle) {
      event.preventDefault();
      const body = document.body;
      if (body.classList.contains("sidebar-collapse")) {
        body.classList.remove("sidebar-collapse");
        body.classList.add("sidebar-open");
      } else {
        body.classList.add("sidebar-collapse");
        body.classList.remove("sidebar-open");
      }
      return;
    }
  });
})();`;

const JQUERY_STUB = `(() => {
  class Wrapped {
    constructor(items) {
      this.items = items;
    }

    modal(options) {
      this.items.forEach((element) => {
        window.bootstrap.Modal.getOrCreateInstance(element, options).show();
      });
      return this;
    }

    on(event, selector, handler) {
      const callback = typeof selector === "function" ? selector : handler;
      const targetSelector = typeof selector === "string" ? selector : null;
      this.items.forEach((element) => {
        element.addEventListener(event, (browserEvent) => {
          if (!targetSelector) {
            callback.call(element, browserEvent);
            return;
          }
          const match = browserEvent.target.closest(targetSelector);
          if (match && element.contains(match)) callback.call(match, browserEvent);
        });
      });
      return this;
    }

    addClass(name) {
      this.items.forEach((element) => element.classList.add(name));
      return this;
    }

    removeClass(name) {
      this.items.forEach((element) => element.classList.remove(name));
      return this;
    }

    text(value) {
      if (value === undefined) return this.items[0]?.textContent || "";
      this.items.forEach((element) => { element.textContent = value; });
      return this;
    }

    val(value) {
      if (value === undefined) return this.items[0]?.value ?? "";
      this.items.forEach((element) => { element.value = value; });
      return this;
    }
  }

  function jquery(argument) {
    if (typeof argument === "string") {
      return new Wrapped(Array.from(document.querySelectorAll(argument)));
    }
    if (argument instanceof Element) {
      return new Wrapped([argument]);
    }
    if (argument && typeof argument.length === "number") {
      return new Wrapped(Array.from(argument));
    }
    return new Wrapped([]);
  }

  jquery.fn = Wrapped.prototype;
  window.jQuery = jquery;
  window.$ = jquery;
})();`;

function jsonResponse(route, payload, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    headers: { "cache-control": "no-store" },
    body: JSON.stringify(payload),
  });
}

function parseJsonBody(request) {
  try {
    return request.postDataJSON() || {};
  } catch {
    return {};
  }
}

function localized(en, ceb = en, fr = en, fil = en) {
  return { en, ceb, fr, fil_PH: fil };
}

function textOf(value) {
  if (value && typeof value === "object") {
    return Object.values(value).filter((entry) => typeof entry === "string").join(" ");
  }
  return String(value ?? "");
}

function field(request, name) {
  const body = request.postData() || "";
  const match = body.match(
    new RegExp(`name="${name}"\\r?\\n\\r?\\n([\\s\\S]*?)\\r?\\n--`, "i")
  );
  if (!match) return null;
  const raw = match[1].replace(/\r$/, "");
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

function boolField(request, name, fallback) {
  const value = field(request, name);
  if (value === null) return fallback;
  return String(value).toLowerCase() === "true" || value === true;
}

function arrayField(request, name, fallback = []) {
  const value = field(request, name);
  return Array.isArray(value) ? value : fallback;
}

function jsonField(request, name) {
  const value = field(request, name);
  if (value && typeof value === "object") return value;
  return null;
}

function slugify(value) {
  return String(value || "mock-app")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function gallerySeed() {
  return Array.from({ length: 12 }, (_, index) => {
    const number = index + 1;
    const titles = [
      "Mock Aurora Frame",
      "Mock Forest Frame",
      "Mock Harbor Frame",
      "Mock Studio Frame",
    ];
    return {
      _id: `pw-admin-gallery-${String(number).padStart(2, "0")}`,
      title: localized(`${titles[index % titles.length]} ${String(number).padStart(2, "0")}`),
      description: localized(`Gallery description ${String(number).padStart(2, "0")} for deterministic admin coverage.`),
      image_url: `/static/images/cert${(index % 5) + 1}.webp`,
      tags: index === 0 ? ["aurora", "sky"] : [`tag-${number}`, "mock"],
    };
  });
}

function videoSeed() {
  return Array.from({ length: 8 }, (_, index) => {
    const number = index + 1;
    return {
      _id: `pw-admin-video-${String(number).padStart(2, "0")}`,
      title: localized(index === 0 ? "Mock Beacon Video" : `Mock Video ${String(number).padStart(2, "0")}`),
      description: localized(`Video description ${String(number).padStart(2, "0")} for admin coverage.`),
      video_url: `https://example.com/admin-video-${String(number).padStart(2, "0")}.mp4`,
      file: null,
      tags: index === 0 ? ["beacon", "studio"] : [`video-tag-${number}`, "mock"],
    };
  });
}

function musicSeed() {
  return Array.from({ length: 12 }, (_, index) => {
    const number = index + 1;
    return {
      _id: `pw-admin-music-${String(number).padStart(2, "0")}`,
      title: index === 0 ? "Mock Aurora Theme" : `Mock Admin Track ${String(number).padStart(2, "0")}`,
      artist: `Mock Admin Artist ${String(number).padStart(2, "0")}`,
      url: `https://example.com/admin-music-${String(number).padStart(2, "0")}.mp3`,
      image: `/static/images/cert${(index % 5) + 1}.webp`,
      duration: `3:${String(10 + index).padStart(2, "0")}`,
      lyrics: index === 0 ? "[00:00.00]Mock admin opening line" : "",
      category: index % 3 === 0 ? "Rap" : index % 3 === 1 ? "Pop" : "Chill",
    };
  });
}

function keyProjectSeed() {
  const statuses = ["shipped", "building", "planned"];
  return Array.from({ length: 7 }, (_, index) => {
    const number = index + 1;
    return {
      _id: `pw-admin-project-${String(number).padStart(2, "0")}`,
      title: localized(index === 0 ? "Mock Atlas Platform" : `Mock Project ${String(number).padStart(2, "0")}`),
      description: localized(`Project description ${number} for admin coverage.`),
      stack: localized(`Flask • MongoDB • Vite ${number}`),
      status: statuses[index % statuses.length],
      image_url: `/static/images/cert${(index % 5) + 1}.webp`,
      demo_url: `https://example.com/admin-project-${number}/demo`,
      repo_url: `https://example.com/admin-project-${number}/repo`,
      sort_order: number,
      slides: [
        {
          id: `pw-admin-slide-${number}`,
          title: localized(`Project ${number} overview`),
          description: localized(`Project ${number} slide`),
          image_url: "/static/images/jaom_home.webp",
        },
      ],
      is_active: index !== 5,
    };
  });
}

function roadmapSeed() {
  const companies = ["Northwind Labs", "Harbor Studio", "Aurora Works", "Beacon Group"];
  return Array.from({ length: 6 }, (_, index) => {
    const number = index + 1;
    return {
      _id: `pw-admin-roadmap-${String(number).padStart(2, "0")}`,
      company_name: index === 0 ? "Northwind Labs" : companies[index % companies.length],
      role_title: index === 0 ? "Lead Platform Engineer" : `Mock Engineer ${number}`,
      period: `202${number} - 202${number + 1}`,
      employment_type: index % 2 === 0 ? "Full-time" : "Contract",
      location: "Remote",
      definition: "Engineering role",
      summary: `Roadmap summary ${number} for deterministic admin coverage.`,
      highlights: `Built platform ${number}\nImproved reliability ${number}`,
      cover_image_url: `/static/images/cert${(index % 5) + 1}.webp`,
      activities: [
        {
          id: `pw-admin-activity-${number}`,
          image_url: "/static/images/jaom_about_us.webp",
          title: localized(`Roadmap activity ${number}`),
          caption: localized(`Roadmap caption ${number}`),
        },
      ],
      accent_color: "#0d6efd",
      sort_order: number,
      is_active: index !== 4,
    };
  });
}

function builtAppSeed() {
  return Array.from({ length: 6 }, (_, index) => {
    const number = index + 1;
    return {
      _id: `pw-admin-app-${String(number).padStart(2, "0")}`,
      slug: `mock-admin-app-${number}`,
      platform: index % 2 === 0 ? "mobile" : "desktop",
      version: `1.${number}.0`,
      icon: "bi-app",
      icon_image_url: "/static/images/cert1.webp",
      name: localized(index === 0 ? "Mock App One" : `Mock App ${String(number).padStart(2, "0")}`),
      short_description: localized(`Short app description ${number}.`),
      full_description: {
        en: [`Full app description ${number} paragraph one.`, `Paragraph two for app ${number}.`],
        ceb: [],
        fr: [],
        fil_PH: [],
      },
      snapshots: [
        { id: `pw-admin-snapshot-${number}`, image_url: "/static/images/jaom_home.webp", sort_order: 1 },
      ],
      technologies: [
        { key: "framework", label: "Framework", icon: "bi-code", value: "Flask" },
      ],
      download_url: `https://example.com/admin-app-${number}.apk`,
      sort_order: number,
      is_active: index !== 3,
    };
  });
}

function loginAttemptSeed() {
  return Array.from({ length: 7 }, (_, index) => ({
    _id: index === 0 ? ADMIN_IP : `mock-ip-${String(index + 1).padStart(2, "0")}`,
    device: index === 0 ? "Playwright Browser" : `Mock Device ${index + 1}`,
    attempts: index,
    lockout_until: index > 3 ? "2026-10-23 12:00:00" : "None",
  }));
}

function bookingSeed() {
  return Array.from({ length: 8 }, (_, index) => {
    const number = index + 1;
    return {
      _id: `pw-admin-booking-${String(number).padStart(2, "0")}`,
      name: index === 0 ? "Alice Client" : `Mock Client ${String(number).padStart(2, "0")}`,
      email: `client${number}@example.com`,
      preferred_date: `2026-11-${String(10 + index).padStart(2, "0")}`,
      preferred_time: "10:00",
      message: index === 0
        ? "This is a deliberately long booking message used to verify the expandable message control in the admin booking request table."
        : `Booking message ${number}`,
      created_at: `2026-10-${String(10 + index).padStart(2, "0")} 09:00:00`,
    };
  });
}

function activitySeed() {
  return Array.from({ length: 13 }, (_, index) => ({
    _id: `pw-admin-activity-record-${String(index + 1).padStart(2, "0")}`,
    timestamp: new Date(Date.UTC(2026, 8, 25 + index, 8, index, 0)).toISOString(),
    user_id: index % 2 === 0 ? "pw-admin" : "mock-visitor",
    method: index % 3 === 0 ? "POST" : "GET",
    path: index === 12 ? "/admin/api/add-gallery" : `/mock/activity/${index + 1}`,
    status_code: index % 2 === 0 ? 200 : 404,
    body: { index: index + 1 },
  }));
}

function visitSeed() {
  return Array.from({ length: 13 }, (_, index) => ({
    _id: `pw-admin-visit-${String(index + 1).padStart(2, "0")}`,
    system: index % 2 === 0 ? "Desktop" : "Mobile",
    device: index % 2 === 0 ? "Chrome" : "Safari",
    browser: index % 2 === 0 ? "Chrome 130" : "Safari 18",
    os: index % 2 === 0 ? "Windows" : "iOS",
    page: index === 0 ? "/portfolio" : `/mock/page/${index + 1}`,
    site: index % 3 === 0 ? "social" : "professional",
    ip_address: `10.0.0.${index + 1}`,
    city: "Manila",
    country: "Philippines",
    occurred_at: new Date(Date.UTC(2026, 9, 20 - index, 9, index, 0)).toISOString(),
  }));
}

export function createAdminState() {
  return {
    gallery: gallerySeed(),
    video: videoSeed(),
    music: musicSeed(),
    keyProjects: keyProjectSeed(),
    roadmaps: roadmapSeed(),
    builtApps: builtAppSeed(),
    loginAttempts: loginAttemptSeed(),
    bookings: bookingSeed(),
    activity: activitySeed(),
    visits: visitSeed(),
    sequence: 100,
    requests: [],
    profile: {
      username: "Mock Admin",
      email: "admin@example.com",
      profileImage: "/static/images/avatars/avatar_orange.svg",
    },
    face: {
      registered: 0,
      verified: 0,
      failRegister: false,
      failVerify: false,
    },
  };
}

function sortItems(items, order = "desc", numericField = null) {
  const copy = [...items];
  if (numericField) {
    copy.sort((left, right) => Number(left[numericField] || 0) - Number(right[numericField] || 0));
  }
  if (String(order).toLowerCase() === "desc") copy.reverse();
  return copy;
}

function paginate(items, page, perPage) {
  const total = items.length;
  const safePage = Math.max(1, Number(page) || 1);
  const safePerPage = Math.max(1, Number(perPage) || 10);
  const start = (safePage - 1) * safePerPage;
  return {
    items: items.slice(start, start + safePerPage),
    total,
    totalPages: Math.ceil(total / safePerPage),
    page: safePage,
    perPage: safePerPage,
  };
}

function matches(items, search, fields) {
  const needle = String(search || "").trim().toLowerCase();
  if (!needle) return items;
  return items.filter((item) =>
    fields.some((name) => textOf(item[name]).toLowerCase().includes(needle))
  );
}

function paginationParams(url) {
  return {
    page: url.searchParams.get("page") || 1,
    perPage: url.searchParams.get("per_page") || url.searchParams.get("perPage") || 10,
    order: url.searchParams.get("order") || "desc",
    search: url.searchParams.get("search") || "",
  };
}

function nextId(state, prefix) {
  state.sequence += 1;
  return `pw-admin-${prefix}-${state.sequence}`;
}

function addActivity(state, method, path) {
  state.activity.unshift({
    _id: nextId(state, "activity-record"),
    timestamp: new Date().toISOString(),
    user_id: "pw-admin",
    method,
    path,
    status_code: 200,
    body: { source: "playwright" },
  });
}

function listResponse(route, items, params, key, numericField = null) {
  const page = paginate(sortItems(items, params.order, numericField), params.page, params.perPage);
  return {
    [key]: page.items,
    [`total_${key}`]: page.total,
    total_pages: page.totalPages,
    page: page.page,
    per_page: page.perPage,
    search: params.search,
  };
}

function parseLocalized(value, fallback) {
  return value && typeof value === "object" ? value : fallback;
}

function resourceEndpoint(path) {
  const list = {
    "/admin/api/gallery-list": "gallery",
    "/admin/api/video-list": "video",
    "/admin/api/music-list": "music",
    "/admin/api/key-project-list": "keyProjects",
    "/admin/api/company-roadmap-list": "roadmaps",
    "/admin/api/built-app-list": "builtApps",
    "/admin/api/login-attempts": "loginAttempts",
    "/admin/api/booking-requests": "bookings",
  };
  return list[path] || null;
}

function recordsFor(state, resource) {
  return state[resource];
}

function createRecord(state, resource, request) {
  const id = nextId(state, resource.replace(/[A-Z]/g, (match) => `-${match.toLowerCase()}`));
  if (resource === "gallery") {
    return {
      _id: id,
      title: parseLocalized(jsonField(request, "title"), localized("Mock New Gallery")),
      description: parseLocalized(jsonField(request, "description"), localized("New gallery description")),
      image_url: ADMIN_IMAGE,
      tags: String(field(request, "tags") || "mock").split(",").map((tag) => tag.trim()).filter(Boolean),
    };
  }
  if (resource === "video") {
    return {
      _id: id,
      title: parseLocalized(jsonField(request, "title"), localized("Mock New Video")),
      description: parseLocalized(jsonField(request, "description"), localized("New video description")),
      video_url: ADMIN_VIDEO,
      file: null,
      tags: String(field(request, "tags") || "mock").split(",").map((tag) => tag.trim()).filter(Boolean),
    };
  }
  if (resource === "music") {
    return {
      _id: id,
      title: String(field(request, "title") || "Mock New Track"),
      artist: String(field(request, "artist") || "Mock New Artist"),
      url: String(field(request, "music_url_input") || ADMIN_VIDEO),
      image: ADMIN_IMAGE,
      duration: "3:00",
      lyrics: String(field(request, "lyrics") || ""),
      category: String(field(request, "category") || "Pop"),
    };
  }
  if (resource === "keyProjects") {
    return {
      _id: id,
      title: parseLocalized(jsonField(request, "title"), localized("Mock New Project")),
      description: parseLocalized(jsonField(request, "description"), localized("New project description")),
      stack: parseLocalized(jsonField(request, "stack"), localized("Flask")),
      status: String(field(request, "status") || "planned"),
      image_url: ADMIN_IMAGE,
      demo_url: String(field(request, "demo_url") || ""),
      repo_url: String(field(request, "repo_url") || ""),
      sort_order: Number(field(request, "sort_order") || 0),
      slides: arrayField(request, "slides_meta", []).map((slide, index) => ({
        id: slide.id || `pw-admin-slide-new-${index}`,
        image_url: slide.existing_image_url || ADMIN_IMAGE,
        title: localized(slide.title || `Slide ${index + 1}`),
        description: localized(slide.description || `Slide description ${index + 1}`),
      })),
      is_active: boolField(request, "is_active", true),
    };
  }
  if (resource === "roadmaps") {
    return {
      _id: id,
      company_name: String(field(request, "company_name") || "Mock Company"),
      role_title: String(field(request, "role_title") || "Mock Role"),
      period: String(field(request, "period") || "2026"),
      employment_type: String(field(request, "employment_type") || "Full-time"),
      location: String(field(request, "location") || "Remote"),
      definition: String(field(request, "definition") || ""),
      summary: String(field(request, "summary") || ""),
      highlights: String(field(request, "highlights") || ""),
      cover_image_url: ADMIN_IMAGE,
      activities: arrayField(request, "activities_meta", []).map((activity, index) => ({
        id: activity.id || `pw-admin-roadmap-activity-new-${index}`,
        image_url: activity.existing_image_url || ADMIN_IMAGE,
        title: localized(activity.title || `Activity ${index + 1}`),
        caption: localized(activity.caption || `Activity caption ${index + 1}`),
      })),
      accent_color: String(field(request, "accent_color") || "#0d6efd"),
      sort_order: Number(field(request, "sort_order") || 0),
      is_active: boolField(request, "is_active", true),
    };
  }
  if (resource === "builtApps") {
    const name = parseLocalized(jsonField(request, "name"), localized("Mock New App"));
    return {
      _id: id,
      slug: String(field(request, "slug") || slugify(name.en)),
      platform: String(field(request, "platform") || "Mobile"),
      version: String(field(request, "version") || "1.0.0"),
      icon: String(field(request, "icon") || "bi-app"),
      icon_image_url: ADMIN_IMAGE,
      name,
      short_description: parseLocalized(jsonField(request, "short_description"), localized("New app description")),
      full_description: parseLocalized(jsonField(request, "full_description"), { en: [], ceb: [], fr: [], fil_PH: [] }),
      snapshots: (arrayField(request, "snapshots_meta", []).length
        ? arrayField(request, "snapshots_meta", [])
        : Array.from(
            { length: (request.postData() || "").split('name="snapshot_files"').length - 1 },
            (_, index) => ({ id: `pw-admin-snapshot-new-${index}` })
          )
      ).map((snapshot, index) => ({
        id: snapshot.id || `pw-admin-snapshot-new-${index}`,
        image_url: ADMIN_IMAGE,
        sort_order: index,
      })),
      technologies: arrayField(request, "technologies", []),
      download_url: String(field(request, "download_url") || ""),
      sort_order: Number(field(request, "sort_order") || 0),
      is_active: boolField(request, "is_active", true),
    };
  }
  return null;
}

function updateRecord(record, resource, request) {
  if (resource === "gallery") {
    record.title = parseLocalized(jsonField(request, "title"), record.title);
    record.description = parseLocalized(jsonField(request, "description"), record.description);
    record.tags = String(field(request, "tags") || record.tags.join(",")).split(",").map((tag) => tag.trim()).filter(Boolean);
  } else if (resource === "video") {
    record.title = parseLocalized(jsonField(request, "title"), record.title);
    record.description = parseLocalized(jsonField(request, "description"), record.description);
    record.tags = String(field(request, "tags") || record.tags.join(",")).split(",").map((tag) => tag.trim()).filter(Boolean);
  } else if (resource === "music") {
    record.title = String(field(request, "title") || record.title);
    record.artist = String(field(request, "artist") || record.artist);
    record.category = String(field(request, "category") || record.category);
    record.lyrics = String(field(request, "lyrics") || record.lyrics);
    record.url = String(field(request, "music_url_input") || record.url);
  } else if (resource === "keyProjects") {
    record.title = parseLocalized(jsonField(request, "title"), record.title);
    record.description = parseLocalized(jsonField(request, "description"), record.description);
    record.stack = parseLocalized(jsonField(request, "stack"), record.stack);
    record.status = String(field(request, "status") || record.status);
    record.demo_url = String(field(request, "demo_url") || record.demo_url);
    record.repo_url = String(field(request, "repo_url") || record.repo_url);
    record.sort_order = Number(field(request, "sort_order") || record.sort_order);
    record.slides = arrayField(request, "slides_meta", []).map((slide, index) => ({
      id: slide.id || `pw-admin-slide-${index}`,
      image_url: slide.existing_image_url || ADMIN_IMAGE,
      title: localized(slide.title || `Slide ${index + 1}`),
      description: localized(slide.description || `Slide description ${index + 1}`),
    }));
    record.is_active = boolField(request, "is_active", record.is_active);
  } else if (resource === "roadmaps") {
    record.company_name = String(field(request, "company_name") || record.company_name);
    record.role_title = String(field(request, "role_title") || record.role_title);
    record.period = String(field(request, "period") || record.period);
    record.employment_type = String(field(request, "employment_type") || record.employment_type);
    record.location = String(field(request, "location") || record.location);
    record.definition = String(field(request, "definition") || record.definition);
    record.summary = String(field(request, "summary") || record.summary);
    record.highlights = String(field(request, "highlights") || record.highlights);
    record.accent_color = String(field(request, "accent_color") || record.accent_color);
    record.sort_order = Number(field(request, "sort_order") || record.sort_order);
    record.activities = arrayField(request, "activities_meta", []).map((activity, index) => ({
      id: activity.id || `pw-admin-roadmap-activity-${index}`,
      image_url: activity.existing_image_url || ADMIN_IMAGE,
      title: localized(activity.title || `Activity ${index + 1}`),
      caption: localized(activity.caption || `Activity caption ${index + 1}`),
    }));
    record.is_active = boolField(request, "is_active", record.is_active);
  } else if (resource === "builtApps") {
    record.slug = String(field(request, "slug") || record.slug);
    record.platform = String(field(request, "platform") || record.platform);
    record.version = String(field(request, "version") || record.version);
    record.icon = String(field(request, "icon") || record.icon);
    record.name = parseLocalized(jsonField(request, "name"), record.name);
    record.short_description = parseLocalized(jsonField(request, "short_description"), record.short_description);
    record.full_description = parseLocalized(jsonField(request, "full_description"), record.full_description);
    record.download_url = String(field(request, "download_url") || record.download_url);
    record.sort_order = Number(field(request, "sort_order") || record.sort_order);
    record.is_active = boolField(request, "is_active", record.is_active);
    record.snapshots = arrayField(request, "snapshots_meta", []).map((snapshot, index) => ({
      id: snapshot.id || `pw-admin-snapshot-${index}`,
      image_url: ADMIN_IMAGE,
      sort_order: index,
    }));
    record.technologies = arrayField(request, "technologies", record.technologies);
  }
}

const DELETE_MESSAGES = {
  gallery: "Gallery deleted successfully",
  video: "Video deleted successfully",
  music: "Music deleted successfully",
  keyProjects: "Key project deleted successfully",
  roadmaps: "Company roadmap deleted successfully",
  builtApps: "Built app deleted successfully",
  loginAttempts: "Login Attempt deleted successfully",
  bookings: "Booking request deleted successfully",
};

export function handleAdminRequest(route, state, url) {
  const request = route.request();
  const method = request.method();

  if (!url.pathname.startsWith("/admin/api/")) return null;
  if (url.pathname.startsWith("/admin/api/otp/")) return null;

  state.requests.push({
    method,
    path: url.pathname,
    search: url.search,
  });

  if (url.pathname === "/admin/api/face/register" && method === "POST") {
    if (state.face.failRegister) {
      return jsonResponse(route, { ok: false, message: "No face detected." }, 400);
    }
    state.face.registered += 1;
    return jsonResponse(route, { ok: true, message: "Face registered successfully." });
  }

  if (url.pathname === "/admin/api/face/records" && method === "GET") {
    return jsonResponse(route, {
      ok: true,
      has_face: state.face.registered > 0,
      records: state.face.registered > 0 ? [{ id: "mock-face" }] : [],
    });
  }

  if (url.pathname === "/admin/api/face/verify" && method === "POST") {
    if (state.face.failVerify) {
      return jsonResponse(route, { ok: false, message: "Face did not match." }, 400);
    }
    state.face.verified += 1;
    return route.continue({ url: `${url.origin}/__playwright/face-verify` });
  }

  if (url.pathname === "/admin/api/dashboard-summary") {
    return jsonResponse(route, {
      visitor_total_count: 128,
      bot_total_count: 12,
      total_music: state.music.length,
      total_gallery: state.gallery.length,
      total_video: state.video.length,
      total_projects: state.keyProjects.length,
      total_roadmaps: state.roadmaps.length,
      device_breakdown: [
        { label: "Windows", count: 52 },
        { label: "iOS", count: 34 },
        { label: "Android", count: 21 },
        { label: "macOS", count: 13 },
        { label: "Linux", count: 6 },
        { label: "Other", count: 2 },
      ],
    });
  }

  if (url.pathname === "/admin/api/get-client-ip") {
    return jsonResponse(route, { ip: ADMIN_IP });
  }

  if (url.pathname === "/admin/api/visits/info") {
    return jsonResponse(route, {
      data: null,
      visitor_total_count: state.visits.length,
      bot_total_count: 0,
      total_count: state.visits.length,
    });
  }

  if (url.pathname === "/admin/api/recent-activity" && method === "GET") {
    const params = paginationParams(url);
    const paramsCamel = {
      ...params,
      perPage: url.searchParams.get("perPage") || params.perPage,
    };
    const filtered = matches(state.activity, params.search, ["user_id", "method", "path", "status_code"]);
    const page = paginate(sortItems(filtered, params.order), paramsCamel.page, paramsCamel.perPage);
    return jsonResponse(route, {
      data: page.items,
      total: page.total,
      page: page.page,
      per_page: page.perPage,
    });
  }

  if (url.pathname === "/admin/api/visits-list" && method === "GET") {
    const params = paginationParams(url);
    const filtered = matches(state.visits, params.search, [
      "system",
      "device",
      "browser",
      "os",
      "page",
      "site",
      "ip_address",
      "city",
      "country",
    ]);
    const page = paginate(sortItems(filtered, params.order), params.page, params.perPage);
    return jsonResponse(route, {
      data: page.items,
      total: page.total,
      page: page.page,
      per_page: page.perPage,
    });
  }

  if (url.pathname === "/admin/api/delete-activity" && method === "DELETE") {
    const body = parseJsonBody(request);
    const ids = Array.isArray(body.record_ids) ? body.record_ids.map(String) : [];
    state.activity = state.activity.filter((item) => !ids.includes(String(item._id)));
    return jsonResponse(route, { ok: true, message: "Activity selected records deleted successfully." });
  }

  if (url.pathname === "/admin/api/clear-all-activity" && method === "DELETE") {
    state.activity = [];
    return jsonResponse(route, { ok: true, message: "All recent activity cleared successfully." });
  }

  if (url.pathname === "/admin/api/clear-all-visitors" && method === "DELETE") {
    state.visits = [];
    return jsonResponse(route, { ok: true, message: "All visitor records cleared successfully." });
  }

  if (url.pathname.startsWith("/admin/api/delete-visits/") && method === "DELETE") {
    const id = url.pathname.split("/").pop();
    state.visits = state.visits.filter((item) => String(item._id) !== id);
    return jsonResponse(route, { ok: true, message: "Visitor record deleted." });
  }

  if (url.pathname === "/admin/api/update-profile" && method === "POST") {
    const username = String(field(request, "username") || state.profile.username);
    state.profile.username = username;
    return jsonResponse(route, {
      message: "Profile updated successfully!",
      username,
      profile_image: state.profile.profileImage,
    });
  }

  if (url.pathname === "/admin/api/music-categories" && method === "GET") {
    return jsonResponse(route, ["All", "Rap", "Love Song", "Pop", "R&B", "Rock", "Chill", "Party", "Workout", "Mood", "Focus"]);
  }

  const resource = resourceEndpoint(url.pathname);
  if (resource && method === "GET") {
    const params = paginationParams(url);
    let items = recordsFor(state, resource);

    if (resource === "gallery" || resource === "video") {
      items = matches(items, params.search, ["title", "description", "tags"]);
      return jsonResponse(route, listResponse(route, items, params, resource));
    }

    if (resource === "music") {
      items = matches(items, params.search, ["title", "artist", "category", "lyrics"]);
      return jsonResponse(route, listResponse(route, items, params, "music"));
    }

    if (resource === "keyProjects") {
      items = matches(items, params.search, ["title", "description", "stack", "status"]);
      const statusFilter = url.searchParams.get("status") || "";
      const activeFilter = url.searchParams.get("is_active") || "";
      if (statusFilter) items = items.filter((item) => item.status === statusFilter);
      if (activeFilter) items = items.filter((item) => String(item.is_active) === activeFilter);
      const page = paginate(sortItems(items, params.order, "sort_order"), params.page, params.perPage);
      return jsonResponse(route, {
        projects: page.items,
        total_projects: page.total,
        total_pages: page.totalPages,
        page: page.page,
        per_page: page.perPage,
      });
    }

    if (resource === "roadmaps") {
      items = matches(items, params.search, ["company_name", "role_title", "period", "summary"]);
      const employment = url.searchParams.get("employment_type") || "";
      const activeFilter = url.searchParams.get("is_active") || "";
      if (employment) items = items.filter((item) => item.employment_type === employment);
      if (activeFilter) items = items.filter((item) => String(item.is_active) === activeFilter);
      const page = paginate(sortItems(items, params.order, "sort_order"), params.page, params.perPage);
      return jsonResponse(route, {
        roadmaps: page.items,
        total_roadmaps: page.total,
        total_pages: page.totalPages,
        page: page.page,
        per_page: page.perPage,
      });
    }

    if (resource === "builtApps") {
      items = matches(items, params.search, ["name", "slug", "version"]);
      const platform = url.searchParams.get("platform") || "";
      const activeFilter = url.searchParams.get("is_active") || "";
      if (platform) items = items.filter((item) => item.platform === platform);
      if (activeFilter) items = items.filter((item) => String(item.is_active) === activeFilter);
      const page = paginate(sortItems(items, params.order, "sort_order"), params.page, params.perPage);
      return jsonResponse(route, {
        apps: page.items,
        total_apps: page.total,
        total_pages: page.totalPages,
        page: page.page,
        per_page: page.perPage,
      });
    }

    if (resource === "loginAttempts") {
      items = matches(items, params.search, ["_id", "device", "attempts"]);
      const page = paginate(sortItems(items, params.order), params.page, params.perPage);
      return jsonResponse(route, {
        login_attempt: page.items,
        total_login_attempt: page.total,
        total_pages: page.totalPages,
        page: page.page,
        per_page: page.perPage,
      });
    }

    if (resource === "bookings") {
      items = matches(items, params.search, ["name", "email", "message"]);
      const page = paginate(sortItems(items, params.order), params.page, params.perPage);
      return jsonResponse(route, {
        booking_requests: page.items,
        total: page.total,
        total_pages: page.totalPages,
        page: page.page,
        per_page: page.perPage,
      });
    }
  }

  const addMatch = url.pathname.match(/^\/admin\/api\/add-(gallery|video|music|key-project|company-roadmap|built-app)$/);
  if (addMatch && method === "POST") {
    const map = {
      gallery: "gallery",
      video: "video",
      music: "music",
      "key-project": "keyProjects",
      "company-roadmap": "roadmaps",
      "built-app": "builtApps",
    };
    const resourceKey = map[addMatch[1]];
    const record = createRecord(state, resourceKey, request);
    state[resourceKey].push(record);
    addActivity(state, "POST", url.pathname);
    return jsonResponse(route, {
      message: `${resourceKey === "keyProjects" ? "Key project" : resourceKey === "roadmaps" ? "Company roadmap" : resourceKey === "builtApps" ? "Built app" : resourceKey} added successfully`,
      id: record._id,
    }, 201);
  }

  const updateMatch = url.pathname.match(/^\/admin\/api\/update-(gallery|video|music|key-project|company-roadmap|built-app)\/([^/]+)$/);
  if (updateMatch && method === "PUT") {
    const map = {
      gallery: "gallery",
      video: "video",
      music: "music",
      "key-project": "keyProjects",
      "company-roadmap": "roadmaps",
      "built-app": "builtApps",
    };
    const resourceKey = map[updateMatch[1]];
    const id = decodeURIComponent(updateMatch[2]);
    const record = state[resourceKey].find((item) => String(item._id) === id);
    if (!record) {
      return jsonResponse(route, { message: "Record not found" }, 404);
    }
    updateRecord(record, resourceKey, request);
    addActivity(state, "PUT", url.pathname);
    return jsonResponse(route, {
      message: `${resourceKey === "keyProjects" ? "Key project" : resourceKey === "roadmaps" ? "Company roadmap" : resourceKey === "builtApps" ? "Built app" : resourceKey} updated successfully`,
      id: record._id,
    });
  }

  const deleteMatch = url.pathname.match(/^\/admin\/api\/delete-(gallery|video|music|key-project|company-roadmap|built-app|login-attempt|booking-request)\/([^/]+)$/);
  if (deleteMatch && method === "DELETE") {
    const map = {
      gallery: "gallery",
      video: "video",
      music: "music",
      "key-project": "keyProjects",
      "company-roadmap": "roadmaps",
      "built-app": "builtApps",
      "login-attempt": "loginAttempts",
      "booking-request": "bookings",
    };
    const resourceKey = map[deleteMatch[1]];
    const id = decodeURIComponent(deleteMatch[2]);
    state[resourceKey] = state[resourceKey].filter((item) => String(item._id) !== id);
    addActivity(state, "DELETE", url.pathname);
    return jsonResponse(route, { ok: true, message: DELETE_MESSAGES[resourceKey] });
  }

  if (url.pathname === "/admin/api/clear-all-booking-requests" && method === "DELETE") {
    state.bookings = [];
    return jsonResponse(route, { ok: true, message: "All booking requests cleared successfully." });
  }

  return jsonResponse(route, {});
}

export function adminAssetResponse(route, url, resourceType) {
  if (resourceType === "script") {
    if (url.pathname.includes("jquery")) {
      return route.fulfill({ status: 200, contentType: "text/javascript", body: JQUERY_STUB });
    }
    if (url.pathname.includes("bootstrap")) {
      return route.fulfill({ status: 200, contentType: "text/javascript", body: BOOTSTRAP_STUB });
    }
    if (url.pathname.toLowerCase().includes("adminlte")) {
      return route.fulfill({ status: 200, contentType: "text/javascript", body: ADMINLTE_STUB });
    }
  }

  if (resourceType === "stylesheet" && url.pathname.includes("bootstrap")) {
    return route.fulfill({ status: 200, contentType: "text/css", body: BOOTSTRAP_CSS });
  }

  return null;
}
