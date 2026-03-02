from functools import wraps

from flask import flash, redirect, request, session, url_for


def login_required(view_fn):
    """Simple session-based auth guard for page routes."""

    @wraps(view_fn)
    def _wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view_fn(*args, **kwargs)

    return _wrapped
