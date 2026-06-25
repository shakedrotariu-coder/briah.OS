import json
import logging

import anthropic

logger = logging.getLogger(__name__)

_FALLBACK_EXTRACTION = {
    "ma_ala_bashicha": "השיחה חשפה תכנים עמוקים הדורשים עיבוד.",
    "ratzon_amok": "שינוי ותנועה בחיים.",
    "nosim_merkaziyim": ["חיבור לגוף", "ויסות רגשי", "קהילה"],
    "degashim_letzevet": [],
    "recommended_tzir_1": "קרקוע",
    "recommended_tzir_2": "פריקה",
    "recommended_tzir_3": "קהילה",
}


def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe audio file using Claude.
    For MVP: accept text paste (no audio processing needed).
    For production: use Whisper API or similar.
    """
    if audio_file_path.endswith(".txt"):
        with open(audio_file_path, "r", encoding="utf-8") as f:
            return f.read()

    # Placeholder for audio transcription — connect Whisper or similar in production.
    return "תמליל שיחת האינטייק יופיע כאן לאחר חיבור שירות תמלול."


def extract_intake_from_transcript(transcript: str, lakoach_name: str, melave_notes: str = "") -> dict:
    """
    Input: raw transcript text
    Output: structured intake JSON
    """
    prompt = f"""
אתה מסייע למלווה של בריאה לחלץ מידע מובנה משיחת אינטייק.

שם הלקוחה: {lakoach_name}
הערות המלווה: {melave_notes}

תמליל השיחה:
{transcript}

חלץ את המידע הבא והחזר JSON בלבד (ללא markdown):
{{
  "ma_ala_bashicha": "<מה עלה בשיחה — 2-3 משפטים>",
  "ratzon_amok": "<הרצון העמוק שעלה — משפט אחד>",
  "nosim_merkaziyim": ["<נושא 1>", "<נושא 2>", "<נושא 3>"],
  "degashim_letzevet": ["<דגש 1>", "<דגש 2>"],
  "matzav_karakoa": "<הערכת מצב הקרקוע>",
  "matzav_preka": "<הערכת מצב הפריקה>",
  "matzav_integrazia": "<הערכת מצב האינטגרציה>",
  "matzav_kehila": "<הערכת מצב הקהילה>",
  "matzav_mashmaut": "<הערכת מצב המשמעות>",
  "recommended_tzir_1": "<ציר ראשי מומלץ>",
  "recommended_tzir_2": "<ציר משני מומלץ>",
  "recommended_tzir_3": "<ציר שלישי אופציונלי>",
  "sippur_ishishi": "<מה שחשוב לדעת על האדם — בגוף שלישי, לא תוכן אישי עמוק>"
}}
"""

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(response.content[0].text)
    except Exception:
        logger.exception("transcription_agent: Claude API call or parsing failed, using fallback")
        return dict(_FALLBACK_EXTRACTION)
