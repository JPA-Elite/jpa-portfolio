function showLoading() {
    let overlay = document.getElementById("loading-overlay");
    if (overlay) {
        overlay.style.display = "flex";
    }
}

function hideLoading() {
    let overlay = document.getElementById("loading-overlay");
    if (overlay) {
        overlay.style.display = "none";
    }
}