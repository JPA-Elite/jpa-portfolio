from flask import Flask, render_template # type: ignore
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

app = Flask(__name__)

app.config["LANGUAGES"] = LANGUAGES
app.config["BABEL_DEFAULT_LOCALE"] = BABEL_DEFAULT_LOCALE
app.register_blueprint(pages_bp)


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


@app.errorhandler(404)
def not_found(error):
    return render_template(ERROR_404_PAGE, title="Not Found", error=error), 404


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
