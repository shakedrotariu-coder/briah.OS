import logging
from datetime import date
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session

from routes.auth import login_required
from services.supabase_client import supabase

metapel_bp = Blueprint("metapel", __name__, url_prefix="/metapel")
logger = logging.getLogger(__name__)

_MOCK_LAKOCHIM = [
    {"id": "1", "full_name": "נועה כהן", "next_session": "2026-06-25", "needs_summary": True},
]
_MOCK_SESSIONS = [
    {"scheduled_at": "2026-06-25 10:00", "lakoach_name": "נועה כהן", "status": "מתוכנן"},
]


def _metapel_only(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "metapel":
            flash("גישה רק למטפלים", "error")
            return redirect("/login")
        return view(*args, **kwargs)

    return wrapped


@metapel_bp.route("")
@login_required
@_metapel_only
def dashboard():
    lakochim = _MOCK_LAKOCHIM
    upcoming_sessions = _MOCK_SESSIONS

    if supabase is not None:
        try:
            lakochim = (
                supabase.table("lakoach_profiles")
                .select("*, users(full_name)")
                .eq("metapel_id", session.get("user_id"))
                .execute()
                .data
            )
            upcoming_sessions = (
                supabase.table("sessions")
                .select("*")
                .eq("metapel_id", session.get("user_id"))
                .execute()
                .data
            )
        except Exception:
            logger.exception("Failed to load metapel dashboard, using mock data")

    return render_template("metapel/dashboard.html", lakochim=lakochim, upcoming_sessions=upcoming_sessions)


@metapel_bp.route("/lakoach/<lakoach_id>")
@login_required
@_metapel_only
def lakoach_profile(lakoach_id):
    lakoach = {"id": lakoach_id, "full_name": "נועה כהן"}
    degashim = ["זקוקה לקרקוע", "רגישות גבוהה למגע"]
    tochnit_row = None
    sessions = _MOCK_SESSIONS

    if supabase is not None:
        try:
            lakoach = supabase.table("users").select("id, full_name").eq("id", lakoach_id).single().execute().data
            intake_res = supabase.table("intakes").select("raw_summary").eq("lakoach_id", lakoach_id).execute()
            if intake_res.data:
                degashim = intake_res.data[0].get("raw_summary", {}).get("degashim", [])
            tochnit_res = supabase.table("tochniyot_ishiyot").select("*").eq("lakoach_id", lakoach_id).execute()
            tochnit_row = tochnit_res.data[0] if tochnit_res.data else None
            sessions = supabase.table("sessions").select("*").eq("lakoach_id", lakoach_id).execute().data
        except Exception:
            logger.exception("Failed to load lakoach profile %s", lakoach_id)

    return render_template(
        "metapel/lakoach.html",
        lakoach=lakoach,
        degashim=degashim,
        tochnit=tochnit_row,
        sessions=sessions,
    )


@metapel_bp.route("/sikum/<lakoach_id>", methods=["GET"])
@login_required
@_metapel_only
def sikum(lakoach_id):
    lakoach = {"id": lakoach_id, "full_name": "נועה כהן"}
    session_number = 1

    if supabase is not None:
        try:
            lakoach = supabase.table("users").select("id, full_name").eq("id", lakoach_id).single().execute().data
            count_res = supabase.table("sessions").select("id").eq("lakoach_id", lakoach_id).execute()
            session_number = len(count_res.data) + 1
        except Exception:
            logger.exception("Failed to load sikum form data for %s", lakoach_id)

    return render_template(
        "metapel/sikum.html",
        lakoach=lakoach,
        session_number=session_number,
        today=date.today().isoformat(),
    )


@metapel_bp.route("/sikum/<lakoach_id>", methods=["POST"])
@login_required
@_metapel_only
def save_sikum(lakoach_id):
    sikum_text = request.form.get("sikum")
    if not sikum_text:
        flash("יש להזין סיכום קצר", "error")
        return redirect(f"/metapel/sikum/{lakoach_id}")

    if supabase is not None:
        try:
            supabase.table("sessions").insert({
                "lakoach_id": lakoach_id,
                "metapel_id": session.get("user_id"),
                "scheduled_at": request.form.get("session_date"),
                "sikum": sikum_text,
                "degashim": ", ".join(request.form.getlist("degashim")),
                "status": "completed",
            }).execute()
        except Exception:
            logger.exception("Failed to save sikum for %s", lakoach_id)
            flash("שמירת הסיכום נכשלה", "error")
            return redirect(f"/metapel/sikum/{lakoach_id}")

    flash("הסיכום נשמר", "success")
    return redirect(f"/metapel/lakoach/{lakoach_id}")
