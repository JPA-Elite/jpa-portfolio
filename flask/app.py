from flask import Flask, render_template, send_from_directory # type: ignore
from config import (
    ERROR_404_PAGE,
    LANGUAGES,
    BABEL_DEFAULT_LOCALE,
    EN_LOCALE,
    CEB_LOCALE,
    TL_LOCALE,
    get_locale,
)
from flask_babel import Babel  # type: ignore
from pages import pages_bp 
from datetime import datetime
from sitemap import sitemap_bp  # Import the sitemap blueprint
import os

app = Flask(__name__)

app.config["LANGUAGES"] = LANGUAGES
app.config["BABEL_DEFAULT_LOCALE"] = BABEL_DEFAULT_LOCALE
app.register_blueprint(pages_bp)
# Register the sitemap blueprint
app.register_blueprint(sitemap_bp)

babel = Babel(app)
babel.init_app(app, locale_selector=get_locale)


@app.context_processor
def inject_locale():
    return dict(get_locale=get_locale)


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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
