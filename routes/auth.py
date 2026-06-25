import logging
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.supabase_client import supabase

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)

_ROLE_HOME = {
    "admin": "/admin",
    "melave": "/melave",
    "metapel": "/metapel",
    "lakoach": "/lakoach",
}

# Mock users for development when Supabase isn't configured.
_MOCK_USERS = {
    "admin@briah.co": {"id": "mock-admin", "role": "admin", "full_name": "איינב"},
    "melave@briah.co": {"id": "mock-melave", "role": "melave", "full_name": "מלווה דמה"},
    "metapel@briah.co": {"id": "mock-metapel", "role": "metapel", "full_name": "מטפל דמה"},
    "lakoach@briah.co": {"id": "mock-lakoach", "role": "lakoach", "full_name": "לקוח דמה"},
}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("יש להתחבר כדי להמשיך", "error")
            return redirect("/login")
        return view(*args, **kwargs)

    return wrapped


def get_current_user():
    return {
        "id": session.get("user_id"),
        "role": session.get("role"),
        "full_name": session.get("full_name"),
        "email": session.get("email"),
    }


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")
    user = None

    if supabase is not None:
        try:
            auth_result = supabase.auth.sign_in_with_password({"email": email, "password": password})
            user_row = (
                supabase.table("users")
                .select("id, full_name, role")
                .eq("id", auth_result.user.id)
                .single()
                .execute()
            )
            user = user_row.data
        except Exception:
            logger.exception("Supabase login failed for %s", email)

    if user is None and email in _MOCK_USERS:
        # Development fallback: any password accepted for the seeded mock emails.
        user = _MOCK_USERS[email]

    if user is None:
        flash("שם משתמש או סיסמה שגויים", "error")
        return redirect("/login")

    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["full_name"] = user["full_name"]
    session["email"] = email

    return redirect(_ROLE_HOME.get(user["role"], "/login"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
