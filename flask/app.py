from flask import Flask, render_template, url_for, redirect, request  # type: ignore
import json
from config import (
    PROFILE_IMAGE,
    RESUME_PDF,
    GALLERY_JSON_PATH,
    IMAGE_PATH,
    VLOG_JSON_PATH,
    PROFILE_PAGE,
    GALLERY_PAGE,
    VLOG_PAGE,
    CONCERN_PAGE,
    ERROR_404_PAGE,
)
from utils import paginate_data

app = Flask(__name__)


@app.route("/")
def index():
    # Redirect to the '/profile' route
    return redirect(url_for("profile"))


@app.route("/profile")
def profile():
    # Use the profile_image and resume_pdf in this route
    return render_template(
        PROFILE_PAGE,
        profile_image=PROFILE_IMAGE,
        resume_pdf=RESUME_PDF,
        title="My Portfolio",
    )


@app.route("/gallery")
def gallery():
    with open(GALLERY_JSON_PATH) as f:
        gallery_data = json.load(f)

    page = request.args.get("page", 1, type=int)
    items_per_page = 6

    paginated_gallery_data, total_pages = paginate_data(
        gallery_data, page, items_per_page
    )

    return render_template(
        GALLERY_PAGE,
        image_path=IMAGE_PATH,
        gallery_data=paginated_gallery_data,
        current_page=page,
        total_pages=total_pages,
        title="My Gallery",
    )


@app.route("/vlog")
def vlog():
    with open(VLOG_JSON_PATH) as f:
        vlog_data = json.load(f)

    page = request.args.get("page", 1, type=int)
    items_per_page = 3

    paginated_vlog_data, total_pages = paginate_data(vlog_data, page, items_per_page)

    return render_template(
        VLOG_PAGE,
        vlogs=paginated_vlog_data,
        current_page=page,
        total_pages=total_pages,
        title="My Vlogs",
    )


@app.route("/concern")
def concern():
    return render_template(CONCERN_PAGE, title="My Concern")


# Custom error handler for 404 Not Found
@app.errorhandler(404)
def not_found(error):
    return render_template(ERROR_404_PAGE, title="Not Found", error=error), 404


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
