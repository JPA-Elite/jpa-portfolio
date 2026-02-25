from flask import Flask, render_template, send_from_directory # type: ignore
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
from backend.security import init_ddos_guard
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv('SECRET_KEY')
app.config["LANGUAGES"] = LANGUAGES
app.config["BABEL_DEFAULT_LOCALE"] = BABEL_DEFAULT_LOCALE

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

# ✅ Configure cache globally
app.config["CACHE_TYPE"] = os.getenv("CACHE_TYPE", "simple")
try:
    app.config["CACHE_DEFAULT_TIMEOUT"] = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "86400"))
except (TypeError, ValueError):
    app.config["CACHE_DEFAULT_TIMEOUT"] = 86400

cache_redis_url = os.getenv("CACHE_REDIS_URL")
if cache_redis_url:
    app.config["CACHE_REDIS_URL"] = cache_redis_url

cache_key_prefix = os.getenv("CACHE_KEY_PREFIX")
if cache_key_prefix:
    app.config["CACHE_KEY_PREFIX"] = cache_key_prefix

app.register_blueprint(pages_bp)
app.register_blueprint(sitemap_bp)
app.register_blueprint(api_bp)


# ✅ Initialize cache
cache.init_app(app)

# ✅ App-level abuse throttling / basic DDoS guard (best-effort; edge protection still required)
init_ddos_guard(app)

# ✅ Initialize Babel
babel = Babel(app)
babel.init_app(app, locale_selector=get_locale)

@app.after_request
@app.after_request
def remove_csp(response):
    response.headers.pop("Content-Security-Policy", None)
    return response

@app.context_processor
def inject_locale():
    return dict(get_locale=get_locale)

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
    app.run(debug=True, host="0.0.0.0")
