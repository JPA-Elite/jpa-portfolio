from flask import render_template
from config import (
    ADMIN_CHAT_PAGE,
    ADMIN_DASHBOARD_PAGE,
    ADMIN_MUSIC_PAGE,
    ADMIN_PROJECT_PAGE,
    ADMIN_SETTINGS_PAGE,
    ADMIN_VIDEO_PAGE,

)

# ************************** PAGES ********************************
def admin_dashboard_route():
    return render_template(ADMIN_DASHBOARD_PAGE, title="Admin Dashboard")

def admin_chat_route():
    return render_template(ADMIN_CHAT_PAGE, title="Admin Chat")

def admin_video_route():
    return render_template(ADMIN_VIDEO_PAGE, title="Admin Video")

def admin_music_route():
    return render_template(ADMIN_MUSIC_PAGE, title="Admin Music")

def admin_project_route():
    return render_template(ADMIN_PROJECT_PAGE, title="Admin Project")

def admin_settings_route():
    return render_template(ADMIN_SETTINGS_PAGE, title="Admin Settings")