from flask import render_template
from config import (
    ADMIN_DASHBOARD_PAGE,

)

# ************************** PAGES ********************************
def admin_dashboard_route():
    return render_template(ADMIN_DASHBOARD_PAGE, title="Admin Dashboard")
