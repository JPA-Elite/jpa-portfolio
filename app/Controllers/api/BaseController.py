from flask import redirect, stream_with_context, url_for, request, jsonify, Response
import requests
from app.Services.PortfolioService import PortfolioService
from app.Services.VisitService import VisitService
from app.Repositories.PortfolioRepository import PortfolioRepository
from app.Repositories.VisitRepository import VisitRepository
from app.Services.MusicService import MusicService
from app.Repositories.MusicRepository import MusicRepository
from flask_babel import gettext
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from app.Requests.api.BaseControllerRequest import BaseControllerRequest
from app.utils import safe_filename_parts, stream_generator

# Initialize Services
portfolio_service = PortfolioService(repository=PortfolioRepository())
visit_service = VisitService(repository=VisitRepository())
music_service = MusicService(repository=MusicRepository())

# ************************** API Controller ********************************

def change_language_route(lang_code=""):
    form = BaseControllerRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

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
    form = BaseControllerRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    records = data["records"]

    result = visit_service.delete_page_system_info(records)
    return jsonify(result)

def profile_config_route():
    qa_data = [
        { "question": gettext("qa_name"), "answer": gettext("qa_name_answer") },
        { "question": gettext("qa_age"), "answer": gettext("qa_age_answer") },
        { "question": gettext("qa_job"), "answer": gettext("qa_job_answer") },
        { "question": gettext("qa_favorite_sport"), "answer": gettext("qa_favorite_sport_answer") },
        { "question": gettext("qa_favorite_subject"), "answer": gettext("qa_favorite_subject_answer") },
        { "question": gettext("qa_live"), "answer": gettext("qa_live_answer") },
        { "question": gettext("qa_dream_job"), "answer": gettext("qa_dream_job_answer") },
        { "question": gettext("qa_type_of_person"), "answer": gettext("qa_type_of_person_answer") },
        { "question": gettext("qa_nickname"), "answer": gettext("qa_nickname_answer") },
        { "question": gettext("qa_favorite_programming_language"), "answer": gettext("qa_favorite_programming_language_answer") },
    ]

    return jsonify({
        'qaData': qa_data
    })

def download_song_route():
    form = BaseControllerRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    url = data["url"]
    music = music_service.get_music_by_url(url)

    if music:
        title = music.get("title", "Unknown")
        artist = music.get("artist", "Unknown")
    else:
        title = "download"
        artist = ""

    fallback_base, utf8_quoted_base = safe_filename_parts(title, artist)
    fallback_name = f"{fallback_base}.mp3"
    utf8_name = f"{utf8_quoted_base}.mp3"

    r = requests.get(url, stream=True, timeout=30)
    if r.status_code != 200:
        return {"error": "Failed to download file"}, 500

    content_type = r.headers.get("Content-Type", "application/octet-stream")

    content_disposition = (
        f'attachment; filename="{fallback_name}"; filename*=UTF-8\'\'{utf8_name}'
    )

    headers = {
        "Content-Disposition": content_disposition,
        "Content-Type": content_type,
    }

    return Response(
        stream_generator(r),
        headers=headers
    )

def get_client_ip_route():
    form = BaseControllerRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    return jsonify({"ip": client_ip})

def proxy_audio_route():
    form = BaseControllerRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    url = data["url"]
    range_header = data["range_header"]
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

