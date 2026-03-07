const authConfig = window.serverAuthConfig || {};

const googleButtonId = String(authConfig.googleButtonId || "").trim();
const googleButton = googleButtonId ? document.getElementById(googleButtonId) : null;
const firebaseConfig = authConfig.firebase || null;
const authMode = String(authConfig.mode || "login").trim().toLowerCase();
const authForm = document.querySelector(".server-auth-card form");
const authSubmitBtn = authForm ? authForm.querySelector("button[type=\"submit\"]") : null;

function setButtonLoading(button, isLoading, labelText) {
    if (!button) return;
    if (isLoading) {
        button.dataset.originalHtml = button.innerHTML;
        button.disabled = true;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            ${labelText || "Processing..."}
        `;
        return;
    }

    button.disabled = false;
    if (button.dataset.originalHtml) {
        button.innerHTML = button.dataset.originalHtml;
    }
}

function isFirebaseReady(config) {
    if (!config || typeof config !== "object") return false;
    return Boolean(config.apiKey && config.authDomain && config.projectId && config.appId);
}

async function signInWithGoogle() {
    if (!googleButton) return;
    if (!isFirebaseReady(firebaseConfig)) {
        window.alert("Google sign-in is not configured. Set Firebase env values first.");
        return;
    }

    setButtonLoading(googleButton, true, "Connecting Google...");
    try {
        const [{ initializeApp }, { getAuth, GoogleAuthProvider, signInWithPopup }] = await Promise.all([
            import("https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js"),
            import("https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js"),
        ]);

        const app = initializeApp(firebaseConfig);
        const auth = getAuth(app);
        const provider = new GoogleAuthProvider();
        provider.setCustomParameters({ prompt: "select_account" });

        const result = await signInWithPopup(auth, provider);
        const idToken = await result.user.getIdToken();

        const response = await fetch("/api/server/auth/google", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                id_token: idToken,
                mode: authMode === "register" ? "register" : "login",
            }),
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.message || "Google authentication failed.");
        }

        window.location.href = "/server/app";
    } catch (error) {
        window.alert(error?.message || "Google sign-in failed.");
    } finally {
        setButtonLoading(googleButton, false);
    }
}

if (googleButton) {
    googleButton.addEventListener("click", () => {
        signInWithGoogle().catch(() => null);
    });
}

if (authForm && authSubmitBtn) {
    authForm.addEventListener("submit", () => {
        const label = authMode === "register" ? "Creating account..." : "Signing in...";
        setButtonLoading(authSubmitBtn, true, label);
    });
}
