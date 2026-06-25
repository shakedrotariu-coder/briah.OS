import json
import logging

import anthropic

logger = logging.getLogger(__name__)

_FALLBACK_RESULT = {
    "resilience_score": 65,
    "breakdown": {"karakoa": 60, "preka": 55, "integrazia": 65, "kehila": 70, "mashmaut": 60},
    "primary_focus": "preka",
    "strengths": ["פתיחות", "מוטיבציה לשינוי"],
    "growth_areas": ["חיבור לגוף", "ויסות רגשי"],
    "journey_type": "moderate",
    "recommended_activities": ["יוגה סומטית", "ריברסינג", "מעגל נשים"],
    "summary_he": "השאלון מגלה אדם שמחפש שינוי עמוק.",
    "personal_letter": "שלום יקרה, תודה על הפתיחות.",
}


def analyze_intake(answers: dict, lakoach_name: str) -> dict:
    """
    Input: dict of answers {q1: value, q2: value, ...}
    Output: {
        resilience_score, breakdown (5 layers), primary_focus,
        strengths, growth_areas, personal_letter, journey_type,
        recommended_activities, summary_he
    }
    """
    prompt = f"""
אתה AI מומחה של בריאה — פלטפורמת ריפוי המבוססת על מחקרי ד"ר בסל ואן דר קולק.

חמשת מישורי בריאה:
- קרקוע: ביטחון פיזיולוגי במערכת העצבים
- פריקה: שחרור מתח ואנרגיה אצורה
- אינטגרציה: חיבור גוף-נפש ועיבוד רגשי
- קהילה: תחושת שייכות וחיבור
- משמעות: כיוון וערך פנימי

הלקוחה: {lakoach_name}

תשובות השאלון:
{json.dumps(answers, ensure_ascii=False, indent=2)}

מידע על הסולם: 1=נמוך מאוד, 5=גבוה מאוד
שאלות טקסט: תשובות פתוחות

נתח את התשובות והחזר JSON בלבד (ללא markdown):
{{
  "resilience_score": <מספר 0-100 המשקף חוסן כללי>,
  "breakdown": {{
    "karakoa": <0-100>,
    "preka": <0-100>,
    "integrazia": <0-100>,
    "kehila": <0-100>,
    "mashmaut": <0-100>
  }},
  "primary_focus": "<המישור שדורש הכי הרבה תשומת לב>",
  "strengths": ["<חוזק 1>", "<חוזק 2>", "<חוזק 3>"],
  "growth_areas": ["<תחום צמיחה 1>", "<תחום צמיחה 2>"],
  "journey_type": "<gentle|moderate|intensive>",
  "recommended_activities": ["<פעילות 1 מהרשימה>", "<פעילות 2>", "<פעילות 3>"],
  "summary_he": "<2-3 משפטים חמים, אישיים, לא קליניים — מה שעלה מהשאלון>",
  "personal_letter": "<מכתב אישי קצר ל{lakoach_name} בטון חם של בריאה, מה ראינו בה, מה אנחנו מזמינים אותה לעשות>"
}}

פעילויות בריאה הקיימות (בחר מהרשימה):
יוגה סומטית, ריברסינג, אקסטטיק דאנס, סאונד הילינג, ביטוי קולי,
מדיטציה, דמיון מודרך, כתיבה אינטגרטיבית, מעגל נשים, הרצאות, טיפול 1:1

חשוב: הטון צריך להיות חם, אנושי, מחזיק — לא קליני ולא מאובחן.
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
        logger.exception("intake_agent: Claude API call or parsing failed, using fallback result")
        return dict(_FALLBACK_RESULT, personal_letter=f"שלום {lakoach_name}, תודה על הפתיחות.")
