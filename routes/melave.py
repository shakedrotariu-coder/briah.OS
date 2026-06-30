import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from functools import wraps

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session

from agents.tochnit_agent import build_tochnit
from agents.transcription_agent import extract_intake_from_transcript, transcribe_audio
from routes.auth import login_required
from services.email_service import send_assessment_results
from services.pdf_service import generate_tochnit_pdf
from services.supabase_client import supabase

melave_bp = Blueprint("melave", __name__, url_prefix="/melave")
logger = logging.getLogger(__name__)

_MOCK_LAKOCHIM = [
    {"id": "1", "full_name": "נועה כהן", "mashlul": "צמיחה", "shav": "ממתין לאינטייק",
     "shav_class": "cream", "start_date": "2026-01-15"},
]

_MOCK_EXTRACTION = {
    "ma_ala_bashicha": "מה עלה בשיחה (דמה — יתחבר ל-AI עם Supabase מחובר)",
    "ratzon_amok": "רצון עמוק שעלה (דמה)",
    "nosim_merkaziyim": ["חיבור לגוף", "ויסות רגשי", "קהילה"],
    "recommended_tzir_1": "קרקוע",
    "recommended_tzir_2": "פריקה",
    "recommended_tzir_3": "קהילה",
}


def _melave_only(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "melave":
            flash("גישה רק למלווים", "error")
            return redirect("/login")
        return view(*args, **kwargs)

    return wrapped


@melave_bp.route("")
@login_required
@_melave_only
def dashboard():
    lakochim = _MOCK_LAKOCHIM

    if supabase is not None:
        try:
            profiles = (
                supabase.table("lakoach_profiles")
                .select("*, users(*)")
                .eq("melave_id", session.get("user_id"))
                .execute()
                .data
                or []
            )
            lakochim = []
            for p in profiles:
                u = p["users"]
                intake_res = (
                    supabase.table("intakes")
                    .select("status, created_at")
                    .eq("lakoach_id", u["id"])
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                    .data
                )
                tochnit_res = (
                    supabase.table("tochniyot_ishiyot").select("id, sent_at").eq("lakoach_id", u["id"]).execute().data
                )

                if tochnit_res and tochnit_res[0].get("sent_at"):
                    shav, shav_class = "תוכנית נשלחה", "ok"
                elif intake_res:
                    shav, shav_class = "אינטייק הושלם", "warning"
                else:
                    shav, shav_class = "ממתין לאינטייק", "cream"

                lakochim.append({
                    **u,
                    "shav": shav,
                    "shav_class": shav_class,
                    "mashlul": p.get("mashlul", ""),
                    "start_date": p.get("start_date", ""),
                })
        except Exception:
            logger.exception("Failed to load melave's lakochim, using mock data")

    return render_template("melave/dashboard.html", lakochim=lakochim)


@melave_bp.route("/intake/<lakoach_id>")
@login_required
@_melave_only
def intake(lakoach_id):
    lakoach = {"id": lakoach_id, "full_name": "נועה כהן"}
    intake_row = None

    if supabase is not None:
        try:
            lakoach = supabase.table("users").select("*").eq("id", lakoach_id).single().execute().data
            intake_res = (
                supabase.table("intakes")
                .select("*")
                .eq("lakoach_id", lakoach_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            intake_row = intake_res.data[0] if intake_res.data else None
        except Exception:
            logger.exception("Failed to load intake for %s", lakoach_id)

    return render_template("melave/intake.html", lakoach=lakoach, intake=intake_row)


@melave_bp.route("/intake/<lakoach_id>/save", methods=["POST"])
@login_required
@_melave_only
def save_intake(lakoach_id):
    if supabase is not None:
        try:
            supabase.table("intakes").insert({
                "lakoach_id": lakoach_id,
                "melave_id": session.get("user_id"),
                "melave_notes": request.form.get("melave_notes"),
                "raw_summary": {
                    "ma_ala_bashicha": request.form.get("ma_ala_bashicha", ""),
                    "ratzon_amok": request.form.get("ratzon_amok", ""),
                    "nosim_merkaziyim": request.form.getlist("nosim"),
                },
                "status": "completed",
            }).execute()
        except Exception:
            logger.exception("Failed to save intake for %s", lakoach_id)
            flash("שמירת האינטייק נכשלה", "error")
            return redirect(f"/melave/intake/{lakoach_id}")

    flash("האינטייק נשמר", "success")
    return redirect(f"/melave/tochnit/{lakoach_id}")


@melave_bp.route("/intake/<lakoach_id>/process", methods=["POST"])
@login_required
@_melave_only
def process_intake(lakoach_id):
    """Process transcript with AI — extracts structured intake data."""
    transcript = request.form.get("transcript", "")

    if "audio_file" in request.files and request.files["audio_file"].filename:
        f = request.files["audio_file"]
        ext = os.path.splitext(f.filename)[1] or ".mp3"
        path = os.path.join(tempfile.gettempdir(), f"intake_{lakoach_id}{ext}")
        f.save(path)
        transcript = transcribe_audio(path)

    if not transcript:
        return jsonify({"error": "no transcript"}), 400

    lakoach_name = "הלקוחה"
    if supabase is not None:
        try:
            lakoach_row = supabase.table("users").select("full_name").eq("id", lakoach_id).single().execute().data
            lakoach_name = lakoach_row.get("full_name", lakoach_name)
        except Exception:
            logger.exception("Failed to load lakoach name for %s", lakoach_id)

    extracted = extract_intake_from_transcript(transcript, lakoach_name, request.form.get("melave_notes", ""))

    if supabase is not None:
        try:
            supabase.table("intakes").upsert({
                "lakoach_id": lakoach_id,
                "melave_id": session.get("user_id"),
                "transcript": transcript,
                "melave_notes": request.form.get("melave_notes", ""),
                "raw_summary": extracted,
                "status": "draft",
            }).execute()
        except Exception:
            logger.exception("Failed to save processed intake for %s", lakoach_id)

    return jsonify({"success": True, "data": extracted})


@melave_bp.route("/tochnit/<lakoach_id>")
@login_required
@_melave_only
def tochnit(lakoach_id):
    lakoach = {"id": lakoach_id, "full_name": "נועה כהן"}
    intake_row = None
    tochnit_row = None
    mashlul = "tzmiha"

    if supabase is not None:
        try:
            lakoach = supabase.table("users").select("*").eq("id", lakoach_id).single().execute().data
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
            profile = supabase.table("lakoach_profiles").select("mashlul").eq("user_id", lakoach_id).single().execute().data
            mashlul = profile.get("mashlul", mashlul) if profile else mashlul
        except Exception:
            logger.exception("Failed to load tochnit for %s", lakoach_id)

    return render_template(
        "melave/tochnit.html", lakoach=lakoach, intake=intake_row, tochnit=tochnit_row, mashlul=mashlul
    )


@melave_bp.route("/tochnit/<lakoach_id>/generate", methods=["POST"])
@login_required
@_melave_only
def tochnit_generate(lakoach_id):
    """Generate a full personal plan with AI from the saved intake."""
    lakoach_name = "הלקוחה"
    intake_data = _MOCK_EXTRACTION
    onboarding_data = {}
    mashlul = "tzmiha"

    if supabase is not None:
        try:
            lakoach_row = supabase.table("users").select("full_name").eq("id", lakoach_id).single().execute().data
            lakoach_name = lakoach_row.get("full_name", lakoach_name)

            intake_res = (
                supabase.table("intakes")
                .select("*")
                .eq("lakoach_id", lakoach_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if intake_res.data:
                intake_data = intake_res.data[0].get("raw_summary") or intake_data

            ob_res = (
                supabase.table("onboarding_steps")
                .select("*")
                .eq("lakoach_id", lakoach_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if ob_res.data:
                ob = ob_res.data[0]
                for s in range(1, 6):
                    onboarding_data.update(ob.get(f"step{s}_data") or {})

            profile = supabase.table("lakoach_profiles").select("mashlul").eq("user_id", lakoach_id).single().execute().data
            mashlul = profile.get("mashlul", mashlul) if profile else mashlul
        except Exception:
            logger.exception("Failed to load intake/profile for tochnit generation, using mock data for %s", lakoach_id)

    result = build_tochnit(intake_data, lakoach_name, mashlul, onboarding_data)
    return jsonify({"success": True, "data": result})


@melave_bp.route("/tochnit/<lakoach_id>/save", methods=["POST"])
@login_required
@_melave_only
def save_tochnit(lakoach_id):
    if supabase is not None:
        try:
            supabase.table("tochniyot_ishiyot").upsert({
                "lakoach_id": lakoach_id,
                "tzir_1": request.form.get("tzir_1", ""),
                "tzir_2": request.form.get("tzir_2", ""),
                "tzir_3": request.form.get("tzir_3", ""),
                "paaluyot": json.loads(request.form.get("paaluyot", "[]") or "[]"),
                "melave_notes": request.form.get("personal_letter", ""),
            }).execute()
        except Exception:
            logger.exception("Failed to save tochnit for %s", lakoach_id)
            flash("שמירת התוכנית נכשלה", "error")
            return redirect(f"/melave/tochnit/{lakoach_id}")

    flash("הטיוטה נשמרה", "success")
    return redirect(f"/melave/tochnit/{lakoach_id}")


@melave_bp.route("/tochnit/<lakoach_id>/send", methods=["POST"])
@login_required
@_melave_only
def send_tochnit(lakoach_id):
    if supabase is None:
        flash("התוכנית נשלחה ללקוח ולבריאה (מצב פיתוח — אין Supabase)", "success")
        return redirect("/melave")

    try:
        lakoach = supabase.table("users").select("*").eq("id", lakoach_id).single().execute().data or {}

        tochnit_res = (
            supabase.table("tochniyot_ishiyot")
            .select("*")
            .eq("lakoach_id", lakoach_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        tochnit_row = tochnit_res.data[0] if tochnit_res.data else {}

        intake_res = (
            supabase.table("intakes")
            .select("ai_assessment")
            .eq("lakoach_id", lakoach_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        ai_result = intake_res.data[0].get("ai_assessment") if intake_res.data else {}
        ai_result = ai_result or {}

        pdf_bytes = generate_tochnit_pdf(
            lakoach_name=lakoach.get("full_name", ""),
            tochnit=tochnit_row,
            ai_result=ai_result,
        )

        assessment_html = f"""
        <div style="background:#fff0db;padding:20px;border-radius:16px;margin:20px 0;direction:rtl;">
          <strong style="color:#634734;">Resilience Score: {ai_result.get('resilience_score', '—')}/100</strong>
          <p style="color:#8c6b54;margin-top:8px;">{ai_result.get('summary_he', '')}</p>
          <p style="color:#634734;margin-top:12px;">התוכנית האישית שלך מצורפת כ-PDF 🌿</p>
        </div>
        """

        email_sent = send_assessment_results(
            to_email=lakoach.get("email", ""),
            full_name=lakoach.get("full_name", ""),
            assessment_html=assessment_html,
            pdf_bytes=pdf_bytes if pdf_bytes else None,
        )

        supabase.table("tochniyot_ishiyot").update({
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }).eq("lakoach_id", lakoach_id).execute()

        if email_sent:
            flash(f"התוכנית נשלחה ל-{lakoach.get('email')} עם PDF מצורף ✓", "success")
        else:
            flash("התוכנית סומנה כנשלחה — המייל לא נשלח (בדקי הגדרות SMTP)", "info")
    except Exception as e:
        logger.exception("Failed to send tochnit for %s", lakoach_id)
        flash(f"שגיאה בשליחה: {str(e)[:80]}", "error")
        return redirect(f"/melave/tochnit/{lakoach_id}")

    return redirect("/melave")
