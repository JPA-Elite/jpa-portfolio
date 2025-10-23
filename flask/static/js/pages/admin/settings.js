document.getElementById("profileForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const usernameError = document.getElementById("usernameError");
    const passwordError = document.getElementById("passwordError");
    let isValid = true;

    usernameError.classList.add("d-none");
    passwordError.classList.add("d-none");

    if (!username) {
        usernameError.textContent = "Username is required.";
        usernameError.classList.remove("d-none");
        isValid = false;
    } else if (username.length < 5) {
        usernameError.textContent = "Username must be at least 5 characters.";
        usernameError.classList.remove("d-none");
        isValid = false;
    }

    if (!password) {
        passwordError.textContent = "Password is required.";
        passwordError.classList.remove("d-none");
        isValid = false;
    } else if (password.length < 5) {
        passwordError.textContent = "Password must be at least 5 characters.";
        passwordError.classList.remove("d-none");
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
        const msgBox = document.getElementById("responseMessage");

        if (res.ok) {
            msgBox.innerHTML = `<div class="alert alert-success">${result.message}</div>`;
        } else {
            msgBox.innerHTML = `<div class="alert alert-danger">${result.message}</div>`;
        }

        setTimeout(() => {
            window.location.href = "/admin/logout";
        }, 2000);
    } catch (error) {
        document.getElementById("responseMessage").innerHTML =
            `<div class="alert alert-danger">Something went wrong.</div>`;
        console.error(error);
    }
});
