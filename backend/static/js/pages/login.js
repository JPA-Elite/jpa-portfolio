document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
    const signInBtn = form.querySelector("button[type='submit']");

    form.addEventListener("submit", () => {
        signInBtn.disabled = true;
        signInBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span>`;
    });
});