import datetime
import logging

from flask import Blueprint, redirect, render_template, request, url_for

from agents.intake_agent import analyze_intake
from services.email_service import send_assessment_results
from services.supabase_client import supabase

intake_bp = Blueprint("intake", __name__)
logger = logging.getLogger(__name__)

QUESTIONS = [
    # קרקוע (2 שאלות)
    {
        "id": "q1", "layer": "karakoa", "layer_name": "קרקוע",
        "layer_class": "karakoa", "type": "scale",
        "text": "עד כמה את מרגישה בטוחה ורגועה בגופך בחיי היומיום?",
        "scale_low": "כלל לא", "scale_high": "לגמרי",
    },
    {
        "id": "q2", "layer": "karakoa", "layer_name": "קרקוע",
        "layer_class": "karakoa", "type": "scale",
        "text": "כמה קל לך להירגע אחרי מצב לחוץ?",
        "scale_low": "קשה מאוד", "scale_high": "קל מאוד",
    },
    # פריקה (2 שאלות)
    {
        "id": "q3", "layer": "preka", "layer_name": "פריקה",
        "layer_class": "preka", "type": "scale",
        "text": "עד כמה את מרגישה שיש לך מקום לשחרר רגשות ומתח בחיים שלך?",
        "scale_low": "כמעט אין", "scale_high": "יש לי הרבה",
    },
    {
        "id": "q4", "layer": "preka", "layer_name": "פריקה",
        "layer_class": "preka", "type": "text",
        "text": "מה בדרך כלל עוזר לך להרגיש קלה יותר כשמשהו כבד?",
        "placeholder": "תנועה, שיחה, בכי, מוזיקה...",
    },
    # אינטגרציה (2 שאלות)
    {
        "id": "q5", "layer": "integrazia", "layer_name": "אינטגרציה",
        "layer_class": "integrazia", "type": "scale",
        "text": "עד כמה את מרגישה שאת מבינה את הקשר בין מה שאת מרגישה בגוף לבין מה שקורה לך רגשית?",
        "scale_low": "בכלל לא", "scale_high": "מאוד",
    },
    {
        "id": "q6", "layer": "integrazia", "layer_name": "אינטגרציה",
        "layer_class": "integrazia", "type": "scale",
        "text": "כמה קל לך לעבד חוויות רגשיות קשות ולהמשיך הלאה?",
        "scale_low": "קשה מאוד", "scale_high": "קל יחסית",
    },
    # קהילה (2 שאלות)
    {
        "id": "q7", "layer": "kehila", "layer_name": "קהילה",
        "layer_class": "kehila", "type": "scale",
        "text": "עד כמה את מרגישה שייכות ותמיכה מהסביבה שלך?",
        "scale_low": "מאוד מבודדת", "scale_high": "מאוד מחוברת",
    },
    {
        "id": "q8", "layer": "kehila", "layer_name": "קהילה",
        "layer_class": "kehila", "type": "text",
        "text": "תארי קשר אחד בחייך שמרגיש לך בטוח ומחזיק אותך.",
        "placeholder": "אפשר לכתוב על אדם, קבוצה, קהילה...",
    },
    # משמעות (2 שאלות)
    {
        "id": "q9", "layer": "mashmaut", "layer_name": "משמעות",
        "layer_class": "mashmaut", "type": "scale",
        "text": "עד כמה את מרגישה שיש לך כיוון ומשמעות בחיים שלך עכשיו?",
        "scale_low": "אבודה", "scale_high": "ברורה מאוד",
    },
    {
        "id": "q10", "layer": "mashmaut", "layer_name": "משמעות",
        "layer_class": "mashmaut", "type": "text",
        "text": "מה את מקווה שישתנה בחייך עד סוף התהליך בבריאה?",
        "placeholder": "כתבי בחופשיות — אין תשובה נכונה...",
    },
    # 2 שאלות פתוחות נוספות
    {
        "id": "q11", "layer": "karakoa", "layer_name": "כללי",
        "layer_class": "karakoa", "type": "text",
        "text": "מה הביא אותך לבריאה עכשיו, בדיוק בנקודה הזו בחיים?",
        "placeholder": "ספרי לנו...",
    },
    {
        "id": "q12", "layer": "kehila", "layer_name": "כללי",
        "layer_class": "kehila", "type": "text",
        "text": "יש משהו שחשוב לך שנדע עלייך לפני שמתחילים?",
        "placeholder": "כל מה שתרצי לשתף...",
    },
]

_MOCK_LAKOACH = {"id": "mock-lakoach", "full_name": "משתמש פיתוח", "email": "dev@test.com"}

_MOCK_RESULT = {
    "resilience_score": 68,
    "breakdown": {"karakoa": 72, "preka": 55, "integrazia": 65, "kehila": 80, "mashmaut": 62},
    "strengths": ["קשר עמוק לאחרים", "מודעות עצמית", "רצון עמוק לצמוח"],
    "growth_areas": ["שחרור ופריקה", "חיבור לגוף"],
    "recommended_activities": ["יוגה סומטית", "ריברסינג", "מעגל נשים"],
    "summary_he": "השאלון מגלה אדם עם חוסן בסיסי חזק ויכולת קשר טובה. יש מקום לעבוד על שחרור מתחים אצורים וחיבור עמוק יותר לגוף.",
    "personal_letter": "שלום יקרה,\n\nתודה על הפתיחות והלב שהבאת לשאלון.\n\nמה שעלה מהתשובות שלך הוא תמונה של אדם שיש בו כוח אמיתי — ובמקביל, גם חיפוש עמוק אחר מרחב לנשום.\n\nאנחנו כאן איתך לאורך הדרך 🤍\n\nבריאה",
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


@intake_bp.route("/intake/<token>", methods=["GET"])
def intake_form(token):
    """Show the intake questionnaire"""
    if supabase is not None:
        try:
            profile = _load_profile_by_token(token)
            if not profile:
                return render_template("intake/error.html", msg="הלינק לא תקין. פנה למלווה שלך.")

            expires = datetime.datetime.fromisoformat(profile["intake_token_expires"])
            if datetime.datetime.now(datetime.timezone.utc) > expires:
                return render_template("intake/error.html", msg="הלינק פג תוקף. פנה למלווה שלך לקבלת לינק חדש.")

            if profile.get("intake_submitted_at"):
                return redirect(url_for("intake.intake_results", token=token))

            lakoach = profile["users"]
            return render_template("intake/form.html", lakoach=lakoach, questions=QUESTIONS, token=token)
        except Exception:
            logger.exception("Failed to load intake form for token %s, using mock data", token)

    return render_template("intake/form.html", lakoach=_MOCK_LAKOACH, questions=QUESTIONS, token=token)


@intake_bp.route("/intake/<token>", methods=["POST"])
def intake_submit(token):
    """Process answers → AI → save → redirect to results"""
    answers = dict(request.form.items())
    lakoach_name = "לקוח"

    if supabase is not None:
        try:
            profile = _load_profile_by_token(token)
            lakoach = profile["users"]
            lakoach_id = lakoach["id"]
            lakoach_name = lakoach["full_name"]

            result = analyze_intake(answers, lakoach_name)

            supabase.table("intakes").insert({
                "lakoach_id": lakoach_id,
                "raw_summary": answers,
                "ai_assessment": result,
                "resilience_score": result["resilience_score"],
                "score_breakdown": result["breakdown"],
                "status": "completed",
            }).execute()

            supabase.table("lakoach_profiles").update({
                "intake_submitted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }).eq("intake_token", token).execute()

            assessment_html = f"""
            <div style="background:#fff0db; padding:20px; border-radius:16px; margin:20px 0;">
              <strong style="color:#634734;">Resilience Score: {result['resilience_score']}/100</strong>
              <p style="color:#8c6b54; margin-top:8px;">{result['summary_he']}</p>
            </div>
            """
            send_assessment_results(lakoach["email"], lakoach_name, assessment_html)
        except Exception:
            logger.exception("Failed to process intake submission for token %s", token)

    return redirect(url_for("intake.intake_results", token=token))


@intake_bp.route("/intake/<token>/result")
def intake_results(token):
    """Show AI assessment results"""
    if supabase is not None:
        try:
            profile = _load_profile_by_token(token)
            lakoach = profile["users"]
            lakoach_id = lakoach["id"]

            intake_res = (
                supabase.table("intakes")
                .select("*")
                .eq("lakoach_id", lakoach_id)
                .order("created_at", desc=True)
                .limit(1)
                .single()
                .execute()
            )
            ai_result = intake_res.data.get("ai_assessment", {})

            return render_template("intake/results.html", lakoach=lakoach, result=ai_result, token=token)
        except Exception:
            logger.exception("Failed to load intake results for token %s, using mock data", token)

    return render_template("intake/results.html", lakoach=_MOCK_LAKOACH, result=_MOCK_RESULT, token=token)
