# pages.py
from flask import Blueprint, redirect, url_for, render_template, request, jsonify
from Services.PortfolioService import PortfolioService
from Services.VisitService import VisitService
from utils import filter_data, paginate_data
from config import (
    ADD_PORTFOLIO_PAGE,
    CONCERN_PAGE,
    GALLERY_JSON_PATH,
    GALLERY_PAGE,
    IMAGE_PATH,
    PROFILE_IMAGE,
    PROFILE_PAGE,
    RESUME_PDF,
    VLOG_JSON_PATH,
    VLOG_PAGE,
    DEVICE_INFO_VISIT_PAGE,
    get_locale,
)
from flask_babel import gettext  # type: ignore
from markupsafe import escape  # type: ignore
import requests

# Create a Blueprint for pages
pages_bp = Blueprint("pages", __name__)

# Initialize Services
portfolio_service = PortfolioService()
visit_service = VisitService()

# ************************** PAGES ********************************


@pages_bp.route("/")
def index():
    return handle_log_parameter() or redirect(url_for("pages.profile"))


@pages_bp.route("/profile")
def profile():
    # Retrieve translations
    profile_name = gettext("profile_name")
    profile_intro = gettext("profile_intro")
    profile_age = gettext("profile_age")
    profile_introvert = gettext("profile_introvert")
    profile_job = gettext("profile_job")
    profile_goals = gettext("profile_goals")
    profile_desc = f"{escape(profile_intro)} {escape(profile_age)}<br>{escape(profile_introvert)}<br>{escape(profile_job)} {escape(profile_goals)}"

    # project details
    project_jaom = url_for("static", filename="images/jaom.png", _external=True)

    return handle_log_parameter() or render_template(
        PROFILE_PAGE,
        profile_image=PROFILE_IMAGE,
        resume_pdf=RESUME_PDF,
        title="My Portfolio",
        profile_name=profile_name,
        profile_desc=profile_desc,
        project_jaom=project_jaom,
    )


@pages_bp.route("/gallery")
def gallery():
    # Generate the dynamic URL for the gallery JSON
    gallery_url = url_for("static", filename="json/gallery.json", _external=True)

    # Fetch JSON data from the URL
    response = requests.get(gallery_url)
    gallery_data = response.json()

    # Get the search query from the request arguments
    search_query = request.args.get("search", "")
    # Filter the gallery data using the generalized function
    filtered_gallery_data = filter_data(gallery_data, get_locale(), search_query)

    # Paginate the filtered data
    page = request.args.get("page", 1, type=int)
    items_per_page = 6
    paginated_gallery_data, total_pages = paginate_data(
        filtered_gallery_data, page, items_per_page
    )

    return handle_log_parameter() or render_template(
        GALLERY_PAGE,
        image_path=IMAGE_PATH,
        gallery_data=paginated_gallery_data,
        current_page=page,
        total_pages=total_pages,
        title="My Gallery",
        search_query=search_query,
    )


@pages_bp.route("/vlog")
def vlog():
    # Generate the dynamic URL for the vlog JSON
    vlog_url = url_for("static", filename="json/vlog.json", _external=True)

    # Fetch JSON data from the URL
    response = requests.get(vlog_url)
    vlog_data = response.json()

    # Get the search query from the request arguments
    search_query = request.args.get("search", "")
    # Filter the vlog data using the generalized function
    filtered_vlog_data = filter_data(vlog_data, get_locale(), search_query)

    # Paginate the filtered data
    page = request.args.get("page", 1, type=int)
    items_per_page = 3
    paginated_vlog_data, total_pages = paginate_data(
        filtered_vlog_data, page, items_per_page
    )

    return handle_log_parameter() or render_template(
        VLOG_PAGE,
        vlogs=paginated_vlog_data,
        current_page=page,
        total_pages=total_pages,
        title="My Vlogs",
        search_query=search_query,
    )


@pages_bp.route("/concern")
def concern():
    return handle_log_parameter() or render_template(CONCERN_PAGE, title="My Concern")


@pages_bp.route("/change_language/<lang_code>")
def change_language(lang_code):
    # Parse the referrer URL to remove any existing search query
    referrer_url = request.referrer if request.referrer else url_for("index")

    # Redirect to the referrer URL while clearing the search query
    response = redirect(
        f"{referrer_url.split('?')[0]}?search="
    )  # Set search query to empty
    response.set_cookie("lang", lang_code)
    return response


# Route to render the form
@pages_bp.route("/add_portfolio_form")
def add_portfolio_form():
    return handle_log_parameter() or render_template(ADD_PORTFOLIO_PAGE)


@pages_bp.route("/add_portfolio", methods=["POST"])
def add_portfolio():
    data = {
        "name": request.form.get("name"),
        "email": request.form.get("email"),
    }

    try:
        portfolio_service.add_portfolio(data["name"], data["email"])
        return jsonify({"message": "Data inserted successfully!"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@pages_bp.route("/device-info/visits")
def device_info():
    page = int(request.args.get("page", 1))
    per_page = 10
    documents, total_docs = visit_service.get_paginated_system_info(page, per_page)
    total_pages = (total_docs + per_page - 1) // per_page  # Calculate total pages

    return handle_log_parameter() or render_template(
        DEVICE_INFO_VISIT_PAGE,
        documents=[doc.to_dict() for doc in documents],
        current_page=page,
        total_pages=total_pages,
        title="User Visits",
    )


# ************************** PRIVATE FUNCTIONS ********************************
def handle_log_parameter():
    log_query = request.args.get("log", "").lower()

    if log_query == "true":
        result = portfolio_service.add_system_info()
        print(result)
        return redirect(url_for(request.endpoint))

    return None
