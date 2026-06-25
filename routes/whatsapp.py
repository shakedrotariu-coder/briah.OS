import logging
import os

from flask import Blueprint, Response, request

from agents.companion_agent import get_companion_response
from services.supabase_client import supabase
from services.whatsapp_service import make_twiml_response, send_daily_checkin

wa_bp = Blueprint("whatsapp", __name__)
logger = logging.getLogger(__name__)


@wa_bp.route("/whatsapp", methods=["POST"])
def webhook():
    """Receive incoming WhatsApp messages from Twilio."""
    incoming_msg = request.form.get("Body", "").strip()
    from_number = request.form.get("From", "").replace("whatsapp:", "")

    if not incoming_msg or not from_number:
        return Response(make_twiml_response(""), mimetype="text/xml")

    if supabase is None:
        logger.info("DEV: WhatsApp inbound from %s: %s", from_number, incoming_msg)
        return Response(make_twiml_response("שלום 🌿 (מצב פיתוח — Supabase לא מחובר)"), mimetype="text/xml")

    try:
        user_result = supabase.table("users").select("*").eq("phone", from_number).limit(1).execute().data

        if not user_result:
            reply = "שלום! 🌿 לא מצאנו את מספרך במערכת. פנה/י לבריאה."
            return Response(make_twiml_response(reply), mimetype="text/xml")

        user = user_result[0]
        uid = user["id"]

        supabase.table("wa_messages").insert({
            "user_id": uid,
            "direction": "inbound",
            "body": incoming_msg,
        }).execute()

        if incoming_msg in ["1", "2", "3", "4", "5"]:
            score = int(incoming_msg)
            supabase.table("companion_logs").insert({
                "lakoach_id": uid,
                "role": "user",
                "content": f"צ׳ק-אין יומי: {score}/5",
                "channel": "whatsapp",
            }).execute()

            if score <= 2:
                reply = "תודה שענית 🤍 נשמע שהיום קצת כבד. זכרי — המלווה שלך כאן בשבילך. יש לנו אותך."
            elif score == 3:
                reply = "תודה! יום בינוני — אלו גם ימים חשובים במסע 🌿 מה עוזר לך להתמקד היום?"
            else:
                reply = f"מדהים! {score}/5 — זה נשמע כמו יום טוב 🌟 מה מרגיש טוב?"

            supabase.table("companion_logs").insert({
                "lakoach_id": uid,
                "role": "assistant",
                "content": reply,
                "channel": "whatsapp",
            }).execute()
            supabase.table("wa_messages").insert({
                "user_id": uid,
                "direction": "outbound",
                "body": reply,
            }).execute()
        else:
            ctx = {}
            try:
                intake_res = (
                    supabase.table("intakes")
                    .select("ai_assessment")
                    .eq("lakoach_id", uid)
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                    .data
                )
                if intake_res:
                    ctx = intake_res[0].get("ai_assessment") or {}
            except Exception:
                logger.exception("Failed to load journey context for %s", uid)

            reply = get_companion_response(uid, incoming_msg, user.get("full_name", ""), ctx)
            supabase.table("wa_messages").insert({
                "user_id": uid,
                "direction": "outbound",
                "body": reply,
            }).execute()

        return Response(make_twiml_response(reply), mimetype="text/xml")

    except Exception:
        logger.exception("WhatsApp webhook failed for %s", from_number)
        reply = "מצטערים, הייתה בעיה. ננסה שוב 🤍"
        return Response(make_twiml_response(reply), mimetype="text/xml")


@wa_bp.route("/whatsapp/send-checkins", methods=["POST"])
def send_checkins():
    """Internal endpoint — send daily check-ins to all active users."""
    secret = request.headers.get("X-Internal-Secret", "")
    if secret != os.getenv("INTERNAL_SECRET", "briah-internal"):
        return {"error": "unauthorized"}, 401

    if supabase is None:
        return {"sent": 0, "failed": 0, "note": "Supabase not configured"}

    try:
        profiles = (
            supabase.table("lakoach_profiles").select("*, users(*)").eq("status", "active").execute().data or []
        )

        sent, failed = 0, 0
        for p in profiles:
            user = p.get("users") or {}
            phone = user.get("phone", "")
            name = user.get("full_name", "")
            if phone and user.get("wa_opted_in"):
                ok = send_daily_checkin(phone, name)
                if ok:
                    sent += 1
                else:
                    failed += 1

        return {"sent": sent, "failed": failed}
    except Exception as e:
        logger.exception("Failed to send daily checkins")
        return {"error": str(e)}, 500
