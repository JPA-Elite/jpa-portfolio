const PLACEHOLDER_IMAGE = Buffer.from(
  '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="#d9d9d9"/></svg>'
);

const ION_ICON_STUB = `
if (!customElements.get("ion-icon")) {
  class IonIconElement extends HTMLElement {
    connectedCallback() {
      this.style.display = "inline-block";
      this.style.width = "1em";
      this.style.height = "1em";
    }
  }
  customElements.define("ion-icon", IonIconElement);
}
`;

const LOCAL_HOSTS = new Set([
  "professional.jpastack.local",
  "jpastack.local",
  "admin.jpastack.local",
  "localhost",
  "127.0.0.1",
  "[::1]",
]);

function addBaseUrlHost(hosts, baseURL) {
  if (!baseURL) {
    return;
  }

  try {
    hosts.add(new URL(baseURL).hostname);
  } catch {
    return;
  }
}

function jsonResponse(route, payload) {
  return route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify(payload),
  });
}

function applyVote(state, isLike) {
  if (state.vote === isLike) {
    state.vote = null;
    if (isLike) {
      state.likes -= 1;
    } else {
      state.dislikes -= 1;
    }
    return;
  }

  if (state.vote === true) {
    state.likes -= 1;
  }

  if (state.vote === false) {
    state.dislikes -= 1;
  }

  state.vote = isLike;

  if (isLike) {
    state.likes += 1;
  } else {
    state.dislikes += 1;
  }
}

async function handleRoute(route, state, localHosts) {
  const request = route.request();
  const url = new URL(request.url());
  const resourceType = request.resourceType();

  if (url.pathname === "/api/built-app-like/counts") {
    return jsonResponse(route, {
      like_counts: state.likes,
      dislike_counts: state.dislikes,
      user_vote: state.vote,
    });
  }

  if (url.pathname === "/api/built-app-like/vote" && request.method() === "POST") {
    const body = request.postDataJSON();
    applyVote(state, Boolean(body.is_like));

    return jsonResponse(route, {
      message: "Vote updated",
      data: { action: "updated", is_like: state.vote },
    });
  }

  if (url.pathname.startsWith("/api/")) {
    return jsonResponse(route, {});
  }

  if (localHosts.has(url.hostname)) {
    return route.continue();
  }

  if (resourceType === "image") {
    return route.fulfill({
      status: 200,
      contentType: "image/svg+xml",
      body: PLACEHOLDER_IMAGE,
    });
  }

  if (resourceType === "document") {
    return route.fulfill({
      status: 200,
      contentType: "text/html",
      body: "<!doctype html><html><body></body></html>",
    });
  }

  if (resourceType === "script") {
    return route.fulfill({
      status: 200,
      contentType: "text/javascript",
      body: url.hostname === "unpkg.com" ? ION_ICON_STUB : "",
    });
  }

  if (resourceType === "stylesheet") {
    return route.fulfill({
      status: 200,
      contentType: "text/css",
      body: "",
    });
  }

  return route.fulfill({ status: 204 });
}

export async function installMockSite(context, options = {}) {
  const state = {
    likes: options.likeCount ?? 12,
    dislikes: options.dislikeCount ?? 3,
    vote: options.userVote ?? null,
  };
  const localHosts = new Set(LOCAL_HOSTS);
  addBaseUrlHost(localHosts, options.baseURL);

  await context.route("**/*", (route) => handleRoute(route, state, localHosts));

  return state;
}
