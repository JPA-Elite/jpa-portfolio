function showLoading() {
    let loader = document.querySelector(".dots-loader");
    if (loader) {
        loader.style.display = "flex";
    }
}

function hideLoading() {
    let loader = document.querySelector(".dots-loader");
    if (loader) {
        loader.style.display = "none";
    }
}