import logging
from datetime import date
from functools import wraps

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session

from agents.companion_agent import get_companion_response
from routes.auth import login_required
from services.supabase_client import supabase

lakoach_bp = Blueprint("lakoach", __name__, url_prefix="/lakoach")
logger = logging.getLogger(__name__)

_MOCK_DASHBOARD = {
    "score": 68,
    "breakdown": {"karakoa": 72, "preka": 55, "integrazia": 65, "kehila": 80, "mashmaut": 62},
    "strengths": ["קשר עמוק לאחרים", "מודעות עצמית"],
    "recommended_activities": ["יוגה סומטית", "ריברסינג", "מעגל נשים"],
    "primary_focus": "preka",
    "journey_type": "moderate",
    "personal_letter": "",
}


def _lakoach_only(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "lakoach":
            flash("גישה רק ללקוחות", "error")
            return redirect("/login")
        return view(*args, **kwargs)

    return wrapped


@lakoach_bp.route("")
@login_required
@_lakoach_only
def dashboard():
    user_id = session.get("user_id")
    lakoach = {"id": user_id, "full_name": session.get("full_name")}
    tochnit_row = None
    melave_row = None
    metapel_row = None
    next_session = None
    day_num = 1
    result = dict(_MOCK_DASHBOARD)

    if supabase is not None:
        try:
            profile = (
                supabase.table("lakoach_profiles")
                .select("*, users(*)")
                .eq("user_id", user_id)
                .single()
                .execute()
                .data
            )
            lakoach = profile.get("users", lakoach)

            intake_res = (
                supabase.table("intakes")
                .select("*")
                .eq("lakoach_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if intake_res.data:
                ai_result = intake_res.data[0].get("ai_assessment") or {}
                result = {
                    "score": ai_result.get("resilience_score", 0),
                    "breakdown": ai_result.get("breakdown", {}),
                    "strengths": ai_result.get("strengths", []),
                    "recommended_activities": ai_result.get("recommended_activities", []),
                    "primary_focus": ai_result.get("primary_focus", ""),
                    "journey_type": ai_result.get("journey_type", "moderate"),
                    "personal_letter": ai_result.get("personal_letter", ""),
                }

            tochnit_res = (
                supabase.table("tochniyot_ishiyot")
                .select("*")
                .eq("lakoach_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            tochnit_row = tochnit_res.data[0] if tochnit_res.data else None

            if profile.get("melave_id"):
                melave_row = supabase.table("users").select("*").eq("id", profile["melave_id"]).single().execute().data
            if profile.get("metapel_id"):
                metapel_row = supabase.table("users").select("*").eq("id", profile["metapel_id"]).single().execute().data
                ns = (
                    supabase.table("sessions")
                    .select("*")
                    .eq("lakoach_id", user_id)
                    .eq("status", "scheduled")
                    .order("scheduled_at")
                    .limit(1)
                    .execute()
                    .data
                )
                next_session = ns[0] if ns else None

            start_date = profile.get("start_date")
            if start_date:
                day_num = max(1, (date.today() - date.fromisoformat(start_date)).days + 1)
        except Exception:
            logger.exception("Failed to load lakoach dashboard for %s", user_id)

    luz = tochnit_row.get("luz_hodshi", []) if tochnit_row else []

    return render_template(
        "lakoach/dashboard.html",
        lakoach=lakoach,
        score=result["score"],
        breakdown=result["breakdown"],
        strengths=result["strengths"],
        recommended_activities=result["recommended_activities"],
        primary_focus=result["primary_focus"],
        journey_type=result["journey_type"],
        personal_letter=result["personal_letter"],
        tochnit=tochnit_row,
        luz=luz,
        melave=melave_row,
        metapel=metapel_row,
        next_session=next_session,
        day_num=day_num,
    )


@lakoach_bp.route("/companion", methods=["GET"])
@login_required
@_lakoach_only
def companion():
    user_id = session.get("user_id")
    lakoach = {"id": user_id, "full_name": session.get("full_name")}
    history = []

    if supabase is not None:
        try:
            history = (
                supabase.table("companion_logs")
                .select("*")
                .eq("lakoach_id", user_id)
                .order("created_at")
                .limit(50)
                .execute()
                .data
            )
        except Exception:
            logger.exception("Failed to load companion history for %s", user_id)

    return render_template("lakoach/companion.html", lakoach=lakoach, history=history)


@lakoach_bp.route("/companion", methods=["POST"])
@login_required
@_lakoach_only
def companion_message():
    user_id = session.get("user_id")
    message = (request.get_json(silent=True) or {}).get("message", "").strip()

    if not message:
        return jsonify({"error": "empty"}), 400

    journey_context = {}
    if supabase is not None:
        try:
            intake_res = (
                supabase.table("intakes")
                .select("ai_assessment")
                .eq("lakoach_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if intake_res.data:
                journey_context = intake_res.data[0].get("ai_assessment") or {}
        except Exception:
            logger.exception("Failed to load journey context for %s", user_id)

    reply = get_companion_response(user_id, message, session.get("full_name", ""), journey_context)
    return jsonify({"response": reply})
