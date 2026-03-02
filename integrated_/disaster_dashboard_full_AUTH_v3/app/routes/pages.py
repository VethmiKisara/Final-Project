from flask import Blueprint, redirect, render_template, session, url_for

from .utils import login_required

pages_bp = Blueprint("pages", __name__)


@pages_bp.get("/")
def index():
    # First thing user sees is Login page.
    if session.get("user_id"):
        return redirect(url_for("pages.dashboard"))
    return redirect(url_for("auth.login"))


@pages_bp.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")


@pages_bp.get("/alerts")
@login_required
def alert_logs():
    return render_template("alert_logs.html", active_page="alerts")
