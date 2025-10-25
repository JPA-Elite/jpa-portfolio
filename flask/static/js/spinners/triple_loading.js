function showTripleLoading() {
    let loader = document.querySelector(".dots-loader");
    if (loader) {
        loader.style.display = "flex";
    }
}

function hideTripleLoading() {
    let loader = document.querySelector(".dots-loader");
    if (loader) {
        loader.style.display = "none";
    }
}