from flask import redirect, url_for, request, jsonify
from Services.PortfolioService import PortfolioService
from Services.VisitService import VisitService
from Repositories.PortfolioRepository import PortfolioRepository
from Repositories.VisitRepository import VisitRepository
from flask_babel import gettext

# Initialize Services
portfolio_service = PortfolioService(repository=PortfolioRepository())
visit_service = VisitService(repository=VisitRepository())

# ************************** API Controller ********************************

def change_language_route(lang_code = ""):
    referrer_url = request.referrer if request.referrer else url_for("index")

    response = redirect(
        f"{referrer_url.split('?')[0]}?search="
    )
    response.set_cookie("lang", lang_code)
    return response


def add_portfolio_route():
    data = {
        "name": request.form.get("name"),
        "email": request.form.get("email"),
    }

    try:
        portfolio_service.add_portfolio(data["name"], data["email"])
        return jsonify({"message": "Data inserted successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def delete_page_system_info_route():
    """Delete only the records displayed on the current page."""
    data = request.json
    records = data.get("records", [])

    result = visit_service.delete_page_system_info(records)
    return jsonify(result)

def profile_config_route():
    qa_data = [
        { "question": gettext("qa_name"), "answer": gettext("qa_name_answer") },
        { "question": gettext("qa_age"), "answer": gettext("qa_age_answer") },
        { "question": gettext("qa_job"), "answer": gettext("qa_job_answer") },
        { "question": gettext("qa_favorite_sport"), "answer": gettext("qa_favorite_sport_answer") },
        # { "question": gettext("qa_crush"), "answer": gettext("qa_crush_answer") },
        { "question": gettext("qa_favorite_subject"), "answer": gettext("qa_favorite_subject_answer") },
        { "question": gettext("qa_live"), "answer": gettext("qa_live_answer") },
        { "question": gettext("qa_dream_job"), "answer": gettext("qa_dream_job_answer") },
        { "question": gettext("qa_type_of_person"), "answer": gettext("qa_type_of_person_answer") },
        { "question": gettext("qa_nickname"), "answer": gettext("qa_nickname_answer") },
        # { "question": gettext("qa_behaviour"), "answer": gettext("qa_behaviour_answer") },
        # { "question": gettext("qa_song"), "answer": gettext("qa_song_answer") }
    ]
    
    return jsonify({
        'qaData': qa_data
    })

