import logging
import os

from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

logger = logging.getLogger(__name__)

TWILIO_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")


def get_client():
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    if not sid or not token:
        return None
    return Client(sid, token)


def send_whatsapp(to_phone: str, message: str) -> bool:
    client = get_client()
    if client is None:
        print(f"DEV: WhatsApp to {to_phone} -> {message}", flush=True)
        return False

    try:
        client.messages.create(from_=TWILIO_FROM, to=f"whatsapp:{to_phone}", body=message)
        return True
    except Exception:
        logger.exception("Failed to send WhatsApp message to %s", to_phone)
        return False


def send_daily_checkin(to_phone: str, name: str, step_name: str = None) -> bool:
    msg = f"בוקר טוב {name} 🌿\n"
    if step_name:
        msg += f"היום ב-{step_name}:\n"
    msg += "איך את מרגישה הבוקר?\nענה/י במספר: 1 (קשה) עד 5 (מצוין)"
    return send_whatsapp(to_phone, msg)


def send_milestone(to_phone: str, name: str, milestone: str) -> bool:
    msg = f"🌟 {name}!\n{milestone}\nבריאה מתרגשת ממסעך 🤍"
    return send_whatsapp(to_phone, msg)


def send_reminder(to_phone: str, name: str, activity: str, time: str) -> bool:
    msg = f"תזכורת עבורך {name} 🌿\nהיום ב-{time}: {activity}\nנשמח לראות אותך 🤍"
    return send_whatsapp(to_phone, msg)


def make_twiml_response(text: str) -> str:
    resp = MessagingResponse()
    resp.message(text)
    return str(resp)
