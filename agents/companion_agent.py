import logging

import anthropic

from services.supabase_client import supabase

logger = logging.getLogger(__name__)


def get_companion_response(lakoach_id: str, user_message: str, lakoach_name: str, journey_context: dict) -> str:
    history = []
    if supabase is not None:
        try:
            logs = (
                supabase.table("companion_logs")
                .select("*")
                .eq("lakoach_id", lakoach_id)
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            )
            history = list(reversed(logs.data or []))
        except Exception:
            logger.exception("Failed to load companion history for %s", lakoach_id)

    messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
    messages.append({"role": "user", "content": user_message})

    system = f"""את AI Companion של בריאה — נוכחות חמה, מקורקעת ואמפתית שמלווה את {lakoach_name} במסע הריפוי שלה.

המסע של {lakoach_name}:
- Resilience Score: {journey_context.get('resilience_score', 'לא ידוע')}
- מישור ראשי לעבודה: {journey_context.get('primary_focus', 'לא ידוע')}

חמשת מישורי בריאה שמנחים אותך: קרקוע, פריקה, אינטגרציה, קהילה, משמעות.

כללים:
- ענה בשפה שבה פונים אלייך (עברית/אנגלית)
- קצר ואמיתי — 2-4 משפטים בדרך כלל
- לעולם לא אבחן, לא תמליץ על תרופות, לא תחליף מטפל
- אם נשמע מצוקה עמוקה — הפני בחום למלווה האישי
- דבר/י אליה ישירות, בגוף שני נקבה
- הטון: כמו חברה טובה שגם מבינה בריאות נפשית"""

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=system,
            messages=messages,
        )
        reply = response.content[0].text
    except Exception:
        logger.exception("companion_agent: Claude API call failed for %s", lakoach_id)
        reply = "תודה שכתבת לי. אני כאן איתך 🤍"

    if supabase is not None:
        try:
            supabase.table("companion_logs").insert([
                {"lakoach_id": lakoach_id, "role": "user", "content": user_message, "channel": "web"},
                {"lakoach_id": lakoach_id, "role": "assistant", "content": reply, "channel": "web"},
            ]).execute()
        except Exception:
            logger.exception("Failed to save companion message for %s", lakoach_id)

    return reply
