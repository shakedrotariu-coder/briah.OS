import json
import logging

import anthropic

logger = logging.getLogger(__name__)

AVAILABLE_ACTIVITIES = [
    {"name": "יוגה סומטית", "layer": "karakoa", "type": "group", "frequency": "שבועי"},
    {"name": "ריברסינג", "layer": "preka", "type": "group", "frequency": "דו-שבועי"},
    {"name": "אקסטטיק דאנס", "layer": "preka", "type": "group", "frequency": "שבועי"},
    {"name": "סאונד הילינג", "layer": "karakoa", "type": "group", "frequency": "שבועי"},
    {"name": "ביטוי קולי", "layer": "preka", "type": "group", "frequency": "שבועי"},
    {"name": "מדיטציה בזום", "layer": "mashmaut", "type": "group", "frequency": "יומי"},
    {"name": "דמיון מודרך", "layer": "integrazia", "type": "group", "frequency": "דו-שבועי"},
    {"name": "כתיבה אינטגרטיבית", "layer": "integrazia", "type": "group", "frequency": "שבועי"},
    {"name": "מעגל נשים", "layer": "kehila", "type": "group", "frequency": "חודשי"},
    {"name": "הרצאות", "layer": "kehila", "type": "group", "frequency": "חודשי"},
    {"name": "טיפול 1:1", "layer": "integrazia", "type": "personal", "frequency": "שבועי"},
]

_FALLBACK_TOCHNIT = {
    "tzir_1": {"name": "קרקוע", "layer": "karakoa", "hesber": "יצירת בסיס בטוח ורגוע", "icon": "🌱"},
    "tzir_2": {"name": "פריקה", "layer": "preka", "hesber": "שחרור מתחים אצורים", "icon": "🌊"},
    "tzir_3": {"name": "קהילה", "layer": "kehila", "hesber": "תחושת שייכות וחיבור", "icon": "🤍"},
    "paaluyot": AVAILABLE_ACTIVITIES[:4],
    "matarat_ha_tihlich": ["חיבור לגוף", "ויסות רגשי", "תחושת שייכות"],
}


def build_tochnit(intake_data: dict, lakoach_name: str, mashlul: str = "tzmiha") -> dict:
    """
    Input: intake extraction dict + lakoach info
    Output: full tochnit with 3 axes + activities + personal letter
    """
    prompt = f"""
אתה מומחה בניית תוכניות ריפוי אישיות בבריאה.

לקוחה: {lakoach_name}
מסלול: {mashlul}
מה עלה בשיחה: {intake_data.get('ma_ala_bashicha', '')}
רצון עמוק: {intake_data.get('ratzon_amok', '')}
נושאים מרכזיים: {intake_data.get('nosim_merkaziyim', [])}
ציר מומלץ 1: {intake_data.get('recommended_tzir_1', '')}
ציר מומלץ 2: {intake_data.get('recommended_tzir_2', '')}
ציר מומלץ 3: {intake_data.get('recommended_tzir_3', '')}

פעילויות זמינות: {json.dumps(AVAILABLE_ACTIVITIES, ensure_ascii=False)}

בנה תוכנית אישית והחזר JSON בלבד:
{{
  "tzir_1": {{
    "name": "<שם הציר>",
    "layer": "<karakoa/preka/integrazia/kehila/mashmaut>",
    "hesber": "<הסבר קצר — למה הציר הזה מתאים לה>",
    "icon": "<אמוג׳י מתאים>"
  }},
  "tzir_2": {{...}},
  "tzir_3": {{...}},
  "paaluyot": [
    {{
      "name": "<שם הפעילות>",
      "layer": "<שם המישור>",
      "tifkud": "<תדירות>",
      "support": "<איך זה תומך בתהליך — משפט אחד>"
    }}
  ],
  "mikhtav_ishishi": "<מכתב אישי ל{lakoach_name} — חם, ישיר, בטון בריאה. מתחיל ב'[שם] יקרה,'>",
  "matarat_ha_tihlich": ["<מטרה 1>", "<מטרה 2>", "<מטרה 3>"]
}}

הטון: חם, אנושי, לא קליני. מדבר אל האדם, לא עליו.
"""

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(response.content[0].text)
    except Exception:
        logger.exception("tochnit_agent: Claude API call or parsing failed, using fallback")
        return dict(
            _FALLBACK_TOCHNIT,
            mikhtav_ishishi=f"{lakoach_name} יקרה,\n\nתודה על הפתיחות והלב שהבאת לשיחה.\nאנחנו כאן איתך לאורך הדרך 🤍\n\nבריאה",
        )
