import logging
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_NAME = "בריאה — מעטפת לחיים עצמם"

logger = logging.getLogger(__name__)


def _send(msg: MIMEMultipart) -> bool:
    if not SMTP_USER or not SMTP_PASS:
        logger.info("SMTP not configured — printing email instead of sending:\n%s", msg.as_string())
        return False

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", msg.get("To"))
        return False


def send_intake_invite(to_email: str, full_name: str, intake_token: str) -> bool:
    """Send intake invitation email with unique link"""
    intake_url = f"{os.getenv('BASE_URL', 'http://localhost:5000')}/onboarding/{intake_token}"

    html_body = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px;
         margin: 0 auto; background: #fff0db; padding: 40px; border-radius: 24px;">
      <h1 style="font-family: Georgia, serif; color: #634734; font-weight: 400;
                 font-size: 2rem; margin-bottom: 8px;">בריא.ה</h1>
      <p style="color: #8c6b54; margin-bottom: 32px;">מעטפת לחיים עצמם</p>

      <h2 style="color: #634734; font-family: Georgia, serif; font-weight: 400;">
        שלום {full_name} 🤍
      </h2>
      <p style="color: #634734; line-height: 1.8; margin: 16px 0;">
        ברוכה הבאה לבריאה.<br>
        כדי שנוכל להכין את התוכנית האישית שלך,<br>
        אנחנו מזמינים אותך למלא שאלון קצר שיעזור לנו להכיר אותך טוב יותר.
      </p>
      <p style="color: #8c6b54; font-size: 14px; margin-bottom: 32px;">
        השאלון לוקח כ-10 דקות. אין תשובות נכונות או לא נכונות — רק שלך.
      </p>

      <a href="{intake_url}"
         style="background: #a3502e; color: #fff0db; padding: 16px 32px;
                border-radius: 999px; text-decoration: none; font-size: 16px;
                display: inline-block; font-weight: 500;">
        מלאי את השאלון →
      </a>

      <p style="color: #b89a83; font-size: 12px; margin-top: 32px;">
        הלינק תקף ל-7 ימים. לשאלות — briah@briah.co
      </p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "ברוכה הבאה לבריאה — השאלון שלך מחכה 🌿"
    msg["From"] = f"{FROM_NAME} <{SMTP_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    sent = _send(msg)
    if not sent:
        print(f"DEV: intake invite for {to_email} -> {intake_url}", flush=True)
    return sent


def send_assessment_results(to_email: str, full_name: str, assessment_html: str, pdf_bytes: bytes = None) -> bool:
    """Send assessment results with optional PDF attachment"""
    html_body = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px;
         margin: 0 auto; background: #fff0db; padding: 40px; border-radius: 24px;">
      <h1 style="font-family: Georgia, serif; color: #634734; font-weight: 400;
                 font-size: 2rem;">בריא.ה</h1>
      <p style="color: #8c6b54; margin-bottom: 32px;">מעטפת לחיים עצמם</p>

      <h2 style="color: #634734; font-family: Georgia, serif; font-weight: 400;">
        {full_name}, ה-Assessment שלך מוכן 🌿
      </h2>
      <p style="color: #634734; line-height: 1.8; margin: 16px 0;">
        עיבדנו את התשובות שלך ובנינו עבורך תמונה של המצב הנוכחי שלך.<br>
        מצורף המסמך המלא — וגם המלווה שלך כבר רואה את התוצאות.
      </p>

      {assessment_html}

      <p style="color: #b89a83; font-size: 13px; margin-top: 32px; line-height: 1.6;">
        זהו כלי היכרות — לא אבחנה רפואית.<br>
        המלווה שלך יצור איתך קשר בימים הקרובים לבניית התוכנית האישית.
      </p>
    </div>
    """

    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"התוצאות שלך בבריאה — {full_name} 🌿"
    msg["From"] = f"{FROM_NAME} <{SMTP_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if pdf_bytes:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="briah-assessment-{full_name}.pdf"')
        msg.attach(part)

    sent = _send(msg)
    if not sent:
        print(f"DEV: assessment results email for {to_email}\n{html_body}", flush=True)
    return sent
