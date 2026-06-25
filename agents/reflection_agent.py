import json
import logging

import anthropic

logger = logging.getLogger(__name__)

_BELONGING_KEYS = [
    "feeling_seen", "feeling_belong", "feeling_safe",
    "feeling_supported", "liuvy_meaningful", "feeling_held",
]
_WELLBEING_KEYS = [
    "resilience", "tools", "body_connect", "daily_use", "direction", "general",
]

_FALLBACK_RESULT = {
    "summary": "לא ניתן לנתח — שגיאה טכנית",
    "risk_flags": [],
    "strengths_this_month": [],
    "areas_of_concern": [],
    "progress_vs_last_month": "",
    "recommended_adjustments": [],
    "melave_note": "",
    "community_needs": "",
    "content_feedback": "",
    "overall_status": "progressing",
}


def _to_float(val) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def analyze_reflection(reflection_data: dict, lakoach_name: str, month_num: int, prev_reflections: list = None) -> dict:
    """
    Input: monthly reflection answers + history
    Output: structured analysis for the care team
    """
    belonging_scores = {key: _to_float(reflection_data.get(key, 0)) for key in _BELONGING_KEYS}
    wellbeing_scores = {key: _to_float(reflection_data.get(key, 0)) for key in _WELLBEING_KEYS}

    avg_belonging = sum(belonging_scores.values()) / len(belonging_scores) if belonging_scores else 0
    avg_wellbeing = sum(wellbeing_scores.values()) / len(wellbeing_scores) if wellbeing_scores else 0

    trend_text = ""
    if prev_reflections:
        prev_wb = prev_reflections[-1].get("avg_wellbeing", 0)
        trend = avg_wellbeing - prev_wb
        trend_text = f"שינוי מהחודש הקודם: {'↑ +' if trend > 0 else '↓ '}{abs(trend):.1f} נקודות"

    prompt = f"""
אתה מנתח רפלקציה חודשית עבור צוות בריאה — מרחב ריפוי הוליסטי.

שמה של המשתתפת: {lakoach_name}
חודש מספר: {month_num}

נתוני הרפלקציה:
{json.dumps(reflection_data, ensure_ascii=False, indent=2)}

ציונים מחושבים:
- ממוצע שייכות/מוחזקות: {avg_belonging:.1f}/5
- ממוצע רווחה אישית: {avg_wellbeing:.1f}/5
- תרומה כוללת: {reflection_data.get('contribution', 0)}/5
{trend_text}

נתח את הרפלקציה והחזר JSON בלבד (ללא markdown):
{{
  "summary": "<סיכום 2-3 משפטים של הרפלקציה הכוללת>",
  "risk_flags": [
    {{
      "severity": "high|medium|low",
      "area": "<תחום — שייכות/רווחה/נשירה/תוכן>",
      "description": "<מה מדאיג ומדוע>",
      "recommended_action": "<מה כדאי לעשות>"
    }}
  ],
  "strengths_this_month": ["<חוזק 1>", "<חוזק 2>"],
  "areas_of_concern": ["<נקודה 1>", "<נקודה 2>"],
  "progress_vs_last_month": "<השוואה לחודש קודם — אם יש היסטוריה>",
  "recommended_adjustments": ["<המלצה לשינוי בתוכנית 1>", "<המלצה 2>"],
  "melave_note": "<הערה ישירה למלווה — מה לשים לב, מה לדון בשיחת הליווי>",
  "community_needs": "<האם יש צורך שעלה בנוגע לקהילה?>",
  "content_feedback": "<פידבק על תוכן/לוז שכדאי להעביר לצוות>",
  "overall_status": "flourishing|progressing|plateau|at_risk|needs_attention"
}}

חוקי קריטיים:
- אם avg_belonging < 2.5 → risk_flag HIGH
- אם contribution <= 2 → risk_flag HIGH
- אם "חסר לי" כולל מילות מצוקה → risk_flag MEDIUM
- אם recommendation = "לא ממש" → risk_flag MEDIUM
- הטון תמיד חם, לא קליני
"""

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        result = json.loads(response.content[0].text)
    except Exception:
        logger.exception("reflection_agent: Claude API call or parsing failed, using fallback")
        result = dict(_FALLBACK_RESULT)

    result["avg_belonging"] = round(avg_belonging, 2)
    result["avg_wellbeing"] = round(avg_wellbeing, 2)
    result["belonging_scores"] = belonging_scores
    result["wellbeing_scores"] = wellbeing_scores
    return result
