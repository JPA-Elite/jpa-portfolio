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
    LANGUAGES,
    BABEL_DEFAULT_LOCALE,
    EN_LOCALE,
    CEB_LOCALE
)
from utils import paginate_data
from flask_babel import Babel, gettext  # type: ignore
from markupsafe import escape # type: ignore

app = Flask(__name__)

# Configure Flask-Babel
app.config["LANGUAGES"] = LANGUAGES
app.config["BABEL_DEFAULT_LOCALE"] = BABEL_DEFAULT_LOCALE


def get_locale():
    lang = request.cookies.get("lang") or request.accept_languages.best_match(
        LANGUAGES.keys()
    )
    return lang


# Initialize Flask-Babel
babel = Babel(app)
babel.init_app(app, locale_selector=get_locale)


@app.context_processor
def inject_locale():
    return dict(get_locale=get_locale)

# locale constants
@app.context_processor
def en_locale():
    return dict(en_locale=EN_LOCALE)

@app.context_processor
def ceb_locale():
    return dict(ceb_locale=CEB_LOCALE)

@app.route("/")
def index():
    return redirect(url_for("profile"))


@app.route("/change_language/<lang_code>")
def change_language(lang_code):
    referrer = request.referrer or url_for("index")
    response = redirect(referrer)
    response.set_cookie("lang", lang_code)
    return response


@app.route("/profile")
def profile():
    # Retrieve translations
    profile_name = gettext("profile_name")
    profile_intro = gettext("profile_intro")
    profile_age = gettext("profile_age")
    profile_introvert = gettext("profile_introvert")
    profile_job = gettext("profile_job")
    profile_goals = gettext("profile_goals")
    # Construct profile_desc with proper escaping
    profile_desc = f"{escape(profile_intro)} {escape(profile_age)}<br>{escape(profile_introvert)}<br>{escape(profile_job)} {escape(profile_goals)}"

    return render_template(
        PROFILE_PAGE,
        profile_image=PROFILE_IMAGE,
        resume_pdf=RESUME_PDF,
        title="My Portfolio",
        profile_name=profile_name,
        profile_desc=profile_desc,
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
