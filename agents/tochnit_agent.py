import json
import logging

from openai import OpenAI

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
    "mikhtav_ishishi": "",
    "matarat_ha_tihlich": ["חיבור לגוף", "ויסות רגשי", "תחושת שייכות"],
    "executive_summary": "",
    "main_objectives": [],
    "action_plan": "",
    "action_steps": [],
    "recommendations": [],
    "challenges": [],
    "solutions": [],
    "milestones": [],
    "final_summary": "",
}


def _build_prompt(intake_data: dict, lakoach_name: str, mashlul: str, onboarding_data: dict) -> tuple:
    all_data = {**onboarding_data, **intake_data}

    mashlul_names = {
        "ikur": "עיקור (פוסט-טראומה / מצב קיצוני)",
        "tzmiha": "צמיחה (התפתחות אישית)",
        "hamakata": "הקלה (ניהול יומיומי)",
    }
    mashlul_label = mashlul_names.get(mashlul, mashlul)

    system_prompt = (
        'אתה ארכיטקט תוכניות טיפוליות בכיר בבריאה — פלטפורמת חוסן ובריאות נפשית המבוססת על מחקרי ד"ר בסל ואן דר קולק.\n\n'
        "תפקידך ליצור תוכנית ריפוי אישית מעמיקה שמרגישה כאילו נכתבה על ידי מטפל מנוסה שבילה שעות עם האדם הספציפי הזה.\n\n"
        "חמשת מישורי בריאה:\n"
        "- קרקוע: ביטחון פיזיולוגי במערכת העצבים\n"
        "- פריקה: שחרור מתח ואנרגיה אצורה\n"
        "- אינטגרציה: חיבור גוף-נפש ועיבוד רגשי\n"
        "- קהילה: תחושת שייכות וחיבור\n"
        "- משמעות: כיוון וערך פנימי\n\n"
        "לפני שתכתוב, חשוב צעד אחר צעד:\n"
        "1. מה האתגר המרכזי של האדם הזה? מה מייחד אותו?\n"
        "2. מה החוזקות הנסתרות שלו?\n"
        "3. מה המצב הספציפי שלו דורש — בעדינות, לא בגנריות?\n"
        "4. כיצד 5 המישורים מתחברים לסיפור הייחודי שלו?\n"
        "5. מה באמת יעזור — לא מה שנשמע טיפולי?\n\n"
        "הטון: חם, אנושי, ישיר. לא קליני. לא תבנית. לא גנרי."
    )

    sections = []

    personal = []
    if all_data.get("full_name"): personal.append(f"שם: {all_data['full_name']}")
    if all_data.get("age"): personal.append(f"גיל: {all_data['age']}")
    if all_data.get("city"): personal.append(f"עיר: {all_data['city']}")
    if all_data.get("about_me"): personal.append(f"על עצמה: {all_data['about_me']}")
    if personal:
        sections.append("=== פרטים אישיים ===\n" + "\n".join(personal))

    situation = []
    if all_data.get("what_brought_you"): situation.append(f"מה הביא אותה: {all_data['what_brought_you']}")
    if all_data.get("main_concerns"): situation.append(f"דאגות עיקריות: {all_data['main_concerns']}")
    if all_data.get("where_i_am"): situation.append(f"איפה היא נמצאת: {all_data['where_i_am']}")
    if all_data.get("hopes"): situation.append(f"תקוות: {all_data['hopes']}")
    if situation:
        sections.append("=== מצב נוכחי ===\n" + "\n".join(situation))

    prefs = []
    if all_data.get("what_helps"): prefs.append(f"מה עוזר לה: {all_data['what_helps']}")
    if all_data.get("interests"): prefs.append(f"תחומי עניין: {all_data['interests']}")
    if all_data.get("challenges"): prefs.append(f"אתגרים: {all_data['challenges']}")
    if all_data.get("past_experience"): prefs.append(f"ניסיון עבר: {all_data['past_experience']}")
    if all_data.get("not_interested"): prefs.append(f"לא מעוניינת ב: {all_data['not_interested']}")
    if prefs:
        sections.append("=== העדפות וניסיון ===\n" + "\n".join(prefs))

    clinical = []
    if all_data.get("emotional_background"): clinical.append(f"רקע רגשי: {all_data['emotional_background']}")
    if all_data.get("in_treatment"): clinical.append(f"בטיפול: {all_data['in_treatment']}")
    if all_data.get("treatment_details"): clinical.append(f"פרטי טיפול: {all_data['treatment_details']}")
    if all_data.get("medical_status"): clinical.append(f"מצב רפואי: {all_data['medical_status']}")
    if all_data.get("safety_needs"): clinical.append(f"צרכי ביטחון: {all_data['safety_needs']}")
    if clinical:
        sections.append("=== רקע קליני ===\n" + "\n".join(clinical))

    goals = []
    if all_data.get("therapy_goals"): goals.append(f"מטרות טיפול: {all_data['therapy_goals']}")
    if all_data.get("one_goal"): goals.append(f"מטרה אחת חשובה: {all_data['one_goal']}")
    if all_data.get("therapy_type"): goals.append(f"סוג טיפול מועדף: {all_data['therapy_type']}")
    if all_data.get("mashlul_reason"): goals.append(f"סיבה למסלול: {all_data['mashlul_reason']}")
    if all_data.get("anything_else"): goals.append(f"נוסף: {all_data['anything_else']}")
    if goals:
        sections.append("=== מטרות ===\n" + "\n".join(goals))

    intake_parts = []
    if intake_data.get("ma_ala_bashicha"): intake_parts.append(f"מה עלה בשיחה: {intake_data['ma_ala_bashicha']}")
    if intake_data.get("ratzon_amok"): intake_parts.append(f"רצון עמוק: {intake_data['ratzon_amok']}")
    if intake_data.get("nosim_merkaziyim"): intake_parts.append(f"נושאים מרכזיים: {intake_data['nosim_merkaziyim']}")
    if intake_parts:
        sections.append("=== תמצית שיחת אינטייק ===\n" + "\n".join(intake_parts))

    user_prompt = (
        f"לקוחה: {lakoach_name}\n"
        f"מסלול: {mashlul_label}\n\n"
        + "\n\n".join(sections)
        + f"\n\nפעילויות בריאה זמינות:\n{json.dumps(AVAILABLE_ACTIVITIES, ensure_ascii=False)}\n\n"
        "צורי תוכנית ריפוי אישית מלאה. החזירי JSON בלבד (ללא markdown, ללא ```):\n\n"
        '{\n'
        '  "executive_summary": "<סיכום מצב המטופלת — 3-4 משפטים אישיים וחדים, לא גנריים>",\n'
        '  "main_objectives": ["<מטרה ראשית 1>", "<מטרה ראשית 2>", "<מטרה ראשית 3>"],\n'
        '  "action_plan": "<תיאור כללי של התוכנית — 2-3 משפטים המסבירים את הגישה>",\n'
        '  "action_steps": [\n'
        '    {"step": "<שם הצעד>", "description": "<מה עושים ולמה — משפט אחד ישיר>"},\n'
        '    {"step": "<שם הצעד>", "description": "<הסבר>"},\n'
        '    {"step": "<שם הצעד>", "description": "<הסבר>"},\n'
        '    {"step": "<שם הצעד>", "description": "<הסבר>"}\n'
        '  ],\n'
        '  "recommendations": ["<המלצה ספציפית 1>", "<המלצה 2>", "<המלצה 3>", "<המלצה 4>"],\n'
        '  "challenges": ["<אתגר צפוי 1>", "<אתגר צפוי 2>", "<אתגר צפוי 3>"],\n'
        '  "solutions": ["<פתרון לאתגר 1>", "<פתרון לאתגר 2>", "<פתרון לאתגר 3>"],\n'
        '  "milestones": ["<אבן דרך שבוע 2>", "<אבן דרך חודש 1>", "<אבן דרך חודש 2>", "<אבן דרך חודש 3>"],\n'
        '  "final_summary": "<סיום מחמם ומעצים — 2-3 משפטים שמחזקים את הבחירה שלה>",\n'
        f'  "tzir_1": {{"name": "<שם הציר>", "layer": "<karakoa/preka/integrazia/kehila/mashmaut>", "hesber": "<למה מתאים לה>", "icon": "<אמוג׳י>"}},\n'
        f'  "tzir_2": {{"name": "<שם הציר>", "layer": "<layer>", "hesber": "<הסבר>", "icon": "<אמוג׳י>"}},\n'
        f'  "tzir_3": {{"name": "<שם הציר>", "layer": "<layer>", "hesber": "<הסבר>", "icon": "<אמוג׳י>"}},\n'
        '  "paaluyot": [\n'
        '    {"name": "<שם מהרשימה>", "layer": "<layer>", "tifkud": "<תדירות>", "support": "<איך עוזר לה ספציפית>"},\n'
        '    {"name": "<שם>", "layer": "<layer>", "tifkud": "<תדירות>", "support": "<תמיכה>"},\n'
        '    {"name": "<שם>", "layer": "<layer>", "tifkud": "<תדירות>", "support": "<תמיכה>"},\n'
        '    {"name": "<שם>", "layer": "<layer>", "tifkud": "<תדירות>", "support": "<תמיכה>"}\n'
        '  ],\n'
        f'  "mikhtav_ishishi": "<מכתב אישי ל{lakoach_name} — חם, ישיר, בטון בריאה. מתחיל ב\'{lakoach_name} יקרה,\'>",\n'
        '  "matarat_ha_tihlich": ["<מטרה 1>", "<מטרה 2>", "<מטרה 3>"]\n'
        '}'
    )

    return system_prompt, user_prompt


def _call_openai(system_prompt: str, user_prompt: str) -> str:
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=3000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


def _parse_response(raw_text: str) -> dict:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[1:end])
    return json.loads(text.strip())


def build_tochnit(intake_data: dict, lakoach_name: str, mashlul: str = "tzmiha", onboarding_data: dict = None) -> dict:
    system_prompt, user_prompt = _build_prompt(intake_data, lakoach_name, mashlul, onboarding_data or {})

    try:
        raw = _call_openai(system_prompt, user_prompt)
        return _parse_response(raw)
    except Exception:
        logger.exception("tochnit_agent: OpenAI call or parsing failed, using fallback")
        return dict(
            _FALLBACK_TOCHNIT,
            mikhtav_ishishi=(
                f"{lakoach_name} יקרה,\n\n"
                "תודה על הפתיחות והלב שהבאת לשיחה.\n"
                "אנחנו כאן איתך לאורך הדרך 🤍\n\n"
                "בריאה"
            ),
        )
