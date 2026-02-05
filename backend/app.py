from flask import Flask, render_template, request, send_from_directory # type: ignore
from backend.configurations import (
    ERROR_404_PAGE,
    LANGUAGES,
    BABEL_DEFAULT_LOCALE,
    EN_LOCALE,
    CEB_LOCALE,
    TL_LOCALE,
    get_locale,
)
from flask_babel import Babel  # type: ignore
from backend.pages import pages_bp
from backend.api import api_bp
from datetime import datetime, timedelta
from backend.sitemap import sitemap_bp  # Import the sitemap blueprint
import os
from backend.extensions import cache
from backend.constants.app_defaults import SECURITY_HEADERS
from dotenv import load_dotenv


def _is_truthy(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv('SECRET_KEY')
app.config["LANGUAGES"] = LANGUAGES
app.config["BABEL_DEFAULT_LOCALE"] = BABEL_DEFAULT_LOCALE

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

# ✅ Configure cache globally
app.config["CACHE_TYPE"] = "simple"
app.config["CACHE_DEFAULT_TIMEOUT"] = 86400

app.register_blueprint(pages_bp)
app.register_blueprint(sitemap_bp)
app.register_blueprint(api_bp)


# ✅ Initialize cache
cache.init_app(app)

# ✅ Initialize Babel
babel = Babel(app)
babel.init_app(app, locale_selector=get_locale)


@app.context_processor
def inject_locale():
    return dict(get_locale=get_locale)

@app.after_request
def apply_security_headers(response):
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)

    # Cache static assets more aggressively in non-debug mode
    if not app.debug and request.path.startswith("/static/"):
        response.headers.setdefault("Cache-Control", "public, max-age=31536000, immutable")

    return response


@app.context_processor
def inject_hcaptcha():
    return dict(HCAPTCHA_SITE_KEY=os.getenv("HCAPTCHA_SITE_KEY"))


# ************************** LOCALE CONTANTS ********************************

@app.context_processor
def en_locale():
    return dict(en_locale=EN_LOCALE)


@app.context_processor
def ceb_locale():
    return dict(ceb_locale=CEB_LOCALE)


@app.context_processor
def tl_locale():
    return dict(tl_locale=TL_LOCALE)

@app.context_processor
def inject_now():
    return dict(now=datetime.now())

@app.errorhandler(404)
def not_found(error):
    return render_template(ERROR_404_PAGE, title="Not Found", error=error), 404

@app.route('/robots.txt')
def robots():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'robots.txt')


@app.template_filter()
def truncate_text(text, length=120):
    if text and len(text) > length:
        return text[:length] + " ..."
    return text

if __name__ == "__main__":
    debug = _is_truthy(os.getenv("FLASK_DEBUG", "1"))
    app.run(host="0.0.0.0", debug=debug, use_reloader=debug)
