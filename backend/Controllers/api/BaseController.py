from flask import redirect, stream_with_context, url_for, request, jsonify, Response
import requests
from backend.Services.PortfolioService import PortfolioService
from backend.Services.VisitService import VisitService
from backend.Repositories.PortfolioRepository import PortfolioRepository
from backend.Repositories.VisitRepository import VisitRepository
from flask_babel import gettext
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Initialize Services
portfolio_service = PortfolioService(repository=PortfolioRepository())
visit_service = VisitService(repository=VisitRepository())

# ************************** API Controller ********************************

def change_language_route(lang_code=""):
    referrer_url = request.referrer or url_for("index")

    parsed = urlparse(referrer_url)
    params = parse_qs(parsed.query)

    params.pop("search", None)

    final_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        urlencode(params, doseq=True),
        parsed.fragment
    ))

    response = redirect(final_url)
    response.set_cookie("lang", lang_code)
    return response

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

def download_song_route():
    url = request.args.get('url')
    filename = url.split('/')[-1]
    r = requests.get(url, stream=True)
    return Response(
        r.iter_content(chunk_size=8192),
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": r.headers.get("Content-Type", "audio/mpeg")
        }
    )

def get_client_ip_route():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    return jsonify({"ip": client_ip})

def proxy_audio_route():
    url = request.args.get("url")
    range_header = request.headers.get('Range', None)
    headers = {}

    if range_header:
        headers['Range'] = range_header

    resp = requests.get(url, headers=headers, stream=True)

    def generate():
        for chunk in resp.iter_content(chunk_size=4096):
            if chunk:
                yield chunk

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    response_headers = [
        (name, value) for (name, value) in resp.raw.headers.items()
        if name.lower() not in excluded_headers
    ]

    return Response(
        stream_with_context(generate()),
        status=resp.status_code,
        headers=response_headers,
    )
