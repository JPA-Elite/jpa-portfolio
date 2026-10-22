import { AdminFaceService } from "../../services/AdminFaceService.js";

const adminFaceService = new AdminFaceService();

(function () {
    const statusEl = document.getElementById("faceStatus");
    const videoEl = document.getElementById("faceVideo");
    const canvasEl = document.getElementById("faceCanvas");
    const registerBtn = document.getElementById("registerBtn");
    const verifyBtn = document.getElementById("verifyBtn");

    if (!statusEl || !videoEl || !canvasEl || !registerBtn || !verifyBtn) return;

    function setStatus(message, type) {
        statusEl.className = "alert alert-" + (type || "info");
        statusEl.textContent = message;
    }

    function captureFrameAsB64() {
        const w = videoEl.videoWidth;
        const h = videoEl.videoHeight;
        if (!w || !h) throw new Error("Camera not ready.");

        canvasEl.width = w;
        canvasEl.height = h;
        const ctx = canvasEl.getContext("2d");
        ctx.drawImage(videoEl, 0, 0, w, h);

        return canvasEl.toDataURL("image/jpeg", 0.85);
    }

    function sleep(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }

    async function captureMultiFramesB64(count = 5, intervalMs = 150) {
        const frames = [];
        for (let i = 0; i < count; i++) {
            frames.push(captureFrameAsB64());
            if (i < count - 1) await sleep(intervalMs);
        }
        return frames;
    }

    async function postFace(action) {
        const frames = await captureMultiFramesB64(5, 150);
        if (action === "register") {
            return adminFaceService.register(frames);
        }
        return adminFaceService.verify(frames);
    }

    async function startCamera() {
        try {
            setStatus("Starting camera...", "info");
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: "user" },
                audio: false,
            });
            videoEl.srcObject = stream;

            stream.getVideoTracks().forEach((track) => {
                track.enabled = true;
            });
            registerBtn.disabled = false;
            verifyBtn.disabled = false;

            setStatus("Camera ready. Register your face, then verify.", "success");
        } catch (error) {
            setStatus("Camera error: " + (error && error.message ? error.message : String(error)), "danger");
            registerBtn.disabled = true;
            verifyBtn.disabled = true;
        }
    }

    registerBtn.addEventListener("click", async function () {
        registerBtn.disabled = true;
        verifyBtn.disabled = true;
        try {
            setStatus("Registering face... Please stay still.", "info");
            const payload = await postFace("register");
            setStatus(payload.message || "Face registered successfully.", "success");
            verifyBtn.disabled = false;
        } catch (error) {
            setStatus(error && error.message ? error.message : "Failed to register face.", "danger");
        } finally {
            registerBtn.disabled = false;
            verifyBtn.disabled = false;
        }
    });

    verifyBtn.addEventListener("click", async function () {
        registerBtn.disabled = true;
        verifyBtn.disabled = true;
        try {
            setStatus("Verifying face... Please stay still.", "info");
            const payload = await postFace("verify");
            setStatus(payload.message || "Face verified. Unlocking...", "success");
            window.location.href = "/admin/dashboard";
        } catch (error) {
            setStatus(error && error.message ? error.message : "Failed to verify face.", "danger");
            registerBtn.disabled = false;
            verifyBtn.disabled = false;
        }
    });

    startCamera();
})();
