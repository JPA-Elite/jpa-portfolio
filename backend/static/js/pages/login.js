document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
    const signInBtn = form.querySelector("button[type='submit']");
    const usernameField = form.querySelector("input[name='username']");
    const passwordField = form.querySelector("input[name='password']");

    function showError(input, message) {
        input.classList.add("is-invalid");
        // Remove any existing error message for this field
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

    // Real-time: clear error as user types
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
});