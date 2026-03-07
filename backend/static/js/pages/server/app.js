const bootState = window.serverCommunityState || {};

const REACTION_EMOJIS = [
    "\u{1F44D}", "\u{1F44E}", "\u2764\uFE0F", "\u{1F525}", "\u{1F44F}", "\u2705",
    "\u{1F389}", "\u{1F602}", "\u{1F60D}", "\u{1F914}", "\u{1F64F}", "\u{1F680}",
    "\u{1F4A1}", "\u{1F3AF}", "\u{1F91D}", "\u{1F622}", "\u{1F973}", "\u{1F44C}",
    "\u{1F31F}", "\u{1F4AF}", "\u{1F60E}", "\u{1F64C}", "\u{1F62E}", "\u{1F621}",
];
const DEFAULT_AVATAR = "/static/admin/assets/img/admin.png";
const CHAT_PAGE_SIZE = 50;
const THREAD_PAGE_SIZE = 50;
const FILES_PAGE_SIZE = 50;
const ACTIVITIES_PAGE_SIZE = 12;
const NOTIFICATIONS_PAGE_SIZE = 30;
const SERVER_THEME_KEY = "server.theme";

const state = {
    currentUser: bootState.currentUser || null,
    channels: Array.isArray(bootState.channels) ? bootState.channels : [],
    activeChannelId: bootState.activeChannelId || "",
    viewMode: "messages",
    searchQuery: "",
    activeFetchToken: 0,
    activeThreadFetchToken: 0,
    messages: [],
    searchResults: [],
    chatPage: 1,
    chatTotalPages: 1,
    chatTotalItems: 0,
    threadMessages: [],
    threadRootMessage: null,
    threadPage: 1,
    threadTotalPages: 1,
    threadTotalItems: 0,
    notifications: [],
    notificationsPage: 1,
    notificationsTotalPages: 1,
    notificationsTotalItems: 0,
    activities: [],
    activitiesPage: 1,
    activitiesTotalPages: 1,
    activitiesTotalItems: 0,
    pendingDeleteMessageId: "",
    pendingDeleteChannelId: "",
    pendingRenameChannelId: "",
    pendingEditMessageId: "",
    threadRootId: "",
    reactionTargetMessageId: "",
    scrollToBottomNext: false,
    threadScrollToBottomNext: false,
    files: [],
    filesPage: 1,
    filesTotalPages: 1,
    filesTotalItems: 0,
    fileCount: 0,
    fileLimit: null,
    editingFileId: "",
    activitiesFilter: "all",
    rightPanelMode: "thread",
    profilePanelUser: null,
};

const channelListEl = document.getElementById("serverChannelList");
const titleEl = document.getElementById("activeChannelTitle");
const descriptionEl = document.getElementById("activeChannelDescription");
const channelMemberSummaryEl = document.getElementById("channelMemberSummary");
const messagesEl = document.getElementById("serverMessages");
const messagesPaginationEl = document.getElementById("serverMessagesPagination");
const messageForm = document.getElementById("serverMessageForm");
const messageInput = document.getElementById("serverMessageInput");
const messageSendBtn = document.getElementById("serverMessageSendBtn");
const createChannelForm = document.getElementById("createChannelForm");
const createChannelModal = document.getElementById("createChannelModal");
const renameChannelForm = document.getElementById("renameChannelForm");
const renameChannelModal = document.getElementById("renameChannelModal");
const renameChannelIdInput = document.getElementById("renameChannelId");
const renameChannelNameInput = document.getElementById("renameChannelName");
const renameChannelDescriptionInput = document.getElementById("renameChannelDescription");
const deleteChannelModal = document.getElementById("deleteChannelModal");
const confirmDeleteChannelBtn = document.getElementById("confirmDeleteChannelBtn");
const deleteMessageModal = document.getElementById("deleteMessageModal");
const confirmDeleteMessageBtn = document.getElementById("confirmDeleteMessageBtn");
const editMessageModal = document.getElementById("editMessageModal");
const editMessageForm = document.getElementById("editMessageForm");
const editMessageInput = document.getElementById("editMessageInput");
const chatBodyEl = document.querySelector(".server-chat-body");
const threadPanelEl = document.getElementById("serverThreadPanel");
const threadListEl = document.getElementById("serverThreadList");
const threadPaginationEl = document.getElementById("serverThreadPagination");
const threadParentMetaEl = document.getElementById("threadParentMeta");
const threadForm = document.getElementById("serverThreadForm");
const threadInput = document.getElementById("serverThreadInput");
const threadSendBtn = document.getElementById("serverThreadSendBtn");
const closeThreadPanelBtn = document.getElementById("closeThreadPanel");
const notificationsModal = document.getElementById("notificationsModal");
const notificationsModalBody = document.getElementById("notificationsModalBody");
const notificationsModalPaginationEl = document.getElementById("notificationsModalPagination");
const searchModal = document.getElementById("searchModal");
const searchForm = document.getElementById("searchForm");
const searchInput = document.getElementById("searchInput");
const searchResultMeta = document.getElementById("searchResultMeta");
const searchResultsEl = document.getElementById("searchResults");
const clearSearchBtn = document.getElementById("clearSearchBtn");
const messagesTabBtn = document.getElementById("messagesTabBtn");
const filesTabBtn = document.getElementById("filesTabBtn");
const pinsTabBtn = document.getElementById("pinsTabBtn");
const reactionPickerModal = document.getElementById("reactionPickerModal");
const reactionPickerGrid = document.getElementById("reactionPickerGrid");
const activitiesListEl = document.getElementById("serverActivitiesList");
const activitiesPaginationEl = document.getElementById("serverActivitiesPagination");
const activityFiltersEl = document.getElementById("serverActivityFilters");
const refreshActivitiesBtn = document.getElementById("refreshActivitiesBtn");
const themeToggleBtn = document.getElementById("serverThemeToggleBtn");
const themeToggleIcon = document.getElementById("serverThemeToggleIcon");
const profileMetaStatusEl = document.querySelector(".server-profile-meta small");
const threadPanelTitleEl = document.getElementById("serverThreadPanelTitle");
const fileLimitMetaEl = document.getElementById("activeChannelFileLimit");
const fileForm = document.getElementById("serverFileForm");
const fileInput = document.getElementById("serverFileInput");
const fileNameInput = document.getElementById("serverFileNameInput");
const fileUploadBtn = document.getElementById("serverFileUploadBtn");
const fileEditCancelBtn = document.getElementById("serverFileEditCancelBtn");
const fileLimitHintEl = document.getElementById("serverFileLimitHint");

const deleteModalInstance = deleteMessageModal ? new window.bootstrap.Modal(deleteMessageModal) : null;
const editModalInstance = editMessageModal ? new window.bootstrap.Modal(editMessageModal) : null;
const reactionModalInstance = reactionPickerModal ? new window.bootstrap.Modal(reactionPickerModal) : null;
const renameChannelModalInstance = renameChannelModal ? new window.bootstrap.Modal(renameChannelModal) : null;
const deleteChannelModalInstance = deleteChannelModal ? new window.bootstrap.Modal(deleteChannelModal) : null;
const createChannelModalInstance = createChannelModal ? new window.bootstrap.Modal(createChannelModal) : null;

function resetFileEditMode() {
    state.editingFileId = "";
    if (fileNameInput) fileNameInput.value = "";
    if (fileInput) fileInput.value = "";
    if (fileUploadBtn) {
        fileUploadBtn.innerHTML = '<i class="bi bi-upload"></i> Upload';
    }
    fileEditCancelBtn?.classList.add("d-none");
    renderActiveChannelDetails();
}

function setFileEditMode(fileRow) {
    state.editingFileId = String(fileRow?.id || "").trim();
    if (!state.editingFileId) return;
    if (fileNameInput) {
        fileNameInput.value = String(fileRow?.name || fileRow?.original_filename || "");
        fileNameInput.focus();
    }
    if (fileInput) fileInput.value = "";
    if (fileUploadBtn) {
        fileUploadBtn.innerHTML = '<i class="bi bi-pencil-square"></i> Save Update';
    }
    fileEditCancelBtn?.classList.remove("d-none");
    if (fileLimitHintEl) {
        fileLimitHintEl.textContent = "Editing file: update title and optionally choose a replacement file.";
    }
}

function updateChannelUrl(channelId) {
    if (!channelId) return;
    try {
        const url = new URL(window.location.href);
        url.searchParams.set("channel_id", channelId);
        window.history.replaceState({}, "", url.toString());
    } catch (error) {
        console.error(error);
    }
}

function normalizeThemeName(value) {
    return String(value || "").toLowerCase() === "light" ? "light" : "dark";
}

function applyTheme(themeName) {
    const resolvedTheme = normalizeThemeName(themeName);
    document.body.setAttribute("data-server-theme", resolvedTheme);
    localStorage.setItem(SERVER_THEME_KEY, resolvedTheme);

    if (!themeToggleBtn || !themeToggleIcon) return;
    themeToggleIcon.classList.remove("bi-moon-stars-fill", "bi-sun-fill");
    if (resolvedTheme === "dark") {
        themeToggleIcon.classList.add("bi-sun-fill");
        themeToggleBtn.setAttribute("title", "Switch to light theme");
    } else {
        themeToggleIcon.classList.add("bi-moon-stars-fill");
        themeToggleBtn.setAttribute("title", "Switch to dark theme");
    }
}

function toggleTheme() {
    const currentTheme = normalizeThemeName(document.body.getAttribute("data-server-theme"));
    applyTheme(currentTheme === "dark" ? "light" : "dark");
}

function getInitialTheme() {
    return normalizeThemeName(localStorage.getItem(SERVER_THEME_KEY) || "dark");
}

function renderModeTabs() {
    [messagesTabBtn, filesTabBtn, pinsTabBtn].forEach((button) => {
        if (!button) return;
        const mode = String(button.getAttribute("data-view-mode") || "messages");
        button.classList.toggle("is-active", mode === state.viewMode);
    });
    messageForm?.classList.toggle("d-none", state.viewMode === "files");
    fileForm?.classList.toggle("d-none", state.viewMode !== "files");
}

function setButtonLoading(button, isLoading, loadingLabel = "Processing...") {
    if (!button) return;
    if (isLoading) {
        if (!button.dataset.originalHtml) {
            button.dataset.originalHtml = button.innerHTML;
        }
        button.disabled = true;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            ${escapeHtml(loadingLabel)}
        `;
        return;
    }

    button.disabled = false;
    if (button.dataset.originalHtml) {
        button.innerHTML = button.dataset.originalHtml;
    }
}

function wrapSelection(textarea, prefix, suffix = prefix) {
    if (!textarea) return;
    const value = textarea.value;
    const start = textarea.selectionStart ?? 0;
    const end = textarea.selectionEnd ?? 0;
    const selected = value.slice(start, end);
    const nextValue = value.slice(0, start) + prefix + selected + suffix + value.slice(end);
    textarea.value = nextValue;
    const cursorStart = start + prefix.length;
    const cursorEnd = cursorStart + selected.length;
    textarea.setSelectionRange(cursorStart, cursorEnd);
    textarea.focus();
}

function addListPrefix(textarea) {
    if (!textarea) return;
    const value = textarea.value;
    const start = textarea.selectionStart ?? 0;
    const end = textarea.selectionEnd ?? 0;
    const lineStart = value.lastIndexOf("\n", start - 1) + 1;
    const lineEnd = value.indexOf("\n", end);
    const safeEnd = lineEnd === -1 ? value.length : lineEnd;
    const block = value.slice(lineStart, safeEnd);
    const lines = block.split("\n").map((line) => (line.startsWith("- ") ? line : `- ${line}`));
    const nextValue = value.slice(0, lineStart) + lines.join("\n") + value.slice(safeEnd);
    textarea.value = nextValue;
    textarea.setSelectionRange(lineStart, lineStart + lines.join("\n").length);
    textarea.focus();
}

function escapeHtml(value = "") {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function formatMessageText(value = "") {
    const safe = escapeHtml(value);
    const withCode = safe.replace(/`([^`]+)`/g, "<code>$1</code>");
    const withBold = withCode.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    const withItalic = withBold.replace(/_([^_]+)_/g, "<em>$1</em>");
    const withMentions = withItalic.replace(/(^|[\s(])@([a-zA-Z0-9._-]{2,32})/g, "$1<span class=\"server-mention\">@$2</span>");
    const withLines = withMentions.split(/\n/).map((line) => line.replace(/&nbsp;/g, " ").trimEnd());
    const listItems = [];
    const htmlChunks = [];
    const flushList = () => {
        if (!listItems.length) return;
        htmlChunks.push(`<ul class="server-chat-list">${listItems.join("")}</ul>`);
        listItems.length = 0;
    };

    withLines.forEach((line) => {
        const trimmed = line.trim();
        const listMatch = trimmed.match(/^[-*]\s+(.*)$/);
        if (listMatch) {
            const content = listMatch[1].trim();
            listItems.push(`<li>${content || "&nbsp;"}</li>`);
        } else {
            flushList();
            htmlChunks.push(line);
        }
    });
    flushList();
    return htmlChunks.join("<br>");
}

function formatDate(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
}

function formatDateLabel(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    return date.toLocaleDateString(undefined, {
        weekday: "long",
        month: "long",
        day: "numeric",
    });
}

function getDateKey(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    return date.toDateString();
}

function getActiveChannel() {
    return state.channels.find((channel) => channel.id === state.activeChannelId) || null;
}

function getMessageById(messageId) {
    const safeMessageId = String(messageId || "");
    if (!safeMessageId) return null;
    return (
        state.messages.find((item) => String(item.id) === safeMessageId)
        || state.threadMessages.find((item) => String(item.id) === safeMessageId)
        || (state.threadRootMessage && String(state.threadRootMessage.id) === safeMessageId ? state.threadRootMessage : null)
    );
}

async function apiRequest(url, options = {}) {
    const response = await fetch(url, options);
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(payload.message || "Request failed");
    }
    return payload;
}

function renderChannels() {
    if (!channelListEl) return;
    channelListEl.innerHTML = "";

    if (!state.channels.length) {
        channelListEl.innerHTML = `<li class="text-muted small">No channels available</li>`;
        return;
    }

    state.channels.forEach((channel) => {
        const item = document.createElement("li");
        const isActive = channel.id === state.activeChannelId;
        const canManage = Boolean(channel.can_manage);
        const memberCount = Number(channel.member_count || 0);
        item.innerHTML = `
            <div class="server-channel-row">
                <button class="server-channel-item ${isActive ? "active" : ""}" data-channel-id="${escapeHtml(channel.id)}">
                    <span class="server-channel-item-main"># ${escapeHtml(channel.name || "channel")}</span>
                    <span class="server-channel-item-meta">
                        <i class="bi bi-people"></i>
                        <span class="server-channel-member-count">${memberCount}</span>
                    </span>
                </button>
                ${canManage ? `
                    <div class="server-channel-row-actions">
                        <button class="server-icon-btn" type="button" data-action="rename-channel" data-channel-id="${escapeHtml(channel.id)}" title="Rename channel">
                            <i class="bi bi-pencil-square"></i>
                        </button>
                        <button class="server-icon-btn server-icon-btn-danger" type="button" data-action="delete-channel" data-channel-id="${escapeHtml(channel.id)}" title="Delete channel">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                ` : ""}
            </div>
        `;

        // Sidebar channel rows should only show member count (no file quota indicators).
        item.querySelectorAll(".bi-paperclip, .server-channel-file-meta, .server-channel-file-count").forEach((el) => el.remove());
        channelListEl.appendChild(item);
    });
}

function renderActiveChannelDetails() {
    const channel = getActiveChannel();
    if (!channel) {
        titleEl.textContent = "# channel";
        descriptionEl.textContent = "Select a channel to start chatting.";
        if (fileLimitMetaEl) {
            fileLimitMetaEl.textContent = "";
        }
        if (messageInput) {
            messageInput.placeholder = "Type your message...";
        }
        if (fileLimitHintEl) {
            fileLimitHintEl.textContent = "File limit info unavailable.";
        }
        if (channelMemberSummaryEl) {
            channelMemberSummaryEl.innerHTML = "";
        }
        return;
    }

    titleEl.textContent = `# ${channel.name || "channel"}`;
    descriptionEl.textContent = channel.description || "No channel description.";
    if (fileLimitMetaEl) {
        const count = Number(channel.file_count || 0);
        const limit = channel.file_limit;
        fileLimitMetaEl.textContent = limit
            ? `Files: ${count}/${limit} (1MB max per file for members)`
            : `Files: ${count} (admin unlimited)`;
    }
    if (fileLimitHintEl) {
        const limitText = channel.file_limit
            ? `Limit: ${channel.file_count || 0}/${channel.file_limit} files in this channel. Max 1MB per file.`
            : "Admin account: no file count or size limit.";
        fileLimitHintEl.textContent = limitText;
    }
    if (messageInput) {
        messageInput.placeholder = `Message #${channel.name || "channel"}`;
    }

    if (!channelMemberSummaryEl) return;
    const members = Array.isArray(channel.member_preview) ? channel.member_preview.slice(0, 5) : [];
    const memberCount = Number(channel.member_count || members.length);
    const extraCount = Math.max(0, memberCount - members.length);
    channelMemberSummaryEl.innerHTML = `
        <span class="server-member-count">${memberCount} member${memberCount === 1 ? "" : "s"}</span>
        <div class="server-member-stack">
            ${members.map((member) => `
                <button type="button" class="server-member-avatar-wrap server-message-avatar-btn" title="${escapeHtml(member.username || "member")}" data-action="open-profile" data-user-id="${escapeHtml(member.id || "")}">
                    <img class="server-member-avatar" src="${escapeHtml(member.profile_image || DEFAULT_AVATAR)}" alt="${escapeHtml(member.username || "member")}">
                    <span class="server-member-status ${member.is_online ? "is-online" : "is-away"}"></span>
                </button>
            `).join("")}
            ${extraCount > 0 ? `<span class="server-member-more">+${extraCount}</span>` : ""}
        </div>
    `;

    if (profileMetaStatusEl && state.currentUser) {
        const activeMember = members.find((member) => String(member.id || "") === String(state.currentUser.id || ""));
        if (activeMember) {
            const role = String(state.currentUser.account_type || "member");
            profileMetaStatusEl.textContent = `${role.charAt(0).toUpperCase()}${role.slice(1)} - ${activeMember.is_online ? "Online" : "Away"}`;
        }
    }
}

function buildMessageTree(rows) {
    const byId = Object.create(null);
    const repliesByParentId = Object.create(null);
    const rootMessages = [];

    rows.forEach((item) => {
        byId[item.id] = item;
    });

    rows.forEach((item) => {
        const parentId = String(item.parent_message_id || "").trim();
        if (!parentId || !byId[parentId]) {
            rootMessages.push(item);
            return;
        }

        if (!Array.isArray(repliesByParentId[parentId])) {
            repliesByParentId[parentId] = [];
        }
        repliesByParentId[parentId].push(item);
    });

    return { byId, repliesByParentId, rootMessages };
}

function renderReactionButtons(message) {
    const reactions = message.reactions || {};
    const reactionSummary = Object.entries(reactions)
        .filter(([, meta]) => Number(meta?.count || 0) > 0)
        .map(([emoji, meta]) => `
            <button
                type="button"
                class="server-reaction-chip ${meta?.reacted ? "active" : ""}"
                data-action="react"
                data-message-id="${escapeHtml(message.id)}"
                data-emoji="${escapeHtml(emoji)}"
            >${escapeHtml(emoji)} <span>${Number(meta?.count || 0)}</span></button>
        `)
        .join("");

    return `
        <div class="server-message-reactions">
            ${reactionSummary}
        </div>
    `;
}

function renderDateDivider(label) {
    return `
        <div class="server-date-divider">
            <span>${escapeHtml(label || "")}</span>
        </div>
    `;
}

function renderMessageCard(message, depth, tree) {
    if (!message || !message.id) {
        return "";
    }
    const isMine = String(message.user_id || "") === String(state.currentUser?.id || "");
    const isMentioned = Boolean(message.mentioned_me);
    const parent = tree.byId[message.parent_message_id];
    const replyLabel = depth > 0 && parent
        ? `<div class="server-reply-meta">Replying to @${escapeHtml(parent.username || "member")}</div>`
        : "";

    const pinLabel = message.is_pinned ? "Unpin" : "Pin";
    const actions = message.is_deleted
        ? ""
        : `
            <div class="server-message-actions">
                <button type="button" class="server-action-btn" data-action="open-reaction-modal" data-message-id="${escapeHtml(message.id)}">+</button>
                <button type="button" class="server-action-btn" data-action="reply" data-message-id="${escapeHtml(message.id)}">Reply</button>
                ${message.editable ? `<button type="button" class="server-action-btn" data-action="edit" data-message-id="${escapeHtml(message.id)}">Edit</button>` : ""}
                ${message.deletable ? `<button type="button" class="server-action-btn danger" data-action="delete" data-message-id="${escapeHtml(message.id)}">Delete</button>` : ""}
                <button type="button" class="server-action-btn" data-action="pin" data-message-id="${escapeHtml(message.id)}">${pinLabel}</button>
            </div>
        `;

    const body = `
        <div class="server-message-text ${message.is_deleted ? "is-deleted" : ""}">
            ${formatMessageText(message.text || "")}
        </div>
        ${message.edited_at && !message.is_deleted ? `<div class="server-edited-label">Edited ${escapeHtml(formatDate(message.edited_at))}</div>` : ""}
        ${renderReactionButtons(message)}
    `;

    const replyCount = Number(message.reply_count || 0);
    const threadSummaryMarkup = replyCount > 0
        ? `
            <button type="button" class="server-thread-summary" data-action="reply" data-message-id="${escapeHtml(message.id)}">
                ${replyCount} ${replyCount === 1 ? "reply" : "replies"}
            </button>
            <span class="server-thread-summary-meta">Last reply ${escapeHtml(formatDate(message.last_reply_at || ""))}</span>
        `
        : "";

    return `
        <article class="server-message ${isMine ? "is-mine" : ""} ${depth > 0 ? "is-thread-reply" : ""} ${isMentioned ? "is-mentioned" : ""}" data-message-card-id="${escapeHtml(message.id)}">
            <div class="server-message-layout">
                <button type="button" class="server-message-avatar-btn" data-action="open-profile" data-user-id="${escapeHtml(message.user_id || "")}">
                    <img class="server-message-avatar" src="${escapeHtml(message.profile_image || DEFAULT_AVATAR)}" alt="${escapeHtml(message.username || "member")}">
                </button>
                <div class="server-message-content">
                    <div class="server-message-meta">
                        <strong>${escapeHtml(message.username || "member")}</strong>
                        <span>${escapeHtml(formatDate(message.created_at))}</span>
                        ${message.is_pinned ? '<span class="server-pin-badge"><i class="bi bi-pin-angle-fill"></i> Pinned</span>' : ""}
                    </div>
                    ${replyLabel}
                    ${body}
                    <div class="server-thread-summary-row">${threadSummaryMarkup}</div>
                    ${actions}
                </div>
            </div>
        </article>
    `;
}

async function openThreadPanel(messageId) {
    const message = getMessageById(messageId);
    if (message && message.is_deleted) return;
    state.threadRootId = String(message?.parent_message_id || message?.id || messageId || "");
    if (!state.threadRootId) return;
    state.rightPanelMode = "thread";
    state.profilePanelUser = null;
    state.threadPage = 1;
    state.threadScrollToBottomNext = false;
    chatBodyEl?.classList.add("is-thread-open");
    if (threadPanelEl) {
        threadPanelEl.classList.remove("is-empty");
        threadPanelEl.classList.add("is-open");
        threadPanelEl.classList.remove("is-profile");
    }
    if (threadPanelTitleEl) {
        threadPanelTitleEl.textContent = "Thread";
    }
    if (threadForm) {
        threadForm.classList.remove("d-none");
    }
    if (threadPaginationEl) {
        threadPaginationEl.classList.remove("d-none");
    }
    await fetchThreadMessages();
}

function closeThreadPanel() {
    state.rightPanelMode = "thread";
    state.profilePanelUser = null;
    state.threadRootId = "";
    state.threadMessages = [];
    state.threadRootMessage = null;
    state.threadPage = 1;
    state.threadTotalPages = 1;
    state.threadTotalItems = 0;
    chatBodyEl?.classList.remove("is-thread-open");
    if (threadPanelEl) {
        threadPanelEl.classList.add("is-empty");
        threadPanelEl.classList.remove("is-open");
        threadPanelEl.classList.remove("is-profile");
    }
    if (threadPanelTitleEl) {
        threadPanelTitleEl.textContent = "Thread";
    }
    if (threadForm) {
        threadForm.classList.remove("d-none");
    }
    if (threadPaginationEl) {
        threadPaginationEl.classList.remove("d-none");
    }
    if (threadParentMetaEl) {
        threadParentMetaEl.textContent = "Select a message to view the thread.";
    }
    if (threadListEl) {
        threadListEl.innerHTML = "";
    }
    if (threadPaginationEl) {
        threadPaginationEl.innerHTML = "";
    }
}

async function openProfilePanel(userId) {
    const targetUserId = String(userId || "").trim();
    if (!targetUserId || !state.activeChannelId) return;

    const payload = await apiRequest(`/api/server/users/${encodeURIComponent(targetUserId)}?channel_id=${encodeURIComponent(state.activeChannelId)}`);
    state.profilePanelUser = payload.user || null;
    state.rightPanelMode = "profile";
    chatBodyEl?.classList.add("is-thread-open");
    if (threadPanelEl) {
        threadPanelEl.classList.remove("is-empty");
        threadPanelEl.classList.add("is-open");
        threadPanelEl.classList.add("is-profile");
    }
    if (threadPanelTitleEl) {
        threadPanelTitleEl.textContent = "Profile";
    }
    if (threadForm) {
        threadForm.classList.add("d-none");
    }
    if (threadPaginationEl) {
        threadPaginationEl.classList.add("d-none");
    }
    renderProfilePanel();
}

function renderProfilePanel() {
    if (!threadListEl || !threadParentMetaEl) return;
    const user = state.profilePanelUser;
    if (!user) {
        threadListEl.innerHTML = '<div class="server-empty-state">Profile unavailable.</div>';
        threadParentMetaEl.textContent = "No profile details available.";
        return;
    }

    const onlineLabel = user.is_online ? "Online" : "Away";
    threadParentMetaEl.textContent = `@${user.username || "member"} profile`;
    threadListEl.innerHTML = `
        <article class="server-profile-panel-card">
            <div class="server-profile-panel-head">
                <img src="${escapeHtml(user.profile_image || DEFAULT_AVATAR)}" alt="${escapeHtml(user.username || "member")}">
                <div class="server-profile-panel-meta">
                    <strong>${escapeHtml(user.name || user.username || "Member")}</strong>
                    <small>@${escapeHtml(user.username || "member")} - ${escapeHtml(onlineLabel)}</small>
                </div>
            </div>
            <div class="server-profile-panel-grid">
                <div><strong>Role:</strong> ${escapeHtml(user.account_type || "member")}</div>
                <div><strong>Email:</strong> ${escapeHtml(user.email || "-")}</div>
                <div><strong>Location:</strong> ${escapeHtml(user.place || "-")}</div>
                <div><strong>Gender:</strong> ${escapeHtml(user.gender || "-")}</div>
                <div><strong>Birthdate:</strong> ${escapeHtml(user.birthdate || "-")}</div>
                <div>${escapeHtml(user.bio || "")}</div>
            </div>
        </article>
    `;
}

async function fetchThreadMessages() {
    if (state.rightPanelMode !== "thread") {
        return;
    }
    if (!state.activeChannelId || !state.threadRootId) {
        renderThreadPanel();
        return;
    }

    const fetchToken = ++state.activeThreadFetchToken;
    const params = new URLSearchParams({
        channel_id: String(state.activeChannelId),
        parent_message_id: String(state.threadRootId),
        page: String(state.threadPage),
        per_page: String(THREAD_PAGE_SIZE),
    });
    if (state.searchQuery) {
        params.set("search", state.searchQuery);
    }

    const payload = await apiRequest(`/api/server/messages?${params.toString()}`);
    if (fetchToken !== state.activeThreadFetchToken) {
        return;
    }
    state.threadRootMessage = payload.thread_root || null;
    state.threadMessages = payload.messages || [];
    state.threadPage = Number(payload.pagination?.page || state.threadPage || 1);
    state.threadTotalPages = Number(payload.pagination?.total_pages || 1);
    state.threadTotalItems = Number(payload.pagination?.total_items || state.threadMessages.length);
    if (!state.threadRootMessage) {
        closeThreadPanel();
        return;
    }
    renderThreadPanel();
}

function renderThreadPanel() {
    if (!threadListEl || !threadParentMetaEl) return;
    if (state.rightPanelMode !== "thread") {
        renderProfilePanel();
        return;
    }
    if (!state.threadRootId) {
        threadListEl.innerHTML = "";
        threadParentMetaEl.textContent = "Select a message to view the thread.";
        if (threadPaginationEl) threadPaginationEl.innerHTML = "";
        return;
    }

    const rootMessage = state.threadRootMessage || getMessageById(state.threadRootId);
    if (!rootMessage) {
        closeThreadPanel();
        return;
    }

    const replies = state.threadMessages || [];

    threadParentMetaEl.textContent = `${state.threadTotalItems} ${state.threadTotalItems === 1 ? "reply" : "replies"} with @${rootMessage.username || "member"}`;
    const rootMarkup = renderThreadItem(rootMessage, true);
    const repliesMarkup = replies.length
        ? replies.map((message) => renderThreadItem(message, false)).join("")
        : "<div class=\"server-empty-state\">No replies yet.</div>";

    threadListEl.innerHTML = `${rootMarkup}${repliesMarkup}`;
    if (state.threadScrollToBottomNext) {
        threadListEl.scrollTop = threadListEl.scrollHeight;
        state.threadScrollToBottomNext = false;
    } else {
        threadListEl.scrollTop = 0;
    }
    renderPagination(
        threadPaginationEl,
        state.threadPage,
        state.threadTotalPages,
        state.threadTotalItems,
        "thread-page-prev",
        "thread-page-next",
    );
}

function renderThreadItem(message, isRoot) {
    if (!message) return "";
    const isMine = String(message.user_id || "") === String(state.currentUser?.id || "");
    const pinLabel = message.is_pinned ? "Unpin" : "Pin";

    const actions = message.is_deleted
        ? ""
        : `
            <div class="server-message-actions">
                <button type="button" class="server-action-btn" data-action="open-reaction-modal" data-message-id="${escapeHtml(message.id)}">+</button>
                ${isRoot ? "" : `<button type="button" class="server-action-btn" data-action="reply" data-message-id="${escapeHtml(message.id)}">Reply</button>`}
                ${message.editable ? `<button type="button" class="server-action-btn" data-action="edit" data-message-id="${escapeHtml(message.id)}">Edit</button>` : ""}
                ${message.deletable ? `<button type="button" class="server-action-btn danger" data-action="delete" data-message-id="${escapeHtml(message.id)}">Delete</button>` : ""}
                <button type="button" class="server-action-btn" data-action="pin" data-message-id="${escapeHtml(message.id)}">${pinLabel}</button>
            </div>
        `;

    const body = `
        <div class="server-message-text ${message.is_deleted ? "is-deleted" : ""}">
            ${formatMessageText(message.text || "")}
        </div>
        ${message.edited_at && !message.is_deleted ? `<div class="server-edited-label">Edited ${escapeHtml(formatDate(message.edited_at))}</div>` : ""}
        ${renderReactionButtons(message)}
    `;

    return `
        <article class="server-message server-thread-item ${isRoot ? "is-thread-root" : "is-thread-reply"} ${isMine ? "is-mine" : ""}" data-message-card-id="${escapeHtml(message.id)}">
            <div class="server-message-layout">
                <button type="button" class="server-message-avatar-btn" data-action="open-profile" data-user-id="${escapeHtml(message.user_id || "")}">
                    <img class="server-message-avatar" src="${escapeHtml(message.profile_image || DEFAULT_AVATAR)}" alt="${escapeHtml(message.username || "member")}">
                </button>
                <div class="server-message-content">
                    <div class="server-message-meta">
                        <strong>${escapeHtml(message.username || "member")}</strong>
                        <span>${escapeHtml(formatDate(message.created_at))}</span>
                        ${message.is_pinned ? '<span class="server-pin-badge"><i class="bi bi-pin-angle-fill"></i> Pinned</span>' : ""}
                    </div>
                    ${body}
                    ${actions}
                </div>
            </div>
        </article>
    `;
}

function renderPagination(container, page, totalPages, totalItems, prevAction, nextAction) {
    if (!container) return;
    const safePage = Math.max(1, Number(page || 1));
    const safeTotalPages = Math.max(1, Number(totalPages || 1));
    const safeTotalItems = Math.max(0, Number(totalItems || 0));
    if (safeTotalItems <= 0 || safeTotalPages <= 1) {
        container.innerHTML = "";
        return;
    }
    container.innerHTML = `
        <div class="server-pagination-inner">
            <button type="button" class="server-page-btn" data-action="${prevAction}" ${safePage <= 1 ? "disabled" : ""}>Prev</button>
            <span>Page ${safePage} of ${safeTotalPages} - ${safeTotalItems} items</span>
            <button type="button" class="server-page-btn" data-action="${nextAction}" ${safePage >= safeTotalPages ? "disabled" : ""}>Next</button>
        </div>
    `;
}

function renderMessages(rows = []) {
    if (!messagesEl) return;
    state.messages = rows;

    if (!rows.length) {
        const emptyMessage = state.searchQuery
            ? "No messages found for this search."
            : "No messages yet. Start the conversation.";
        messagesEl.innerHTML = `<div class="server-empty-state">${escapeHtml(emptyMessage)}</div>`;
        renderPagination(
            messagesPaginationEl,
            state.chatPage,
            state.chatTotalPages,
            state.chatTotalItems,
            "chat-page-prev",
            "chat-page-next",
        );
        renderThreadPanel();
        return;
    }

    const tree = buildMessageTree(rows);
    const output = [];
    let lastDateKey = "";
    tree.rootMessages.forEach((message) => {
        const currentDateKey = getDateKey(message.created_at);
        if (currentDateKey && currentDateKey !== lastDateKey) {
            output.push(renderDateDivider(formatDateLabel(message.created_at)));
            lastDateKey = currentDateKey;
        }
        output.push(renderMessageCard(message, 0, tree));
    });

    messagesEl.innerHTML = output.join("");
    if (state.scrollToBottomNext) {
        messagesEl.scrollTop = messagesEl.scrollHeight;
        state.scrollToBottomNext = false;
    } else {
        messagesEl.scrollTop = 0;
    }
    renderPagination(
        messagesPaginationEl,
        state.chatPage,
        state.chatTotalPages,
        state.chatTotalItems,
        "chat-page-prev",
        "chat-page-next",
    );
    renderThreadPanel();
}

function renderMessagesLoading() {
    if (!messagesEl) return;
    messagesEl.innerHTML = `
        <div class="server-loading">
            <div class="server-loading-spinner"></div>
            <span>Loading messages...</span>
        </div>
    `;
}

function renderMessagesError(message) {
    if (!messagesEl) return;
    messagesEl.innerHTML = `<div class="server-empty-state">${escapeHtml(message || "Failed to load messages.")}</div>`;
}

async function fetchChannels() {
    const payload = await apiRequest("/api/server/channels");

    state.channels = payload.channels || [];
    if (!state.activeChannelId && state.channels.length) {
        state.activeChannelId = state.channels[0].id;
    }
    if (state.activeChannelId && !state.channels.some((x) => x.id === state.activeChannelId)) {
        state.activeChannelId = state.channels.length ? state.channels[0].id : "";
    }
    renderChannels();
    renderActiveChannelDetails();
    updateChannelUrl(state.activeChannelId);
}

async function fetchMessages() {
    if (state.viewMode === "files") {
        await fetchFiles();
        return;
    }
    const channelId = state.activeChannelId;
    if (!channelId) {
        renderMessages([]);
        return;
    }

    const fetchToken = ++state.activeFetchToken;
    renderMessagesLoading();

    try {
        const params = new URLSearchParams({
            channel_id: String(channelId),
            page: String(state.chatPage),
            per_page: String(CHAT_PAGE_SIZE),
        });
        if (state.searchQuery) {
            params.set("search", state.searchQuery);
        }
        if (state.viewMode === "pins") {
            params.set("pinned_only", "1");
        }

        const payload = await apiRequest(`/api/server/messages?${params.toString()}`);
        if (fetchToken !== state.activeFetchToken) return;

        const messages = payload.messages || [];
        state.chatPage = Number(payload.pagination?.page || state.chatPage || 1);
        state.chatTotalPages = Number(payload.pagination?.total_pages || 1);
        state.chatTotalItems = Number(payload.pagination?.total_items || messages.length);
        renderMessages(messages);
        if (state.threadRootId) {
            await fetchThreadMessages();
        }
    } catch (error) {
        if (fetchToken !== state.activeFetchToken) return;
        renderMessagesError(error.message);
        throw error;
    }
}

async function sendMessage() {
    if (state.viewMode === "files") return;
    const text = String(messageInput?.value || "").trim();
    if (!text || !state.activeChannelId) return;

    setButtonLoading(messageSendBtn, true, "Sending...");
    try {
        await apiRequest("/api/server/messages", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                channel_id: state.activeChannelId,
                text,
            }),
        });
        messageInput.value = "";
        state.chatPage = 1;
        state.scrollToBottomNext = true;
        await fetchMessages();
        await fetchActivities();
    } finally {
        setButtonLoading(messageSendBtn, false);
    }
}

async function sendThreadReply() {
    const text = String(threadInput?.value || "").trim();
    if (!text || !state.activeChannelId || !state.threadRootId) return;

    setButtonLoading(threadSendBtn, true, "Replying...");
    try {
        await apiRequest("/api/server/messages", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                channel_id: state.activeChannelId,
                text,
                parent_message_id: state.threadRootId,
            }),
        });
        threadInput.value = "";
        state.chatPage = 1;
        state.threadPage = 1;
        state.scrollToBottomNext = true;
        state.threadScrollToBottomNext = true;
        await fetchMessages();
        if (state.threadRootId) {
            await fetchThreadMessages();
        }
        await fetchActivities();
    } finally {
        setButtonLoading(threadSendBtn, false);
    }
}

async function createChannel(event) {
    event.preventDefault();
    if (!createChannelForm) return;

    const formData = new FormData(createChannelForm);
    const submitButton = createChannelForm.querySelector("button[type='submit']");
    setButtonLoading(submitButton, true, "Creating...");
    try {
        const payload = await apiRequest("/api/server/channels", {
            method: "POST",
            body: JSON.stringify({
                name: formData.get("name"),
                description: formData.get("description"),
                channel_type: formData.get("channel_type"),
                is_public: createChannelForm.querySelector("[name='is_public']").checked,
            }),
            headers: {
                "Content-Type": "application/json",
            },
        });

        createChannelForm.reset();
        const publicCheckbox = createChannelForm.querySelector("[name='is_public']");
        if (publicCheckbox) {
            publicCheckbox.checked = true;
        }
        createChannelModalInstance?.hide();
        state.activeChannelId = payload.channel?.id || state.activeChannelId;
        state.chatPage = 1;
        await fetchChannels();
        await fetchMessages();
        await fetchActivities();
    } finally {
        setButtonLoading(submitButton, false);
    }
}

async function updateMessageInline(messageId, text) {
    await apiRequest(`/api/server/messages/${encodeURIComponent(messageId)}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
    });
}

async function deleteMessage(messageId) {
    await apiRequest(`/api/server/messages/${encodeURIComponent(messageId)}`, {
        method: "DELETE",
    });
}

async function reactToMessage(messageId, emoji) {
    await apiRequest("/api/server/messages/react", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            message_id: messageId,
            emoji,
        }),
    });
}

async function togglePinMessage(messageId) {
    await apiRequest("/api/server/messages/pin", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            message_id: messageId,
        }),
    });
}

async function updateChannel(channelId, payload) {
    await apiRequest(`/api/server/channels/${encodeURIComponent(channelId)}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });
}

async function deleteChannel(channelId) {
    await apiRequest(`/api/server/channels/${encodeURIComponent(channelId)}`, {
        method: "DELETE",
    });
}

function formatFileSize(bytes) {
    const value = Number(bytes || 0);
    if (value <= 0) return "0 B";
    if (value < 1024) return `${value} B`;
    if (value < (1024 * 1024)) return `${(value / 1024).toFixed(1)} KB`;
    return `${(value / (1024 * 1024)).toFixed(2)} MB`;
}

function renderFiles(rows = []) {
    if (!messagesEl) return;
    state.messages = [];
    if (!rows.length) {
        messagesEl.innerHTML = '<div class="server-empty-state">No files uploaded yet.</div>';
        renderPagination(
            messagesPaginationEl,
            state.filesPage,
            state.filesTotalPages,
            state.filesTotalItems,
            "files-page-prev",
            "files-page-next",
        );
        return;
    }

    messagesEl.innerHTML = rows.map((item) => `
        <article class="server-file-card" data-file-card-id="${escapeHtml(item.id || "")}">
            <div class="server-file-card-head">
                <div>
                    <h5 class="server-file-card-title">${escapeHtml(item.name || item.original_filename || "file")}</h5>
                    <p class="server-file-card-meta">
                        Uploaded by ${escapeHtml(item.uploaded_by_username || "member")} - ${escapeHtml(formatDate(item.created_at))} - ${escapeHtml(formatFileSize(item.file_size))}
                    </p>
                </div>
            </div>
            <div class="server-file-card-actions">
                <a class="server-action-btn" href="${escapeHtml(item.file_url || "#")}" target="_blank" rel="noopener noreferrer">Open</a>
                <a class="server-action-btn" href="${escapeHtml(item.file_url || "#")}" download="${escapeHtml(item.original_filename || "file")}">Download</a>
                ${item.editable ? `<button type="button" class="server-action-btn" data-action="edit-file" data-file-id="${escapeHtml(item.id)}">Update</button>` : ""}
                ${item.deletable ? `<button type="button" class="server-action-btn danger" data-action="delete-file" data-file-id="${escapeHtml(item.id)}">Delete</button>` : ""}
            </div>
        </article>
    `).join("");

    renderPagination(
        messagesPaginationEl,
        state.filesPage,
        state.filesTotalPages,
        state.filesTotalItems,
        "files-page-prev",
        "files-page-next",
    );
}

async function fetchFiles() {
    const channelId = state.activeChannelId;
    if (!channelId) {
        renderFiles([]);
        return;
    }
    if (!messagesEl) return;
    messagesEl.innerHTML = `
        <div class="server-loading">
            <div class="server-loading-spinner"></div>
            <span>Loading files...</span>
        </div>
    `;

    const params = new URLSearchParams({
        channel_id: String(channelId),
        page: String(state.filesPage),
        per_page: String(FILES_PAGE_SIZE),
    });
    const payload = await apiRequest(`/api/server/files?${params.toString()}`);
    state.files = payload.files || [];
    state.filesPage = Number(payload.pagination?.page || state.filesPage || 1);
    state.filesTotalPages = Number(payload.pagination?.total_pages || 1);
    state.filesTotalItems = Number(payload.pagination?.total_items || state.files.length);
    state.fileCount = Number(payload.file_count || state.filesTotalItems || 0);
    state.fileLimit = payload.file_limit === null || payload.file_limit === undefined
        ? null
        : Number(payload.file_limit || 0);

    if (state.editingFileId && !state.files.some((item) => String(item.id) === String(state.editingFileId))) {
        resetFileEditMode();
    }

    const channelIndex = state.channels.findIndex((item) => String(item.id) === String(channelId));
    if (channelIndex >= 0) {
        state.channels[channelIndex].file_count = state.fileCount;
        state.channels[channelIndex].file_limit = state.fileLimit;
        renderChannels();
        renderActiveChannelDetails();
    }
    renderFiles(state.files);
}

async function uploadFile() {
    const channelId = String(state.activeChannelId || "");
    if (!channelId) return;
    const selectedFile = fileInput?.files?.[0] || null;
    const displayName = String(fileNameInput?.value || "").trim();

    if (!state.editingFileId && !selectedFile) {
        throw new Error("Please choose a file to upload.");
    }
    if (state.editingFileId && !displayName && !selectedFile) {
        throw new Error("Provide a new file or updated title.");
    }

    setButtonLoading(fileUploadBtn, true, "Uploading...");
    try {
        if (state.editingFileId) {
            await updateFile(state.editingFileId, displayName, selectedFile);
        } else {
            const formData = new FormData();
            formData.set("channel_id", channelId);
            formData.set("name", displayName);
            formData.set("file", selectedFile);
            await apiRequest("/api/server/files", {
                method: "POST",
                body: formData,
            });
        }
        resetFileEditMode();
        state.filesPage = 1;
        await fetchFiles();
        await fetchChannels();
        await fetchActivities();
    } finally {
        setButtonLoading(fileUploadBtn, false);
    }
}

async function updateFile(fileId, name, file) {
    const formData = new FormData();
    if (name) formData.set("name", name);
    if (file) formData.set("file", file);
    await apiRequest(`/api/server/files/${encodeURIComponent(fileId)}`, {
        method: "PUT",
        body: formData,
    });
}

async function deleteFile(fileId) {
    await apiRequest(`/api/server/files/${encodeURIComponent(fileId)}`, {
        method: "DELETE",
    });
}

async function fetchNotifications() {
    if (!notificationsModalBody) return;
    if (!state.activeChannelId) {
        notificationsModalBody.innerHTML = '<div class="server-empty-state">No recent notifications.</div>';
        if (notificationsModalPaginationEl) {
            notificationsModalPaginationEl.innerHTML = "";
        }
        return;
    }
    notificationsModalBody.innerHTML = `
        <div class="server-loading">
            <div class="server-loading-spinner"></div>
            <span>Loading notifications...</span>
        </div>
    `;

    const params = new URLSearchParams({
        channel_id: String(state.activeChannelId),
        scope: "all",
        page: String(state.notificationsPage),
        per_page: String(NOTIFICATIONS_PAGE_SIZE),
    });
    const payload = await apiRequest(`/api/server/messages?${params.toString()}`);
    state.notifications = payload.messages || [];
    state.notificationsPage = Number(payload.pagination?.page || state.notificationsPage || 1);
    state.notificationsTotalPages = Number(payload.pagination?.total_pages || 1);
    state.notificationsTotalItems = Number(payload.pagination?.total_items || state.notifications.length);

    if (!state.notifications.length) {
        notificationsModalBody.innerHTML = '<div class="server-empty-state">No recent notifications.</div>';
    } else {
        notificationsModalBody.innerHTML = state.notifications.map((row) => `
            <button type="button" class="server-search-item" data-action="notif-open" data-message-id="${escapeHtml(row.id || "")}" data-parent-message-id="${escapeHtml(row.parent_message_id || "")}" data-bs-dismiss="modal">
                <div class="server-search-item-title">
                    <strong>${escapeHtml(row.username || "member")}</strong>
                    <span>${escapeHtml(formatDate(row.created_at))}</span>
                </div>
                <div class="server-search-item-meta">${row.parent_message_id ? "Thread activity" : "Channel activity"}</div>
                <div class="server-search-item-text">${escapeHtml((row.text || "").slice(0, 160))}</div>
            </button>
        `).join("");
    }

    renderPagination(
        notificationsModalPaginationEl,
        state.notificationsPage,
        state.notificationsTotalPages,
        state.notificationsTotalItems,
        "notif-page-prev",
        "notif-page-next",
    );
}

async function fetchActivities() {
    if (!activitiesListEl) return;
    activitiesListEl.innerHTML = `
        <div class="server-loading server-loading-sm">
            <div class="server-loading-spinner"></div>
            <span>Loading activities...</span>
        </div>
    `;

    const params = new URLSearchParams({
        page: String(state.activitiesPage),
        per_page: String(ACTIVITIES_PAGE_SIZE),
    });
    if (state.activitiesFilter && state.activitiesFilter !== "all") {
        params.set("filter", state.activitiesFilter);
    }
    const payload = await apiRequest(`/api/server/activities?${params.toString()}`);
    state.activities = payload.activities || [];
    state.activitiesPage = Number(payload.pagination?.page || state.activitiesPage || 1);
    state.activitiesTotalPages = Number(payload.pagination?.total_pages || 1);
    state.activitiesTotalItems = Number(payload.pagination?.total_items || state.activities.length);

    if (!state.activities.length) {
        activitiesListEl.innerHTML = '<div class="server-empty-state server-empty-state-sm">No recent activities.</div>';
    } else {
        activitiesListEl.innerHTML = state.activities.map((row) => `
            <button type="button" class="server-activity-item" data-action="activity-open" data-channel-id="${escapeHtml(row.channel_id || "")}" data-message-id="${escapeHtml(row.id || "")}" data-parent-message-id="${escapeHtml(row.parent_message_id || "")}">
                <div class="server-activity-item-head">
                    <span class="server-activity-channel">#${escapeHtml(row.channel_name || "channel")}</span>
                    <span class="server-activity-time">${escapeHtml(formatDate(row.created_at))}</span>
                </div>
                <div class="server-activity-item-body">
                    <strong>${escapeHtml(row.username || "member")}</strong>
                    <span>${escapeHtml((row.text || "").slice(0, 74))}</span>
                    <span class="server-search-item-meta">${escapeHtml((row.activity_kind || "all").replace(/^./, (m) => m.toUpperCase()))}</span>
                </div>
            </button>
        `).join("");
    }

    renderPagination(
        activitiesPaginationEl,
        state.activitiesPage,
        state.activitiesTotalPages,
        state.activitiesTotalItems,
        "activities-page-prev",
        "activities-page-next",
    );
    renderActivityFilters();
}

function renderActivityFilters() {
    if (!activityFiltersEl) return;
    const buttons = activityFiltersEl.querySelectorAll("[data-activity-filter]");
    buttons.forEach((button) => {
        const filter = String(button.getAttribute("data-activity-filter") || "all");
        button.classList.toggle("is-active", filter === state.activitiesFilter);
    });
}

function renderSearchResults() {
    if (!searchResultsEl || !searchResultMeta) return;
    if (!state.searchQuery) {
        searchResultMeta.textContent = "Type a keyword to search messages and thread replies.";
        searchResultsEl.innerHTML = "";
        return;
    }
    searchResultMeta.textContent = `${state.searchResults.length} result${state.searchResults.length === 1 ? "" : "s"} for "${state.searchQuery}"`;
    if (!state.searchResults.length) {
        searchResultsEl.innerHTML = '<div class="server-empty-state">No matching messages found.</div>';
        return;
    }

    searchResultsEl.innerHTML = state.searchResults.map((row) => `
        <button type="button" class="server-search-item" data-action="search-open" data-message-id="${escapeHtml(row.id || "")}" data-parent-message-id="${escapeHtml(row.parent_message_id || "")}">
            <div class="server-search-item-title">
                <strong>${escapeHtml(row.username || "member")}</strong>
                <span>${escapeHtml(formatDate(row.created_at))}</span>
            </div>
            <div class="server-search-item-meta">${row.parent_message_id ? "Thread reply" : "Channel message"}</div>
            <div class="server-search-item-text">${escapeHtml((row.text || "").slice(0, 170))}</div>
        </button>
    `).join("");
}

async function fetchSearchResults() {
    if (!state.activeChannelId || !state.searchQuery) {
        state.searchResults = [];
        renderSearchResults();
        return;
    }

    const params = new URLSearchParams({
        channel_id: String(state.activeChannelId),
        scope: "all",
        search: state.searchQuery,
        page: "1",
        per_page: "50",
    });
    const payload = await apiRequest(`/api/server/messages?${params.toString()}`);
    state.searchResults = payload.messages || [];
    renderSearchResults();
}

document.addEventListener("click", async (event) => {
    const activityFilterBtn = event.target.closest("[data-activity-filter]");
    if (activityFilterBtn) {
        const nextFilter = String(activityFilterBtn.getAttribute("data-activity-filter") || "all").toLowerCase();
        if (nextFilter !== state.activitiesFilter) {
            state.activitiesFilter = nextFilter;
            state.activitiesPage = 1;
            await fetchActivities();
        }
        return;
    }

    const channelBtn = event.target.closest("[data-channel-id]");
    const channelActionBtn = event.target.closest("[data-action='rename-channel'], [data-action='delete-channel']");

    if (channelActionBtn) {
        const action = String(channelActionBtn.getAttribute("data-action") || "");
        const channelId = String(channelActionBtn.getAttribute("data-channel-id") || "");
        if (!channelId) return;

        if (action === "rename-channel") {
            const channel = state.channels.find((item) => String(item.id) === channelId);
            if (!channel) return;
            state.pendingRenameChannelId = channelId;
            if (renameChannelIdInput) renameChannelIdInput.value = channelId;
            if (renameChannelNameInput) renameChannelNameInput.value = String(channel.name || "");
            if (renameChannelDescriptionInput) renameChannelDescriptionInput.value = String(channel.description || "");
            renameChannelModalInstance?.show();
            return;
        }

        if (action === "delete-channel") {
            state.pendingDeleteChannelId = channelId;
            deleteChannelModalInstance?.show();
            return;
        }
    }

    if (channelBtn && !event.target.closest(".server-channel-row-actions")) {
        const channelId = channelBtn.getAttribute("data-channel-id");
        if (!channelId) return;
        resetFileEditMode();
        state.activeChannelId = channelId;
        state.chatPage = 1;
        state.filesPage = 1;
        state.threadPage = 1;
        state.searchQuery = "";
        closeThreadPanel();
        renderChannels();
        renderActiveChannelDetails();
        updateChannelUrl(channelId);
        await fetchMessages();
        await fetchNotifications().catch(() => null);
        return;
    }

    const actionButton = event.target.closest("[data-action]");
    if (!actionButton) {
        return;
    }

    const action = actionButton.getAttribute("data-action");
    const messageId = actionButton.getAttribute("data-message-id") || "";
    try {
        if (action === "open-profile") {
            const userId = actionButton.getAttribute("data-user-id") || "";
            if (!userId) return;
            await openProfilePanel(userId);
            return;
        }

        if (action === "reply") {
            await openThreadPanel(messageId);
            return;
        }

        if (action === "open-reaction-modal") {
            state.reactionTargetMessageId = messageId;
            reactionModalInstance?.show();
            return;
        }

        if (action === "pick-reaction") {
            const emoji = actionButton.getAttribute("data-emoji") || "";
            if (!emoji || !state.reactionTargetMessageId) return;
            await reactToMessage(state.reactionTargetMessageId, emoji);
            state.reactionTargetMessageId = "";
            reactionModalInstance?.hide();
            await fetchMessages();
            return;
        }

        if (action === "edit") {
            const message = getMessageById(messageId) || state.threadMessages.find((item) => String(item.id) === String(messageId));
            if (!message) return;
            state.pendingEditMessageId = messageId;
            if (editMessageInput) {
                editMessageInput.value = String(message.raw_text || message.text || "");
            }
            editModalInstance?.show();
            return;
        }

        if (action === "delete") {
            state.pendingDeleteMessageId = messageId;
            deleteModalInstance?.show();
            return;
        }

        if (action === "react") {
            const emoji = actionButton.getAttribute("data-emoji") || "";
            if (!emoji) return;
            await reactToMessage(messageId, emoji);
            await fetchMessages();
            return;
        }

        if (action === "pin") {
            await togglePinMessage(messageId);
            await fetchMessages();
            return;
        }

        if (action === "chat-page-prev" && state.chatPage > 1) {
            state.chatPage -= 1;
            await fetchMessages();
            return;
        }

        if (action === "chat-page-next" && state.chatPage < state.chatTotalPages) {
            state.chatPage += 1;
            await fetchMessages();
            return;
        }

        if (action === "files-page-prev" && state.filesPage > 1) {
            state.filesPage -= 1;
            await fetchFiles();
            return;
        }

        if (action === "files-page-next" && state.filesPage < state.filesTotalPages) {
            state.filesPage += 1;
            await fetchFiles();
            return;
        }

        if (action === "thread-page-prev" && state.threadPage > 1) {
            state.threadPage -= 1;
            await fetchThreadMessages();
            return;
        }

        if (action === "thread-page-next" && state.threadPage < state.threadTotalPages) {
            state.threadPage += 1;
            await fetchThreadMessages();
            return;
        }

        if (action === "notif-page-prev" && state.notificationsPage > 1) {
            state.notificationsPage -= 1;
            await fetchNotifications();
            return;
        }

        if (action === "notif-page-next" && state.notificationsPage < state.notificationsTotalPages) {
            state.notificationsPage += 1;
            await fetchNotifications();
            return;
        }

        if (action === "activities-page-prev" && state.activitiesPage > 1) {
            state.activitiesPage -= 1;
            await fetchActivities();
            return;
        }

        if (action === "activities-page-next" && state.activitiesPage < state.activitiesTotalPages) {
            state.activitiesPage += 1;
            await fetchActivities();
            return;
        }

        if (action === "search-open") {
            const parentMessageId = String(actionButton.getAttribute("data-parent-message-id") || "");
            window.bootstrap?.Modal.getInstance(searchModal)?.hide();
            if (parentMessageId) {
                await openThreadPanel(parentMessageId);
            } else if (messageId) {
                if (state.viewMode === "files") {
                    state.viewMode = "messages";
                    state.chatPage = 1;
                    renderModeTabs();
                    await fetchMessages();
                }
                const messageEl = document.querySelector(`[data-message-card-id=\"${CSS.escape(messageId)}\"]`);
                messageEl?.scrollIntoView({ behavior: "smooth", block: "center" });
            }
            return;
        }

        if (action === "notif-open") {
            const parentMessageId = String(actionButton.getAttribute("data-parent-message-id") || "");
            if (parentMessageId) {
                await openThreadPanel(parentMessageId);
            } else if (messageId) {
                if (state.viewMode === "files") {
                    state.viewMode = "messages";
                    state.chatPage = 1;
                    renderModeTabs();
                    await fetchMessages();
                }
                const messageEl = document.querySelector(`[data-message-card-id=\"${CSS.escape(messageId)}\"]`);
                messageEl?.scrollIntoView({ behavior: "smooth", block: "center" });
            }
            return;
        }

        if (action === "activity-open") {
            const channelId = String(actionButton.getAttribute("data-channel-id") || "");
            const parentMessageId = String(actionButton.getAttribute("data-parent-message-id") || "");
            const activityMessageId = String(actionButton.getAttribute("data-message-id") || "");
            if (channelId && channelId !== String(state.activeChannelId)) {
                state.activeChannelId = channelId;
                state.chatPage = 1;
                closeThreadPanel();
                renderChannels();
                renderActiveChannelDetails();
                updateChannelUrl(channelId);
                await fetchMessages();
            }
            if (parentMessageId) {
                await openThreadPanel(parentMessageId);
            } else if (activityMessageId) {
                if (state.viewMode === "files") {
                    state.viewMode = "messages";
                    state.chatPage = 1;
                    renderModeTabs();
                    await fetchMessages();
                }
                const messageEl = document.querySelector(`[data-message-card-id=\"${CSS.escape(activityMessageId)}\"]`);
                messageEl?.scrollIntoView({ behavior: "smooth", block: "center" });
            }
            return;
        }

        if (action === "edit-file") {
            const fileId = String(actionButton.getAttribute("data-file-id") || "");
            const fileRow = state.files.find((item) => String(item.id) === fileId);
            if (!fileRow) return;
            setFileEditMode(fileRow);
            return;
        }

        if (action === "delete-file") {
            const fileId = String(actionButton.getAttribute("data-file-id") || "");
            if (!fileId) return;
            if (!window.confirm("Delete this file?")) return;
            await deleteFile(fileId);
            await fetchFiles();
            await fetchChannels();
            await fetchActivities();
            return;
        }
    } catch (error) {
        console.error(error);
        window.alert(error.message || "Chat action failed");
    }
});

closeThreadPanelBtn?.addEventListener("click", () => {
    closeThreadPanel();
});

messageForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage().catch((error) => {
        window.alert(error.message || "Failed to send message");
    });
});

fileForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    uploadFile().catch((error) => {
        window.alert(error.message || "Failed to upload file");
    });
});

fileEditCancelBtn?.addEventListener("click", () => {
    resetFileEditMode();
});

threadForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    sendThreadReply().catch((error) => {
        window.alert(error.message || "Failed to reply in thread");
    });
});

createChannelForm?.addEventListener("submit", (event) => {
    createChannel(event).catch((error) => {
        window.alert(error.message || "Failed to create channel");
    });
});

renameChannelForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    const channelId = String(renameChannelIdInput?.value || state.pendingRenameChannelId || "").trim();
    const name = String(renameChannelNameInput?.value || "").trim();
    const description = String(renameChannelDescriptionInput?.value || "").trim();
    if (!channelId || !name) {
        window.alert("Channel name is required.");
        return;
    }

    const submitButton = renameChannelForm.querySelector("button[type='submit']");
    setButtonLoading(submitButton, true, "Saving...");
    updateChannel(channelId, { name, description })
        .then(async () => {
            state.pendingRenameChannelId = "";
            renameChannelModalInstance?.hide();
            await fetchChannels();
            await fetchMessages();
        })
        .catch((error) => {
            window.alert(error.message || "Failed to rename channel");
        })
        .finally(() => {
            setButtonLoading(submitButton, false);
        });
});

confirmDeleteChannelBtn?.addEventListener("click", () => {
    const channelId = String(state.pendingDeleteChannelId || "").trim();
    if (!channelId) return;

    setButtonLoading(confirmDeleteChannelBtn, true, "Deleting...");
    deleteChannel(channelId)
        .then(async () => {
            state.pendingDeleteChannelId = "";
            deleteChannelModalInstance?.hide();
            await fetchChannels();
            await fetchMessages();
            await fetchActivities();
        })
        .catch((error) => {
            window.alert(error.message || "Failed to delete channel");
        })
        .finally(() => {
            setButtonLoading(confirmDeleteChannelBtn, false);
        });
});

confirmDeleteMessageBtn?.addEventListener("click", () => {
    const messageId = String(state.pendingDeleteMessageId || "").trim();
    if (!messageId) return;

    setButtonLoading(confirmDeleteMessageBtn, true, "Deleting...");
    deleteMessage(messageId)
        .then(async () => {
            state.pendingDeleteMessageId = "";
            deleteModalInstance?.hide();
            await fetchMessages();
            await fetchActivities();
        })
        .catch((error) => {
            window.alert(error.message || "Failed to delete message");
        })
        .finally(() => {
            setButtonLoading(confirmDeleteMessageBtn, false);
        });
});

editMessageForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    const messageId = String(state.pendingEditMessageId || "").trim();
    const text = String(editMessageInput?.value || "").trim();
    if (!messageId || !text) {
        window.alert("Message text is required.");
        return;
    }

    const submitButton = editMessageForm.querySelector("button[type='submit']");
    setButtonLoading(submitButton, true, "Saving...");
    updateMessageInline(messageId, text)
        .then(async () => {
            state.pendingEditMessageId = "";
            editModalInstance?.hide();
            await fetchMessages();
            if (state.threadRootId) {
                await fetchThreadMessages();
            }
            await fetchActivities();
        })
        .catch((error) => {
            window.alert(error.message || "Failed to update message");
        })
        .finally(() => {
            setButtonLoading(submitButton, false);
        });
});

messagesTabBtn?.addEventListener("click", async () => {
    if (state.viewMode === "messages") return;
    resetFileEditMode();
    state.viewMode = "messages";
    state.chatPage = 1;
    renderModeTabs();
    await fetchMessages();
});

pinsTabBtn?.addEventListener("click", async () => {
    if (state.viewMode === "pins") return;
    resetFileEditMode();
    state.viewMode = "pins";
    state.chatPage = 1;
    renderModeTabs();
    await fetchMessages();
});

filesTabBtn?.addEventListener("click", async () => {
    if (state.viewMode === "files") return;
    resetFileEditMode();
    state.viewMode = "files";
    state.filesPage = 1;
    renderModeTabs();
    closeThreadPanel();
    await fetchFiles();
});

notificationsModal?.addEventListener("shown.bs.modal", () => {
    state.notificationsPage = 1;
    fetchNotifications().catch((error) => {
        if (notificationsModalBody) {
            notificationsModalBody.innerHTML = `<div class="server-empty-state">${escapeHtml(error.message || "Failed to load notifications.")}</div>`;
        }
    });
});

searchForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    state.searchQuery = String(searchInput?.value || "").trim();
    state.chatPage = 1;
    state.threadPage = 1;
    fetchMessages()
        .then(() => fetchSearchResults())
        .catch((error) => {
            window.alert(error.message || "Search failed");
        });
});

clearSearchBtn?.addEventListener("click", () => {
    state.searchQuery = "";
    if (searchInput) searchInput.value = "";
    state.chatPage = 1;
    fetchMessages()
        .then(() => {
            state.searchResults = [];
            renderSearchResults();
        })
        .catch((error) => {
            window.alert(error.message || "Failed to clear search");
        });
});

searchModal?.addEventListener("shown.bs.modal", () => {
    if (searchInput) {
        searchInput.value = state.searchQuery;
        searchInput.focus();
    }
    renderSearchResults();
    if (state.searchQuery) {
        fetchSearchResults().catch(() => null);
    }
});

refreshActivitiesBtn?.addEventListener("click", () => {
    fetchActivities().catch(() => null);
});

themeToggleBtn?.addEventListener("click", () => {
    toggleTheme();
});

messageInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        messageForm?.requestSubmit();
    }
});

threadInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        threadForm?.requestSubmit();
    }
});

document.addEventListener("click", (event) => {
    const actionBtn = event.target.closest("[data-compose-action]");
    if (!actionBtn) return;
    const action = actionBtn.getAttribute("data-compose-action");
    const targetSelector = actionBtn.getAttribute("data-compose-target");
    const targetInput = targetSelector ? document.querySelector(targetSelector) : messageInput;
    if (action === "bold") {
        wrapSelection(targetInput, "**");
    } else if (action === "italic") {
        wrapSelection(targetInput, "_");
    } else if (action === "list") {
        addListPrefix(targetInput);
    } else if (action === "code") {
        wrapSelection(targetInput, "`");
    } else if (action === "mention") {
        wrapSelection(targetInput, "@", "");
    }
});

async function init() {
    try {
        applyTheme(getInitialTheme());
        renderModeTabs();
        renderActivityFilters();
        if (reactionPickerGrid) {
            reactionPickerGrid.innerHTML = REACTION_EMOJIS.map((emoji) => `
                <button type="button" class="server-emoji-btn" data-action="pick-reaction" data-emoji="${escapeHtml(emoji)}">${escapeHtml(emoji)}</button>
            `).join("");
        }
        await fetchChannels();
        await fetchMessages();
        await fetchActivities();
        if (threadPanelEl) {
            threadPanelEl.classList.add("is-empty");
        }
        chatBodyEl?.classList.remove("is-thread-open");
        if (profileMetaStatusEl && state.currentUser) {
            const role = String(state.currentUser.account_type || "member");
            profileMetaStatusEl.textContent = `${role.charAt(0).toUpperCase()}${role.slice(1)} - Online`;
        }
        updateChannelUrl(state.activeChannelId);
    } catch (error) {
        console.error(error);
        window.alert(error.message || "Failed to load server community");
    }
}

init();
