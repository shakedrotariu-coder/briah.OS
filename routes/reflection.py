import logging
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session

from agents.reflection_agent import analyze_reflection
from agents.tochnit_agent import AVAILABLE_ACTIVITIES
from routes.auth import login_required
from services.supabase_client import supabase

reflection_bp = Blueprint("reflection", __name__)
logger = logging.getLogger(__name__)

_WORKSHOPS = [act["name"] for act in AVAILABLE_ACTIVITIES]


def _lakoach_only(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "lakoach":
            flash("גישה רק ללקוחות", "error")
            return redirect("/login")
        return view(*args, **kwargs)

    return wrapped


def _care_manager_only(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("גישה רק לצוות הניהול", "error")
            return redirect("/login")
        return view(*args, **kwargs)

    return wrapped


@reflection_bp.route("/lakoach/reflection/<int:month_num>", methods=["GET"])
@login_required
@_lakoach_only
def reflection_form(month_num):
    return render_template("lakoach/reflection.html", month=month_num, workshops=_WORKSHOPS)


@reflection_bp.route("/lakoach/reflection/<int:month_num>", methods=["POST"])
@login_required
@_lakoach_only
def reflection_submit(month_num):
    user_id = session.get("user_id")
    reflection_data = dict(request.form.items())

    prev_reflections = []
    if supabase is not None:
        try:
            prev_reflections = (
                supabase.table("monthly_reflections")
                .select("avg_belonging, avg_wellbeing")
                .eq("lakoach_id", user_id)
                .order("month_num")
                .execute()
                .data
                or []
            )
        except Exception:
            logger.exception("Failed to load previous reflections for %s", user_id)

    result = analyze_reflection(reflection_data, session.get("full_name", ""), month_num, prev_reflections)

    if supabase is not None:
        try:
            import datetime

            month_year = datetime.date.today().strftime("%Y-%m")
            supabase.table("monthly_reflections").insert({
                "lakoach_id": user_id,
                "month_num": month_num,
                "month_year": month_year,
                "reflection_data": reflection_data,
                "ai_analysis": result,
                "overall_status": result.get("overall_status"),
                "avg_belonging": result.get("avg_belonging"),
                "avg_wellbeing": result.get("avg_wellbeing"),
            }).execute()
        except Exception:
            logger.exception("Failed to save reflection for %s", user_id)
            flash("שגיאה בשמירת הרפלקציה", "error")
            return redirect(f"/lakoach/reflection/{month_num}")

    flash("תודה שלקחת את הזמן — קיבלנו את הרפלקציה שלך 🤍", "success")
    return redirect("/lakoach")


@reflection_bp.route("/care-manager/<lakoach_id>/reflection/<int:month_num>")
@login_required
@_care_manager_only
def reflection_view(lakoach_id, month_num):
    analysis = {
        "summary": "אין עדיין רפלקציה לחודש זה",
        "overall_status": "progressing",
        "risk_flags": [],
        "recommended_adjustments": [],
        "avg_belonging": 0,
        "avg_wellbeing": 0,
        "belonging_scores": {},
        "wellbeing_scores": {},
        "melave_note": "",
        "content_feedback": "",
    }
    month_history = []
    month_labels = []
    belonging_history = []
    wellbeing_history = []

    if supabase is not None:
        try:
            history = (
                supabase.table("monthly_reflections")
                .select("*")
                .eq("lakoach_id", lakoach_id)
                .order("month_num")
                .execute()
                .data
                or []
            )
            month_history = history

            current = next((r for r in history if r["month_num"] == month_num), None)
            if current and current.get("ai_analysis"):
                analysis = current["ai_analysis"]

            for r in history:
                month_labels.append(f"חודש {r['month_num']}")
                belonging_history.append(r.get("avg_belonging", 0))
                wellbeing_history.append(r.get("avg_wellbeing", 0))
        except Exception:
            logger.exception("Failed to load reflection history for %s", lakoach_id)

    return render_template(
        "care_manager/reflection_view.html",
        analysis=analysis,
        month_history=month_history,
        month_labels=month_labels,
        belonging_history=belonging_history,
        wellbeing_history=wellbeing_history,
        lakoach_id=lakoach_id,
        month_num=month_num,
    )
