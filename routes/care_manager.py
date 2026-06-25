import logging
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, session

from routes.auth import login_required
from services.supabase_client import supabase

cm_bp = Blueprint("care_manager", __name__, url_prefix="/care-manager")
logger = logging.getLogger(__name__)

_MOCK_LAKOCHIM = [
    {"id": "1", "full_name": "נועה כהן", "score": 68, "risk_level": "low", "last_contact": "2026-06-23", "mashlul": "צמיחה"},
    {"id": "2", "full_name": "יואב לוי", "score": 41, "risk_level": "high", "last_contact": "אין", "mashlul": "העמקה"},
]
_MOCK_STATS = {"total": 2, "total_risk": 1, "avg_score": 55, "wa_engagement": 50, "sessions_this_week": 1}


def _care_manager_only(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("גישה רק לצוות הניהול", "error")
            return redirect("/login")
        return view(*args, **kwargs)

    return wrapped


def calculate_risk_flags(lakoach_id: str) -> list:
    """Auto-detect risk flags for a participant."""
    flags = []
    if supabase is None:
        return flags

    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        last_wa = (
            supabase.table("wa_messages")
            .select("sent_at")
            .eq("user_id", lakoach_id)
            .eq("direction", "inbound")
            .order("sent_at", desc=True)
            .limit(1)
            .execute()
            .data
        )

        if not last_wa or last_wa[0]["sent_at"] < cutoff:
            flags.append({"type": "no_response", "severity": "high", "text": "לא ענה/תה ל-WhatsApp 3+ ימים"})

        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        checkins = (
            supabase.table("companion_logs")
            .select("content")
            .eq("lakoach_id", lakoach_id)
            .eq("channel", "whatsapp")
            .ilike("content", "צ׳ק-אין יומי%")
            .gte("created_at", week_ago)
            .execute()
            .data
            or []
        )

        if checkins:
            scores = []
            for c in checkins:
                try:
                    scores.append(int(c["content"].split(":")[1].split("/")[0].strip()))
                except Exception:
                    pass
            if scores and (sum(scores) / len(scores)) < 2.5:
                flags.append({
                    "type": "low_scores",
                    "severity": "medium",
                    "text": f"ממוצע צ׳ק-אין נמוך ({sum(scores) / len(scores):.1f}/5 השבוע)",
                })
    except Exception:
        logger.exception("Failed to calculate risk flags for %s", lakoach_id)

    return flags


@cm_bp.route("")
@login_required
@_care_manager_only
def dashboard():
    lakochim = _MOCK_LAKOCHIM
    risk_alerts = []
    upcoming_sessions = []
    wa_today = []
    stats = _MOCK_STATS

    if supabase is not None:
        try:
            profiles = supabase.table("lakoach_profiles").select("*, users(*)").execute().data or []
            total = len(profiles)

            lakochim = []
            risk_alerts = []
            total_risk = 0

            for p in profiles:
                u = p.get("users") or {}
                uid = u.get("id", "")

                last_checkin = (
                    supabase.table("wa_messages")
                    .select("body, sent_at")
                    .eq("user_id", uid)
                    .eq("direction", "inbound")
                    .order("sent_at", desc=True)
                    .limit(1)
                    .execute()
                    .data
                )

                intake_res = (
                    supabase.table("intakes")
                    .select("resilience_score")
                    .eq("lakoach_id", uid)
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                    .data
                )
                score = intake_res[0]["resilience_score"] if intake_res else None

                flags = calculate_risk_flags(uid)
                if flags:
                    total_risk += 1
                    for f in flags:
                        risk_alerts.append({**f, "lakoach_name": u.get("full_name", ""), "lakoach_id": uid})

                if any(f["severity"] == "high" for f in flags):
                    risk_level = "high"
                elif flags:
                    risk_level = "medium"
                else:
                    risk_level = "low"

                last_contact = last_checkin[0]["sent_at"][:10] if last_checkin else "אין"

                lakochim.append({
                    **u,
                    "score": score,
                    "risk_level": risk_level,
                    "risk_flags": flags,
                    "last_contact": last_contact,
                    "mashlul": p.get("mashlul", ""),
                })

            today = datetime.now(timezone.utc).date().isoformat()
            wa_today = (
                supabase.table("wa_messages").select("*").eq("direction", "inbound").gte("sent_at", today).execute().data
                or []
            )

            upcoming_sessions = (
                supabase.table("sessions")
                .select("*")
                .eq("status", "scheduled")
                .gte("scheduled_at", datetime.now(timezone.utc).isoformat())
                .order("scheduled_at")
                .limit(5)
                .execute()
                .data
                or []
            )

            scored = [l["score"] for l in lakochim if l["score"]]
            avg_score = round(sum(scored) / len(scored)) if scored else 0
            wa_engagement = round((len(wa_today) / max(total, 1)) * 100)

            risk_alerts = risk_alerts[:5]
            wa_today = wa_today[:4]
            stats = {
                "total": total,
                "total_risk": total_risk,
                "avg_score": avg_score,
                "wa_engagement": wa_engagement,
                "sessions_this_week": len(upcoming_sessions),
            }
        except Exception:
            logger.exception("Failed to load CRM dashboard, using mock data")
            lakochim, risk_alerts, upcoming_sessions, wa_today, stats = (
                _MOCK_LAKOCHIM, [], [], [], _MOCK_STATS,
            )

    return render_template(
        "care_manager/dashboard.html",
        lakochim=lakochim,
        risk_alerts=risk_alerts,
        upcoming_sessions=upcoming_sessions,
        wa_today=wa_today,
        stats=stats,
    )


@cm_bp.route("/<lakoach_id>")
@login_required
@_care_manager_only
def lakoach_profile(lakoach_id):
    lakoach = {"id": lakoach_id, "full_name": "לקוח דמה"}
    profile = {}
    intake_row = None
    tochnit_row = None
    sessions = []
    wa_history = []
    risk_flags = []
    score = 0
    breakdown = {}
    strengths = []
    personal_letter = ""

    if supabase is not None:
        try:
            lakoach = supabase.table("users").select("*").eq("id", lakoach_id).single().execute().data
            profile = supabase.table("lakoach_profiles").select("*").eq("user_id", lakoach_id).single().execute().data or {}

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

            sessions = (
                supabase.table("sessions")
                .select("*")
                .eq("lakoach_id", lakoach_id)
                .order("scheduled_at", desc=True)
                .limit(10)
                .execute()
                .data
                or []
            )
            wa_history = (
                supabase.table("wa_messages")
                .select("*")
                .eq("user_id", lakoach_id)
                .order("sent_at", desc=True)
                .limit(20)
                .execute()
                .data
                or []
            )
            risk_flags = calculate_risk_flags(lakoach_id)

            ai_result = intake_row.get("ai_assessment") if intake_row else {} or {}
            score = ai_result.get("resilience_score", 0)
            breakdown = ai_result.get("breakdown", {})
            strengths = ai_result.get("strengths", [])
            personal_letter = ai_result.get("personal_letter", "")
        except Exception:
            logger.exception("Failed to load care_manager profile for %s", lakoach_id)

    return render_template(
        "care_manager/lakoach.html",
        lakoach=lakoach,
        profile=profile,
        intake=intake_row,
        tochnit=tochnit_row,
        sessions=sessions,
        wa_history=wa_history,
        risk_flags=risk_flags,
        score=score,
        breakdown=breakdown,
        strengths=strengths,
        personal_letter=personal_letter,
    )
