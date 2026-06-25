import logging
import secrets
from datetime import datetime, timedelta, timezone

from flask import Blueprint, flash, redirect, render_template, request

from routes.auth import login_required
from services.email_service import send_intake_invite
from services.supabase_client import supabase

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
logger = logging.getLogger(__name__)

_MOCK_LAKOCHIM = [
    {"id": "1", "full_name": "נועה כהן", "mashlul": "צמיחה", "melave_name": "מלווה דמה",
     "metapel_name": "מטפל דמה", "start_date": "2026-01-15", "status_class": "active"},
    {"id": "2", "full_name": "יואב לוי", "mashlul": "העמקה", "melave_name": "מלווה דמה",
     "metapel_name": "—", "start_date": "2026-02-01", "status_class": "waiting"},
]
_MOCK_MELAVIM = [{"id": "mock-melave", "full_name": "מלווה דמה"}]
_MOCK_METAPLIM = [{"id": "mock-metapel", "full_name": "מטפל דמה"}]


def _admin_only(view):
    from functools import wraps
    from flask import session

    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("גישה רק למנהל המערכת", "error")
            return redirect("/login")
        return view(*args, **kwargs)

    return wrapped


@admin_bp.route("")
@login_required
@_admin_only
def dashboard():
    lakochim = _MOCK_LAKOCHIM
    melavim_count = len(_MOCK_MELAVIM)
    metaplim_count = len(_MOCK_METAPLIM)

    if supabase is not None:
        try:
            lakochim_res = supabase.table("lakoach_profiles").select("*, users(full_name)").execute()
            lakochim = lakochim_res.data
            melavim_count = len(supabase.table("users").select("id").eq("role", "melave").execute().data)
            metaplim_count = len(supabase.table("users").select("id").eq("role", "metapel").execute().data)
        except Exception:
            logger.exception("Failed to load admin dashboard data, using mock data")
            flash("מצב פיתוח — נתוני דמה", "info")

    waiting_count = sum(1 for l in lakochim if l.get("status_class") == "waiting" or l.get("metapel_id") is None)

    return render_template(
        "admin/dashboard.html",
        lakochim=lakochim,
        lakochim_count=len(lakochim),
        melavim_count=melavim_count,
        metaplim_count=metaplim_count,
        waiting_count=waiting_count,
    )


@admin_bp.route("/lakoach/new", methods=["GET"])
@login_required
@_admin_only
def lakoach_new():
    melavim = _MOCK_MELAVIM
    if supabase is not None:
        try:
            melavim = supabase.table("users").select("id, full_name").eq("role", "melave").execute().data
        except Exception:
            logger.exception("Failed to load melavim list, using mock data")

    return render_template("admin/lakoach_new.html", melavim=melavim)


@admin_bp.route("/lakoach", methods=["POST"])
@login_required
@_admin_only
def create_lakoach():
    full_name = request.form.get("full_name")
    email = request.form.get("email")

    if not full_name or not email:
        flash("שם מלא ומייל הם שדות חובה", "error")
        return redirect("/admin/lakoach/new")

    token = secrets.token_urlsafe(32)
    expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    if supabase is not None:
        try:
            user_res = (
                supabase.table("users")
                .insert({
                    "full_name": full_name,
                    "email": email,
                    "phone": request.form.get("phone"),
                    "role": "lakoach",
                })
                .execute()
            )
            user_id = user_res.data[0]["id"]
            supabase.table("lakoach_profiles").insert({
                "user_id": user_id,
                "melave_id": request.form.get("melave_id"),
                "mashlul": request.form.get("mashlul"),
                "start_date": request.form.get("start_date"),
                "intake_token": token,
                "intake_token_expires": expires,
            }).execute()
        except Exception:
            logger.exception("Failed to create lakoach %s", email)
            flash("יצירת הלקוח נכשלה", "error")
            return redirect("/admin/lakoach/new")

    send_intake_invite(email, full_name, token)
    flash(f"לקוח נוצר בהצלחה — מייל הזמנה נשלח ל-{email} 🌿", "success")
    return redirect("/admin")


@admin_bp.route("/lakoach/<lakoach_id>")
@login_required
@_admin_only
def lakoach_profile(lakoach_id):
    lakoach = {"id": lakoach_id, "full_name": "לקוח דמה", "email": "", "phone": ""}
    profile = {}
    intake_row = None
    tochnit_row = None
    melave_row = None
    metapel_row = None
    sessions_list = []
    score = 0
    breakdown = {}
    strengths = []

    if supabase is not None:
        try:
            lakoach = supabase.table("users").select("*").eq("id", lakoach_id).single().execute().data
            profile = (
                supabase.table("lakoach_profiles").select("*").eq("user_id", lakoach_id).single().execute().data
                or {}
            )

            intake_res = (
                supabase.table("intakes")
                .select("*")
                .eq("lakoach_id", lakoach_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            intake_row = intake_res.data[0] if intake_res.data else None

            tochnit_res = (
                supabase.table("tochniyot_ishiyot")
                .select("*")
                .eq("lakoach_id", lakoach_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            tochnit_row = tochnit_res.data[0] if tochnit_res.data else None

            if profile.get("melave_id"):
                melave_row = (
                    supabase.table("users")
                    .select("full_name, email, phone")
                    .eq("id", profile["melave_id"])
                    .single()
                    .execute()
                    .data
                )
            if profile.get("metapel_id"):
                metapel_row = (
                    supabase.table("users")
                    .select("full_name, email, phone")
                    .eq("id", profile["metapel_id"])
                    .single()
                    .execute()
                    .data
                )

            sessions_list = (
                supabase.table("sessions")
                .select("*")
                .eq("lakoach_id", lakoach_id)
                .order("scheduled_at", desc=True)
                .limit(5)
                .execute()
                .data
                or []
            )

            ai_result = intake_row.get("ai_assessment") if intake_row else {} or {}
            score = ai_result.get("resilience_score", 0)
            breakdown = ai_result.get("breakdown", {})
            strengths = ai_result.get("strengths", [])
        except Exception:
            logger.exception("Failed to load admin profile for %s", lakoach_id)
            flash("שגיאה בטעינת הפרופיל — מוצגים נתוני דמה", "error")

    return render_template(
        "admin/lakoach_profile.html",
        lakoach=lakoach,
        profile=profile,
        intake=intake_row,
        tochnit=tochnit_row,
        melave=melave_row,
        metapel=metapel_row,
        sessions=sessions_list,
        score=score,
        breakdown=breakdown,
        strengths=strengths,
    )


@admin_bp.route("/shibutz/<lakoach_id>", methods=["GET"])
@login_required
@_admin_only
def shibutz(lakoach_id):
    lakoach = {"id": lakoach_id, "full_name": "לקוח דמה", "mashlul": "צמיחה"}
    metaplim = _MOCK_METAPLIM

    if supabase is not None:
        try:
            lakoach_res = (
                supabase.table("lakoach_profiles")
                .select("*, users(full_name)")
                .eq("user_id", lakoach_id)
                .single()
                .execute()
            )
            lakoach = lakoach_res.data
            metaplim = supabase.table("users").select("id, full_name").eq("role", "metapel").execute().data
        except Exception:
            logger.exception("Failed to load shibutz data for %s", lakoach_id)

    return render_template("admin/shibutz.html", lakoach=lakoach, metaplim=metaplim)


@admin_bp.route("/shibutz/<lakoach_id>", methods=["POST"])
@login_required
@_admin_only
def update_shibutz(lakoach_id):
    metapel_id = request.form.get("metapel_id")

    if supabase is not None:
        try:
            supabase.table("lakoach_profiles").update({"metapel_id": metapel_id}).eq("user_id", lakoach_id).execute()
        except Exception:
            logger.exception("Failed to update shibutz for %s", lakoach_id)
            flash("השיבוץ נכשל", "error")
            return redirect(f"/admin/shibutz/{lakoach_id}")

    flash("השיבוץ אושר", "success")
    return redirect("/admin")
