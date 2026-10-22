import { AdminOtpService } from "../services/AdminOtpService.js";

const adminOtpService = new AdminOtpService();

function initAdminOtpGate() {
    const modalEl = document.getElementById("otpVerifyModal");
    const showOtpModal = modalEl?.dataset?.showFaceModal === "1";

    if (!modalEl) return;

    const statusEl = document.getElementById("otpModalStatus");
    const savedEmailEl = document.getElementById("otpSavedEmail");
    const otpCodeInput = document.getElementById("otpCodeInput");
    const sendOtpBtn = document.getElementById("sendOtpBtn");
    const verifyOtpBtn = document.getElementById("verifyOtpBtn");

    if (!statusEl || !savedEmailEl || !otpCodeInput || !sendOtpBtn || !verifyOtpBtn) return;
    if (!showOtpModal) return;

    const jquery = window.jQuery;

    let verificationCompleted = false;
    let cooldownUntilMs = 0;
    let savedEmail = "";
    let cooldownTimerId = null;

    function isInCooldown() {
        return Date.now() < cooldownUntilMs;
    }

    function setStatus(message, type) {
        statusEl.className = "alert alert-" + (type || "info");
        statusEl.textContent = message;
    }

    function applyCooldown(seconds, message) {
        const safeSeconds = Math.max(0, Number(seconds) || 0);
        if (safeSeconds <= 0) return;

        cooldownUntilMs = Date.now() + safeSeconds * 1000;
        sendOtpBtn.disabled = true;
        verifyOtpBtn.disabled = true;
        otpCodeInput.disabled = true;

        setStatus(message || `Too many invalid attempts. Please wait ${safeSeconds} seconds and try again.`, "danger");

        if (cooldownTimerId) {
            clearInterval(cooldownTimerId);
            cooldownTimerId = null;
        }

        cooldownTimerId = setInterval(() => {
            if (verificationCompleted) {
                clearInterval(cooldownTimerId);
                cooldownTimerId = null;
                return;
            }

            const remainingMs = cooldownUntilMs - Date.now();
            const remainingSeconds = Math.max(0, Math.ceil(remainingMs / 1000));

            if (remainingSeconds <= 0) {
                clearInterval(cooldownTimerId);
                cooldownTimerId = null;

                const value = (otpCodeInput.value || "").trim();
                otpCodeInput.disabled = false;
                sendOtpBtn.disabled = !savedEmail;
                verifyOtpBtn.disabled = value.length < 4 || !savedEmail;
                setStatus("Cooldown ended. You can try again.", "info");
                return;
            }

            setStatus(
                message || `Too many invalid attempts. Please wait ${remainingSeconds} seconds and try again.`,
                "danger"
            );
        }, 500);
    }

    async function loadSavedEmail() {
        try {
            setStatus("Loading saved OTP email...", "info");
            const result = await adminOtpService.fetchEmail();
            const payload = result.data;

            if (!result.ok || !payload || payload.ok !== true) {
                const message = (payload && payload.message) ? payload.message : "Failed to load OTP email.";
                setStatus(message, "danger");
                sendOtpBtn.disabled = true;
                savedEmailEl.textContent = "—";
                return;
            }

            savedEmail = (payload.email || "").trim();
            savedEmailEl.textContent = "OTP will be sent to the authorized email";

            const retryAfterSeconds = Number(payload.retry_after_seconds || 0);
            if (retryAfterSeconds > 0) {
                applyCooldown(retryAfterSeconds, payload.message || "Too many invalid attempts. Please wait and try again.");
                return;
            }

            if (!savedEmail) {
                setStatus("OTP email is not set in Admin Settings.", "warning");
                sendOtpBtn.disabled = true;
                return;
            }

            setStatus("OTP is ready. Click Send OTP.", "success");
            sendOtpBtn.disabled = false;
        } catch (error) {
            setStatus("Could not load OTP email.", "danger");
            sendOtpBtn.disabled = true;
            savedEmailEl.textContent = "—";
        }
    }

    sendOtpBtn.disabled = true;
    loadSavedEmail();

    otpCodeInput.addEventListener("input", function () {
        const value = (otpCodeInput.value || "").trim();
        verifyOtpBtn.disabled = value.length < 4;
    });

    async function sendOtp() {
        sendOtpBtn.disabled = true;
        verifyOtpBtn.disabled = true;

        try {
            setStatus("Sending OTP...", "info");
            const payload = await adminOtpService.sendOtp();
            setStatus(payload.message || "OTP sent. Check your email.", "success");
            otpCodeInput.disabled = false;
            otpCodeInput.value = "";
            verifyOtpBtn.disabled = true;
            setTimeout(() => otpCodeInput.focus(), 0);
        } catch (error) {
            setStatus(error && error.message ? error.message : "Failed to send OTP.", "danger");
            sendOtpBtn.disabled = false;
        } finally {
            if (!verificationCompleted) {
                sendOtpBtn.disabled = !savedEmail;
            }
        }
    }

    sendOtpBtn.addEventListener("click", async function () {
        await sendOtp();
    });

    verifyOtpBtn.addEventListener("click", async function () {
        sendOtpBtn.disabled = true;
        verifyOtpBtn.disabled = true;

        try {
            const otp = (otpCodeInput.value || "").trim();
            setStatus("Verifying OTP...", "info");

            const payload = await adminOtpService.verifyOtp(otp);
            verificationCompleted = true;
            setStatus(payload.message || "OTP verified. Redirecting...", "success");
            window.location.href = "/admin/dashboard";
        } catch (error) {
            const retryAfter = error && error.retry_after_seconds ? Number(error.retry_after_seconds) : 0;
            if (retryAfter > 0) {
                applyCooldown(retryAfter, error && error.message ? error.message : "Too many invalid attempts.");
                return;
            }

            setStatus(error && error.message ? error.message : "Failed to verify OTP.", "danger");
            verifyOtpBtn.disabled = false;
        } finally {
            if (!verificationCompleted) {
                if (!isInCooldown()) {
                    sendOtpBtn.disabled = !savedEmail;
                }
            }
        }
    });

    async function resetOtpGate() {
        try {
            await adminOtpService.resetOtp();
        } catch (error) {
            return;
        }
    }

    modalEl.addEventListener("hidden.bs.modal", function () {
        if (showOtpModal && !verificationCompleted) {
            resetOtpGate().finally(() => {
                if (jquery) {
                    jquery("#otpVerifyModal").modal({ backdrop: "static", keyboard: false });
                }
            });
        }
    });

    if (jquery) {
        jquery("#otpVerifyModal").modal({ backdrop: "static", keyboard: false });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
    const signInBtn = form.querySelector("button[type='submit']");
    const usernameField = form.querySelector("input[name='username']");
    const passwordField = form.querySelector("input[name='password']");

    function showError(input, message) {
        input.classList.add("is-invalid");
        const existing = input.parentElement.querySelector(".invalid-feedback-custom");
        if (existing) existing.remove();
        const div = document.createElement("div");
        div.className = "invalid-feedback-custom";
        div.textContent = message;
        input.parentElement.appendChild(div);
    }

    function clearError(input) {
        input.classList.remove("is-invalid");
        const existing = input.parentElement.querySelector(".invalid-feedback-custom");
        if (existing) existing.remove();
    }

    function validate() {
        let valid = true;
        clearError(usernameField);
        clearError(passwordField);

        if (!usernameField.value.trim()) {
            showError(usernameField, "Username is required.");
            valid = false;
        }
        if (!passwordField.value) {
            showError(passwordField, "Password is required.");
            valid = false;
        }
        return valid;
    }

    [usernameField, passwordField].forEach((field) => {
        field.addEventListener("input", () => clearError(field));
    });

    form.addEventListener("submit", (e) => {
        if (!validate()) {
            e.preventDefault();
            return;
        }
        signInBtn.disabled = true;
        signInBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span>`;
    });

    initAdminOtpGate();
});
