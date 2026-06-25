import datetime
import logging
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.supabase_client import supabase

metapel_bp = Blueprint("metapel", __name__)
logger = logging.getLogger(__name__)

_MOCK_LAKOCHIM = [
    {"id": "1", "full_name": "נועה כהן", "next_session": "2026-06-25 10:00", "needs_summary": True},
]
_MOCK_SESSIONS_WEEK = [
    {"scheduled_at": "2026-06-25 10:00", "lakoach_name": "נועה כהן", "status": "מתוכנן"},
]


def require_metapel(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session or session.get("role") not in ("metapel", "admin"):
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def _enrich_lakoach(profile_row):
    """Takes a lakoach_profiles row (with joined users data) and returns a clean dict for templates."""
    user = profile_row.get("users") or {}
    return {
        "id": user.get("id", ""),
        "full_name": user.get("full_name", "לא ידוע"),
        "email": user.get("email", ""),
        "phone": user.get("phone", ""),
        "mashlul": profile_row.get("mashlul", ""),
        "start_date": profile_row.get("start_date", ""),
        "profile_id": profile_row.get("id", ""),
    }


@metapel_bp.route("/metapel")
@require_metapel
def dashboard():
    lakochim = _MOCK_LAKOCHIM
    upcoming_sessions = _MOCK_SESSIONS_WEEK

    if supabase is not None:
        uid = session["user_id"]
        try:
            profiles = (
                supabase.table("lakoach_profiles")
                .select("*, users!lakoach_profiles_user_id_fkey(*)")
                .eq("metapel_id", uid)
                .execute()
                .data
                or []
            )

            lakochim = []
            for p in profiles:
                lk = _enrich_lakoach(p)

                ns = (
                    supabase.table("sessions")
                    .select("scheduled_at")
                    .eq("lakoach_id", lk["id"])
                    .eq("metapel_id", uid)
                    .eq("status", "scheduled")
                    .gte("scheduled_at", datetime.datetime.now().isoformat())
                    .order("scheduled_at")
                    .limit(1)
                    .execute()
                    .data
                )
                lk["next_session"] = ns[0]["scheduled_at"][:16].replace("T", " ") if ns else None

                needs = (
                    supabase.table("sessions")
                    .select("id")
                    .eq("lakoach_id", lk["id"])
                    .eq("metapel_id", uid)
                    .eq("status", "completed")
                    .is_("sikum", "null")
                    .limit(1)
                    .execute()
                    .data
                )
                lk["needs_summary"] = bool(needs)

                lakochim.append(lk)

            now = datetime.datetime.now()
            week_start = (now - datetime.timedelta(days=now.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            ).isoformat()
            week_end = (now + datetime.timedelta(days=7)).isoformat()

            sessions_week = (
                supabase.table("sessions")
                .select("*")
                .eq("metapel_id", uid)
                .gte("scheduled_at", week_start)
                .lte("scheduled_at", week_end)
                .order("scheduled_at")
                .execute()
                .data
                or []
            )

            upcoming_sessions = []
            for s in sessions_week:
                lk_user = (
                    supabase.table("users").select("full_name").eq("id", s.get("lakoach_id", "")).single().execute().data
                )
                upcoming_sessions.append({
                    **s,
                    "lakoach_name": lk_user.get("full_name", "") if lk_user else "—",
                })
        except Exception:
            logger.exception("Failed to load metapel dashboard, using mock data")
            lakochim, upcoming_sessions = _MOCK_LAKOCHIM, _MOCK_SESSIONS_WEEK

    return render_template(
        "metapel/dashboard.html",
        lakochim=lakochim,
        upcoming_sessions=upcoming_sessions,
    )


@metapel_bp.route("/metapel/lakoach/<lakoach_id>")
@require_metapel
def lakoach_profile(lakoach_id):
    lakoach = {"id": lakoach_id, "full_name": "נועה כהן"}
    tochnit_row = None
    degashim = ["זקוקה לקרקוע", "רגישות גבוהה למגע"]
    sessions = _MOCK_SESSIONS_WEEK

    if supabase is not None:
        try:
            lakoach = supabase.table("users").select("*").eq("id", lakoach_id).single().execute().data or lakoach

            intake_res = (
                supabase.table("intakes")
                .select("*")
                .eq("lakoach_id", lakoach_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
                .data
            )
            intake_row = intake_res[0] if intake_res else None

            tochnit_res = (
                supabase.table("tochniyot_ishiyot")
                .select("*")
                .eq("lakoach_id", lakoach_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
                .data
            )
            tochnit_row = tochnit_res[0] if tochnit_res else None

            degashim = []
            if intake_row:
                raw = intake_row.get("raw_summary") or {}
                if isinstance(raw, dict):
                    degashim = raw.get("degashim_letzevet", [])
                elif isinstance(raw, list):
                    degashim = raw

            sessions_raw = (
                supabase.table("sessions")
                .select("*")
                .eq("lakoach_id", lakoach_id)
                .order("scheduled_at")
                .execute()
                .data
                or []
            )
            sessions = [
                {**s, "session_number": i, "date_display": s["scheduled_at"][:10] if s.get("scheduled_at") else "—"}
                for i, s in enumerate(sessions_raw, 1)
            ]
        except Exception:
            logger.exception("Failed to load metapel lakoach profile for %s", lakoach_id)
            flash("שגיאה בטעינת הפרופיל", "error")
            return redirect(url_for("metapel.dashboard"))

    return render_template(
        "metapel/lakoach.html",
        lakoach=lakoach,
        degashim=degashim,
        tochnit=tochnit_row,
        sessions=sessions,
    )


@metapel_bp.route("/metapel/sikum/<lakoach_id>", methods=["GET"])
@require_metapel
def sikum(lakoach_id):
    lakoach = {"id": lakoach_id, "full_name": "נועה כהן"}
    session_number = 1

    if supabase is not None:
        try:
            lakoach = supabase.table("users").select("*").eq("id", lakoach_id).single().execute().data or lakoach
            count_res = (
                supabase.table("sessions")
                .select("id")
                .eq("lakoach_id", lakoach_id)
                .eq("metapel_id", session["user_id"])
                .execute()
                .data
            )
            session_number = len(count_res) + 1
        except Exception:
            logger.exception("Failed to load sikum form data for %s", lakoach_id)

    return render_template(
        "metapel/sikum.html",
        lakoach=lakoach,
        session_number=session_number,
        today=datetime.date.today().isoformat(),
    )


@metapel_bp.route("/metapel/sikum/<lakoach_id>", methods=["POST"])
@require_metapel
def save_sikum(lakoach_id):
    sikum_text = request.form.get("sikum")
    if not sikum_text:
        flash("יש להזין סיכום קצר", "error")
        return redirect(url_for("metapel.sikum", lakoach_id=lakoach_id))

    degashim_selected = request.form.getlist("degashim")
    degash_extra = request.form.get("degash_extra", "").strip()
    if degash_extra:
        degashim_selected.append(degash_extra)

    if supabase is not None:
        try:
            supabase.table("sessions").insert({
                "lakoach_id": lakoach_id,
                "metapel_id": session["user_id"],
                "scheduled_at": request.form.get("session_date"),
                "sikum": sikum_text,
                "degashim": ", ".join(degashim_selected),
                "session_number": int(request.form.get("session_number", 1)),
                "status": "completed",
            }).execute()
        except Exception:
            logger.exception("Failed to save sikum for %s", lakoach_id)
            flash("שמירת הסיכום נכשלה", "error")
            return redirect(url_for("metapel.sikum", lakoach_id=lakoach_id))

    flash("הסיכום נשמר", "success")
    return redirect(url_for("metapel.lakoach_profile", lakoach_id=lakoach_id))
