import { AdminSettingsService } from "../../services/AdminSettingsService.js";

const adminSettingsService = new AdminSettingsService();

function setButtonLoading(button, isLoading) {
    if (!button) return;
    if (isLoading) {
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...`;
        button.disabled = true;
    } else {
        button.innerHTML = button.dataset.originalText || "Save Changes";
        button.disabled = false;
    }
}

document.getElementById("profileForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const confirmPassword = document.getElementById("confirmPassword").value.trim();
    const profileImageFile = document.getElementById("profileImage").files[0];

    const usernameError = document.getElementById("usernameError");
    const passwordError = document.getElementById("passwordError");
    const confirmPasswordError = document.getElementById("confirmPasswordError");
    const profileImageError = document.getElementById("profileImageError");
    const msgBox = document.getElementById("responseMessage");
    const saveButton = this.querySelector("button[type='submit']");

    let isValid = true;

    // Reset error states
    usernameError.classList.add("d-none");
    passwordError.classList.add("d-none");
    confirmPasswordError.classList.add("d-none");
    profileImageError.classList.add("d-none");
    if (msgBox) msgBox.innerHTML = "";

    // Username validation
    if (!username) {
        usernameError.textContent = "Username is required.";
        usernameError.classList.remove("d-none");
        isValid = false;
    } else if (username.length < 5) {
        usernameError.textContent = "Username must be at least 5 characters.";
        usernameError.classList.remove("d-none");
        isValid = false;
    }

    // Password validation
    if (password && password.length < 5) {
        passwordError.textContent = "Password must be at least 5 characters.";
        passwordError.classList.remove("d-none");
        isValid = false;
    }

    // Confirm password validation
    if (password && confirmPassword !== password) {
        confirmPasswordError.textContent = "Passwords do not match.";
        confirmPasswordError.classList.remove("d-none");
        isValid = false;
    } else if (!password && confirmPassword) {
        confirmPasswordError.textContent = "Enter password first.";
        confirmPasswordError.classList.remove("d-none");
        isValid = false;
    }

    if (profileImageFile && !profileImageFile.type.startsWith("image/")) {
        profileImageError.textContent = "Please upload a valid image file.";
        profileImageError.classList.remove("d-none");
        isValid = false;
    }

    if (!isValid) return;
    setButtonLoading(saveButton, true);

    const data = new FormData();
    data.append("username", username);
    if (password) {
        data.append("password", password);
    }
    if (profileImageFile) {
        data.append("profile_image_file", profileImageFile);
    }

    let keepLoading = false;
    try {
        const result = await adminSettingsService.updateProfile(data);

        if (result.ok) {
            window.notify(result.data?.message || "Updated.", "success");

            if (result.data?.profile_image) {
                const preview = document.getElementById("profileImagePreview");
                if (preview) {
                    preview.src = result.data.profile_image;
                }
            }

            if (password) {
                keepLoading = true;
                setTimeout(() => window.location.href = "/admin/logout", 1500);
            } else {
                keepLoading = true;
                setTimeout(() => window.location.reload(), 900);
            }
        } else {
            window.notify(result.data?.message || "Update failed.", "error");
        }
    } catch (error) {
        window.notify("Something went wrong.", "error");
        console.error(error);
    } finally {
        if (!keepLoading) {
            setButtonLoading(saveButton, false);
        }
    }
});

document.getElementById("profileImage")?.addEventListener("change", (event) => {
    const file = event.target.files?.[0];
    if (!file || !file.type.startsWith("image/")) return;

    const preview = document.getElementById("profileImagePreview");
    if (!preview) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        preview.src = e.target?.result || preview.src;
    };
    reader.readAsDataURL(file);
});
