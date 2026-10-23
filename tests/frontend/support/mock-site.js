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

const DEFAULT_AVATAR = "/static/images/user.webp";
const DEFAULT_UPLOADED_AVATAR = "/static/images/avatars/avatar_orange.svg";
const DEFAULT_PROFILE_AVATAR = "/static/images/avatars/avatar_pink.svg";
const MOCK_IP = "mock-playwright-ip";

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

function jsonResponse(route, payload, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    headers: { "cache-control": "no-store" },
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

function parseJsonBody(request) {
  try {
    return request.postDataJSON() || {};
  } catch {
    return {};
  }
}

function readMultipartField(request, field) {
  const body = request.postData() || "";
  const match = body.match(
    new RegExp(`name="${field}"\\r?\\n\\r?\\n([\\s\\S]*?)\\r?\\n--`, "i")
  );
  if (!match) {
    return null;
  }

  const raw = match[1].replace(/\r$/, "");
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

function ensureContent(state, kind, id) {
  if (!id) {
    return null;
  }

  const content = state.content[kind];
  if (!content[id]) {
    content[id] = {
      likeCount: 12,
      liked: false,
      comments: null,
    };
  }

  return content[id];
}

function ensureComments(state, kind, id) {
  const content = ensureContent(state, kind, id);
  if (!content) {
    return [];
  }

  if (content.comments) {
    return content.comments;
  }

  const now = Date.now();
  content.comments = [
    {
      _id: `${kind}-${id}-own-2`,
      author_name: state.profile.displayName,
      text: `Second own ${kind} comment`,
      created_at: new Date(now - 60_000).toISOString(),
      liked_ips: [],
      is_own: true,
      avatar_url: state.profile.avatarUrl,
    },
    {
      _id: `${kind}-${id}-other-1`,
      author_name: "Mock Neighbor",
      text: `A neighbor ${kind} comment`,
      created_at: new Date(now - 120_000).toISOString(),
      liked_ips: [],
      is_own: false,
      avatar_url: null,
    },
    {
      _id: `${kind}-${id}-own-1`,
      author_name: state.profile.displayName,
      text: `First own ${kind} comment`,
      created_at: new Date(now - 180_000).toISOString(),
      liked_ips: [],
      is_own: true,
      avatar_url: state.profile.avatarUrl,
    },
  ];

  return content.comments;
}

function commentsResponse(state, comments, page, limit) {
  const visibleComments = comments.map((comment) => ({
    ...comment,
    author_name: comment.is_own
      ? state.profile.displayName
      : comment.author_name,
    avatar_url: comment.is_own
      ? state.profile.avatarUrl
      : comment.avatar_url,
    is_liked: comment.liked_ips.includes(MOCK_IP),
  }));

  return {
    comments: visibleComments,
    total: comments.length,
    page,
    limit,
    display_name: state.profile.displayName,
    avatar_url: state.profile.avatarUrl,
    remaining_changes: state.profile.remainingNameChanges,
  };
}

function findCommentBucket(state, commentId) {
  for (const kind of ["gallery", "vlog"]) {
    for (const contentId of Object.keys(state.content[kind])) {
      const comments = ensureComments(state, kind, contentId);
      if (comments.some((comment) => comment._id === commentId)) {
        return { kind, contentId, comments };
      }
    }
  }

  return null;
}

function handleContentLike(state, route, kind, url) {
  const idParam = `${kind}_id`;
  const listParam = `${kind}_ids`;
  const basePath = `/api/${kind}-like`;

  if (url.pathname === `${basePath}/counts/batch`) {
    const ids = (url.searchParams.get(listParam) || "")
      .split(",")
      .map((id) => id.trim())
      .filter(Boolean);
    const items = {};

    for (const id of ids) {
      const content = ensureContent(state, kind, id);
      ensureComments(state, kind, id);
      items[id] = {
        like_counts: content.likeCount,
        comment_counts: content.comments.length,
        is_liked: content.liked,
      };
    }

    return jsonResponse(route, { items });
  }

  if (url.pathname === `${basePath}/counts`) {
    const id = url.searchParams.get(idParam);
    const content = ensureContent(state, kind, id);
    if (!content) {
      return jsonResponse(route, { error: "Missing content id" }, 400);
    }
    ensureComments(state, kind, id);

    return jsonResponse(route, {
      like_counts: content.likeCount,
      comment_counts: content.comments.length,
      is_liked: content.liked,
    });
  }

  if (url.pathname === basePath && route.request().method() === "POST") {
    const id = readMultipartField(route.request(), idParam);
    const content = ensureContent(state, kind, id);
    if (!content) {
      return jsonResponse(route, { error: "Missing content id" }, 400);
    }

    content.liked = !content.liked;
    content.likeCount = Math.max(
      0,
      content.likeCount + (content.liked ? 1 : -1)
    );

    return jsonResponse(route, {
      message: "Like updated",
      data: { like: content.liked },
    });
  }

  return null;
}

function handleComments(state, route, kind, url) {
  const idParam = `${kind}_id`;
  const basePath = `/api/${kind}-comments`;
  const request = route.request();
  const action = url.pathname.startsWith(`${basePath}/`)
    ? url.pathname.slice(basePath.length + 1)
    : "";

  if (!url.pathname.startsWith(basePath)) {
    return null;
  }

  if (!action && request.method() === "GET") {
    const contentId = url.searchParams.get(idParam);
    const comments = ensureComments(state, kind, contentId);
    const page = Number(url.searchParams.get("page") || "1");
    const limit = Number(url.searchParams.get("limit") || "100");

    return jsonResponse(
      route,
      commentsResponse(state, comments, page, limit)
    );
  }

  if (!action && request.method() === "POST") {
    const body = parseJsonBody(request);
    const contentId = body[idParam];
    const comments = ensureComments(state, kind, contentId);
    const text = String(body.text || "");
    const commentId = `mock-comment-${state.commentSequence++}`;

    comments.unshift({
      _id: commentId,
      author_name: state.profile.displayName || body.author_name || "You",
      text,
      created_at: new Date().toISOString(),
      liked_ips: [],
      is_own: true,
      avatar_url: state.profile.avatarUrl,
    });

    return jsonResponse(route, { status: "success", comment_id: commentId });
  }

  if (action === "like" && request.method() === "POST") {
    const body = parseJsonBody(request);
    const bucket = findCommentBucket(state, body.comment_id);
    if (!bucket) {
      return jsonResponse(route, { status: "error", message: "Comment not found" }, 404);
    }

    const comment = bucket.comments.find(
      (item) => item._id === body.comment_id
    );
    const likedIndex = comment.liked_ips.indexOf(MOCK_IP);
    if (likedIndex >= 0) {
      comment.liked_ips.splice(likedIndex, 1);
    } else {
      comment.liked_ips.push(MOCK_IP);
    }

    return jsonResponse(route, {
      status: "success",
      liked: likedIndex < 0,
      like_count: comment.liked_ips.length,
    });
  }

  if (action === "delete-all" && request.method() === "DELETE") {
    const body = parseJsonBody(request);
    const contentId = body[idParam];
    const comments = ensureComments(state, kind, contentId);
    const before = comments.length;
    const remaining = comments.filter((comment) => !comment.is_own);
    const content = ensureContent(state, kind, contentId);
    content.comments = remaining;

    return jsonResponse(route, {
      status: "success",
      deleted: before - remaining.length,
      message: "All your comments were deleted.",
    });
  }

  if (action && request.method() === "DELETE") {
    const bucket = findCommentBucket(state, action);
    if (!bucket) {
      return jsonResponse(route, { status: "error", message: "Comment not found" }, 404);
    }

    bucket.comments.splice(
      bucket.comments.findIndex((comment) => comment._id === action),
      1
    );

    return jsonResponse(route, {
      status: "success",
      message: "Comment deleted successfully.",
    });
  }

  return null;
}

function handleProfile(state, route, url) {
  const request = route.request();

  if (url.pathname === "/api/comment-avatar/upload" && request.method() === "POST") {
    state.profile.avatarUrl = state.profile.uploadedAvatarUrl;
    state.profile.remainingAvatarChanges = Math.max(
      0,
      state.profile.remainingAvatarChanges - 1
    );

    return jsonResponse(route, {
      status: "success",
      avatar_url: state.profile.avatarUrl,
      remaining_avatar_changes: state.profile.remainingAvatarChanges,
    });
  }

  if (url.pathname === "/api/comment-avatar") {
    if (request.method() === "GET") {
      return jsonResponse(route, {
        avatar_url: state.profile.avatarUrl,
        remaining_avatar_changes: state.profile.remainingAvatarChanges,
      });
    }

    if (request.method() === "POST") {
      const body = parseJsonBody(request);
      state.profile.avatarUrl = body.avatar_url || DEFAULT_AVATAR;
      state.profile.remainingAvatarChanges = Math.max(
        0,
        state.profile.remainingAvatarChanges - 1
      );

      return jsonResponse(route, {
        status: "success",
        avatar_url: state.profile.avatarUrl,
        remaining_avatar_changes: state.profile.remainingAvatarChanges,
      });
    }

    if (request.method() === "DELETE") {
      state.profile.avatarUrl = null;
      state.profile.remainingAvatarChanges = Math.max(
        0,
        state.profile.remainingAvatarChanges - 1
      );

      return jsonResponse(route, {
        status: "success",
        avatar_url: state.profile.avatarUrl,
        remaining_avatar_changes: state.profile.remainingAvatarChanges,
      });
    }
  }

  if (url.pathname === "/api/comment-username") {
    if (request.method() === "GET") {
      return jsonResponse(route, {
        display_name: state.profile.displayName,
        remaining_changes: state.profile.remainingNameChanges,
      });
    }

    if (request.method() === "POST") {
      const body = parseJsonBody(request);
      state.profile.displayName = String(body.display_name || "").trim();
      state.profile.remainingNameChanges = Math.max(
        0,
        state.profile.remainingNameChanges - 1
      );

      return jsonResponse(route, {
        status: "success",
        display_name: state.profile.displayName,
        remaining_changes: state.profile.remainingNameChanges,
      });
    }
  }

  return null;
}

async function handleRoute(route, state, localHosts) {
  const request = route.request();
  const url = new URL(request.url());
  const resourceType = request.resourceType();

  if (url.pathname === "/api/built-app-like/counts") {
    return jsonResponse(route, {
      like_counts: state.builtApp.likes,
      dislike_counts: state.builtApp.dislikes,
      user_vote: state.builtApp.vote,
    });
  }

  if (url.pathname === "/api/built-app-like/vote" && request.method() === "POST") {
    const body = request.postDataJSON();
    applyVote(state.builtApp, Boolean(body.is_like));

    return jsonResponse(route, {
      message: "Vote updated",
      data: { action: "updated", is_like: state.builtApp.vote },
    });
  }

  const galleryLike = handleContentLike(state, route, "gallery", url);
  if (galleryLike) {
    return galleryLike;
  }

  const vlogLike = handleContentLike(state, route, "vlog", url);
  if (vlogLike) {
    return vlogLike;
  }

  const galleryComments = handleComments(state, route, "gallery", url);
  if (galleryComments) {
    return galleryComments;
  }

  const vlogComments = handleComments(state, route, "vlog", url);
  if (vlogComments) {
    return vlogComments;
  }

  const profile = handleProfile(state, route, url);
  if (profile) {
    return profile;
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
    builtApp: {
      likes: options.likeCount ?? 12,
      dislikes: options.dislikeCount ?? 3,
      vote: options.userVote ?? null,
    },
    content: {
      gallery: {},
      vlog: {},
    },
    profile: {
      displayName: options.displayName ?? "Mock Visitor",
      avatarUrl: options.avatarUrl ?? DEFAULT_PROFILE_AVATAR,
      remainingNameChanges: options.remainingNameChanges ?? 20,
      remainingAvatarChanges: options.remainingAvatarChanges ?? 20,
      uploadedAvatarUrl:
        options.uploadedAvatarUrl ?? DEFAULT_UPLOADED_AVATAR,
    },
    commentSequence: 1,
  };
  const localHosts = new Set(LOCAL_HOSTS);
  addBaseUrlHost(localHosts, options.baseURL);

  await context.route("**/*", (route) => handleRoute(route, state, localHosts));

  return state;
}
