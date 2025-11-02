document.getElementById("profileForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const confirmPassword = document.getElementById("confirmPassword").value.trim();

    const usernameError = document.getElementById("usernameError");
    const passwordError = document.getElementById("passwordError");
    const confirmPasswordError = document.getElementById("confirmPasswordError");
    const msgBox = document.getElementById("responseMessage");

    let isValid = true;

    // Reset error states
    usernameError.classList.add("d-none");
    passwordError.classList.add("d-none");
    confirmPasswordError.classList.add("d-none");
    msgBox.innerHTML = "";

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
    if (!password) {
        passwordError.textContent = "Password is required.";
        passwordError.classList.remove("d-none");
        isValid = false;
    } else if (password.length < 5) {
        passwordError.textContent = "Password must be at least 5 characters.";
        passwordError.classList.remove("d-none");
        isValid = false;
    }

    // Confirm password validation
    if (password && confirmPassword !== password) {
        confirmPasswordError.textContent = "Passwords do not match.";
        confirmPasswordError.classList.remove("d-none");
        isValid = false;
    }

    if (!isValid) return;

    const data = { username, password };

    try {
        const res = await fetch("/admin/api/update-profile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await res.json();

        if (res.ok) {
            msgBox.innerHTML = `<div class="alert alert-success">${result.message}</div>`;
            setTimeout(() => window.location.href = "/admin/logout", 2000);
        } else {
            msgBox.innerHTML = `<div class="alert alert-danger">${result.message}</div>`;
        }
    } catch (error) {
        msgBox.innerHTML = `<div class="alert alert-danger">Something went wrong.</div>`;
        console.error(error);
    }
});
