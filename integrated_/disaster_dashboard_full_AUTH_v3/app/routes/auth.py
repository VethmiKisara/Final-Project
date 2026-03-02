import re
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash

from ..db import get_db_session


auth_bp = Blueprint("auth", __name__)

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _is_valid_email(email: str) -> bool:
    return bool(email and _EMAIL_RE.match(email))


def _get_user_by_email(db, email: str):
    return (
        db.execute(
            text("SELECT id, username, email, password_hash FROM users WHERE email = :email"),
            {"email": email},
        )
        .mappings()
        .first()
    )


@auth_bp.get("/login")
def login():
    if session.get("user_id"):
        return redirect(url_for("pages.dashboard"))
    return render_template("login.html", title="Login")


@auth_bp.post("/login")
def login_post():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    if not email or not password:
        flash("Email and password are required.", "error")
        return redirect(url_for("auth.login"))

    db = get_db_session()
    try:
        user = _get_user_by_email(db, email)
        if not user:
            flash("No account found for that email.", "error")
            return redirect(url_for("auth.login"))

        stored = user["password_hash"] or ""
        ok = False
        try:
            ok = check_password_hash(stored, password)
        except Exception:
            ok = False
        # fallback for legacy/plain-text (not recommended, but helps if old data exists)
        if not ok and stored == password:
            ok = True

        if not ok:
            flash("Incorrect password.", "error")
            return redirect(url_for("auth.login"))

        session.clear()
        session["user_id"] = int(user["id"])
        session["username"] = user["username"]
        session["email"] = user["email"]
        flash("Logged in successfully.", "success")

        nxt = request.args.get("next")
        return redirect(nxt or url_for("pages.dashboard"))
    finally:
        db.close()


@auth_bp.get("/signup")
def signup():
    if session.get("user_id"):
        return redirect(url_for("pages.dashboard"))
    return render_template("signup.html", title="Sign Up")


@auth_bp.post("/signup")
def signup_post():
    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    if not username or not email or not password:
        flash("All fields are required.", "error")
        return redirect(url_for("auth.signup"))

    if not _is_valid_email(email):
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("auth.signup"))

    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("auth.signup"))

    db = get_db_session()
    try:
        # username uniqueness check (schema doesn't enforce it)
        existing_u = db.execute(
            text("SELECT id FROM users WHERE username = :u LIMIT 1"), {"u": username}
        ).first()
        if existing_u:
            flash("That username is already taken.", "error")
            return redirect(url_for("auth.signup"))

        existing_e = db.execute(
            text("SELECT id FROM users WHERE email = :e LIMIT 1"), {"e": email}
        ).first()
        if existing_e:
            flash("An account with that email already exists.", "error")
            return redirect(url_for("auth.signup"))

        pw_hash = generate_password_hash(password)
        db.execute(
            text(
                "INSERT INTO users (username, email, password_hash) VALUES (:u, :e, :p)"
            ),
            {"u": username, "e": email, "p": pw_hash},
        )
        db.commit()

        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))
    finally:
        db.close()


@auth_bp.get("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.get("/forgot")
def forgot_password():
    return render_template("forgot_password.html", title="Forgot Password")


@auth_bp.post("/forgot")
def forgot_password_post():
    email = (request.form.get("email") or "").strip().lower()
    if not _is_valid_email(email):
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("auth.forgot_password"))

    db = get_db_session()
    try:
        user = _get_user_by_email(db, email)
        if not user:
            # Do not reveal too much; but user asked for relevant messages.
            flash("No account found for that email.", "error")
            return redirect(url_for("auth.forgot_password"))

        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)

        db.execute(
            text(
                "INSERT INTO password_reset_tokens (user_id, token, expires_at, used_at) "
                "VALUES (:uid, :tok, :exp, NULL)"
            ),
            {"uid": int(user["id"]), "tok": token, "exp": expires_at},
        )
        db.commit()

        reset_link = url_for("auth.reset_password", token=token, _external=True)
        # Email sending isn't configured in this project. Show the link for dev use.
        flash(
            "Password reset link generated (email sending not configured). Use this link: "
            + reset_link,
            "info",
        )
        return redirect(url_for("auth.login"))
    finally:
        db.close()


@auth_bp.get("/reset/<token>")
def reset_password(token):
    return render_template("reset_password.html", title="Reset Password", token=token)


@auth_bp.post("/reset/<token>")
def reset_password_post(token):
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm_password") or ""

    if not password or not confirm:
        flash("Both password fields are required.", "error")
        return redirect(url_for("auth.reset_password", token=token))

    if password != confirm:
        flash("Passwords do not match.", "error")
        return redirect(url_for("auth.reset_password", token=token))

    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("auth.reset_password", token=token))

    db = get_db_session()
    try:
        row = (
            db.execute(
                text(
                    "SELECT id, user_id, expires_at, used_at "
                    "FROM password_reset_tokens WHERE token = :t"
                ),
                {"t": token},
            )
            .mappings()
            .first()
        )

        if not row:
            flash("Invalid reset token.", "error")
            return redirect(url_for("auth.login"))

        if row["used_at"] is not None:
            flash("This reset link has already been used.", "error")
            return redirect(url_for("auth.login"))

        # expires_at is stored without timezone; compare with UTC-ish now.
        if row["expires_at"] and datetime.utcnow() > row["expires_at"]:
            flash("This reset link has expired. Please request a new one.", "error")
            return redirect(url_for("auth.forgot_password"))

        pw_hash = generate_password_hash(password)
        db.execute(
            text("UPDATE users SET password_hash = :p WHERE id = :uid"),
            {"p": pw_hash, "uid": int(row["user_id"])},
        )
        db.execute(
            text("UPDATE password_reset_tokens SET used_at = NOW() WHERE id = :id"),
            {"id": int(row["id"])},
        )
        db.commit()

        flash("Password updated. Please log in.", "success")
        return redirect(url_for("auth.login"))
    finally:
        db.close()
