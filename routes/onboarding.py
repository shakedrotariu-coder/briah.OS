import datetime
import logging

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from agents.intake_agent import analyze_intake
from services.supabase_client import supabase

ob_bp = Blueprint("onboarding", __name__)
logger = logging.getLogger(__name__)

ONBOARDING_QUESTIONS = {
    "step1": ["full_name", "age", "city", "about_me"],
    "step2": ["what_brought_you", "main_concerns", "where_i_am", "hopes"],
    "step3": ["what_helps", "interests", "challenges", "past_experience", "not_interested"],
    "step4": ["in_treatment", "treatment_details", "emotional_background",
              "medical_status", "medical_details", "safety_needs"],
    "step5": ["mashlul", "mashlul_reason", "therapy_goals", "therapy_type",
              "therapist_gender", "one_goal", "anything_else"],
}

_MOCK_LAKOACH = {"id": "mock-lakoach", "full_name": "משתמש פיתוח", "email": "dev@test.co"}

_MOCK_RESULT = {
    "resilience_score": 68,
    "breakdown": {"karakoa": 72, "preka": 55, "integrazia": 65, "kehila": 80, "mashmaut": 62},
    "summary_he": "ברוכה הבאה לבריאה. ה-Assessment שלך מגלה אדם עם עוצמה אמיתית ורצון עמוק לשינוי.",
    "strengths": ["קשר עמוק לאחרים", "מודעות עצמית", "רצון לצמוח"],
    "growth_areas": ["שחרור ופריקה", "חיבור לגוף"],
    "recommended_activities": ["יוגה סומטית", "ריברסינג", "מעגל נשים"],
    "personal_letter": "יקרה,\n\nתודה על הפתיחות שהבאת לכל שאלה.\n\nאנחנו כאן איתך 🤍\n\nבריאה",
}


def _load_profile_by_token(token):
    return (
        supabase.table("lakoach_profiles")
        .select("*, users(*)")
        .eq("intake_token", token)
        .single()
        .execute()
        .data
    )


@ob_bp.route("/onboarding/<token>")
def welcome(token):
    lakoach = _MOCK_LAKOACH

    if supabase is not None:
        try:
            profile = _load_profile_by_token(token)
            if profile:
                lakoach = profile["users"]

            ob = (
                supabase.table("onboarding_steps")
                .select("step_completed, completed_at")
                .eq("token", token)
                .execute()
                .data
            )
            if ob and ob[0].get("completed_at"):
                return redirect(url_for("onboarding.result", token=token))
        except Exception:
            logger.exception("Failed to load onboarding welcome for token %s, using mock data", token)

    return render_template("onboarding/welcome.html", lakoach=lakoach, token=token)


@ob_bp.route("/onboarding/step/<int:step>/<token>", methods=["GET", "POST"])
def step(step, token):
    lakoach = _MOCK_LAKOACH

    if supabase is not None:
        try:
            profile = _load_profile_by_token(token)
            if profile:
                lakoach = profile["users"]
        except Exception:
            logger.exception("Failed to load lakoach for onboarding step %s/%s", step, token)

    if request.method == "POST":
        step_data = {}
        step_key = f"step{step}"
        for field in ONBOARDING_QUESTIONS.get(step_key, []):
            val = request.form.getlist(field) or request.form.get(field, "")
            step_data[field] = val if len(val) > 1 else (val[0] if val else "")

        if supabase is not None:
            try:
                existing = supabase.table("onboarding_steps").select("id").eq("token", token).execute().data
                if existing:
                    supabase.table("onboarding_steps").update({
                        f"step{step}_data": step_data,
                        "step_completed": step,
                    }).eq("token", token).execute()
                else:
                    supabase.table("onboarding_steps").insert({
                        "token": token,
                        "lakoach_id": lakoach.get("id", ""),
                        f"step{step}_data": step_data,
                        "step_completed": step,
                    }).execute()
            except Exception:
                logger.exception("Failed to save onboarding step %s for token %s", step, token)

        if step < 5:
            return redirect(url_for("onboarding.step", step=step + 1, token=token))
        return redirect(url_for("onboarding.process", token=token))

    return render_template(f"onboarding/step{step}.html", lakoach=lakoach, token=token, current_step=step)


@ob_bp.route("/onboarding/process/<token>")
def process(token):
    """AI processing — shown as a loading page, then redirects to the result page via JS."""
    return render_template("onboarding/processing.html", token=token)


@ob_bp.route("/onboarding/process/<token>/run", methods=["POST"])
def process_run(token):
    """Called by JS on the processing page to actually run the AI analysis."""
    if supabase is None:
        return jsonify({"success": True})

    try:
        ob = supabase.table("onboarding_steps").select("*").eq("token", token).single().execute().data

        combined = {}
        for s in range(1, 6):
            step_data = ob.get(f"step{s}_data") or {}
            combined.update(step_data)

        result = analyze_intake(combined, combined.get("full_name", ""))

        profile = supabase.table("lakoach_profiles").select("user_id").eq("intake_token", token).single().execute().data
        lakoach_id = profile["user_id"]

        supabase.table("intakes").upsert({
            "lakoach_id": lakoach_id,
            "raw_summary": combined,
            "ai_assessment": result,
            "resilience_score": result.get("resilience_score", 0),
            "score_breakdown": result.get("breakdown", {}),
            "status": "completed",
        }).execute()

        supabase.table("onboarding_steps").update({
            "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }).eq("token", token).execute()

        supabase.table("lakoach_profiles").update({
            "intake_submitted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }).eq("intake_token", token).execute()

        return jsonify({"success": True})
    except Exception as e:
        logger.exception("Failed to process onboarding for token %s", token)
        return jsonify({"success": False, "error": str(e)}), 500


@ob_bp.route("/onboarding/<token>/result")
def result(token):
    lakoach = _MOCK_LAKOACH
    ai_result = _MOCK_RESULT

    if supabase is not None:
        try:
            profile = _load_profile_by_token(token)
            lakoach = profile["users"]

            intake_res = (
                supabase.table("intakes")
                .select("ai_assessment")
                .eq("lakoach_id", lakoach["id"])
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if intake_res.data:
                ai_result = intake_res.data[0].get("ai_assessment") or ai_result
        except Exception:
            logger.exception("Failed to load onboarding result for token %s, using mock data", token)

    return render_template("onboarding/result.html", lakoach=lakoach, ai_result=ai_result, token=token)
