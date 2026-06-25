import json
import logging
import os

import anthropic

logger = logging.getLogger(__name__)

_FALLBACK_EXTRACTION = {
    "ma_ala_bashicha": "השיחה חשפה תכנים משמעותיים הדורשים עיבוד.",
    "ratzon_amok": "שינוי ותנועה בחיים.",
    "nosim_merkaziyim": ["חיבור לגוף", "ויסות רגשי", "קהילה"],
    "degashim_letzevet": [],
    "recommended_tzir_1": "קרקוע",
    "recommended_tzir_2": "פריקה",
    "recommended_tzir_3": "קהילה",
}


def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe audio file using OpenAI Whisper API.
    Supports: mp3, mp4, mpeg, mpga, m4a, wav, webm (max 25MB).
    Falls back to reading the file as text if it's a .txt file.
    """
    if audio_file_path.endswith(".txt"):
        with open(audio_file_path, "r", encoding="utf-8") as f:
            return f.read()

    openai_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_key:
        return "[תמלול לא זמין — חסר OPENAI_API_KEY. ניתן להדביק תמלול ידני בשדה למטה]"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=openai_key)
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="he",
                response_format="text",
            )
        return transcript
    except Exception as e:
        logger.exception("Whisper transcription failed for %s", audio_file_path)
        return f"[תמלול נכשל: {str(e)[:100]}. ניתן להדביק תמלול ידני]"


def extract_intake_from_transcript(transcript: str, lakoach_name: str, melave_notes: str = "") -> dict:
    """
    Input: raw transcript (Hebrew text)
    Output: structured intake JSON via Claude
    """
    if not transcript or transcript.startswith("[תמלול"):
        return {
            "ma_ala_bashicha": "טרם הושלם תמלול — יש להדביק תמלול ידנית",
            "ratzon_amok": "",
            "nosim_merkaziyim": [],
            "degashim_letzevet": [],
            "recommended_tzir_1": "קרקוע",
            "recommended_tzir_2": "פריקה",
            "recommended_tzir_3": "קהילה",
        }

    prompt = f"""
אתה מסייע למלווה של בריאה לחלץ מידע מובנה משיחת אינטייק.

שם הלקוחה: {lakoach_name}
הערות המלווה: {melave_notes or "אין הערות נוספות"}

תמליל השיחה:
---
{transcript[:4000]}
---

חלץ את המידע הבא והחזר JSON בלבד (ללא markdown, ללא ```):
{{
  "ma_ala_bashicha": "<מה עלה בשיחה — 2-3 משפטים חמים>",
  "ratzon_amok": "<הרצון העמוק שעלה — משפט אחד>",
  "nosim_merkaziyim": ["<נושא 1>", "<נושא 2>", "<נושא 3>"],
  "degashim_letzevet": ["<דגש לצוות 1>", "<דגש לצוות 2>"],
  "matzav_karakoa": "<הערכת מצב הקרקוע בקצרה>",
  "matzav_preka": "<הערכת מצב הפריקה>",
  "matzav_integrazia": "<הערכת מצב האינטגרציה>",
  "matzav_kehila": "<הערכת מצב הקהילה>",
  "matzav_mashmaut": "<הערכת מצב המשמעות>",
  "recommended_tzir_1": "<ציר ראשי מומלץ מחמשת המישורים>",
  "recommended_tzir_2": "<ציר משני מומלץ>",
  "recommended_tzir_3": "<ציר שלישי אופציונלי>"
}}
"""

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception:
        logger.exception("transcription_agent: Claude extraction failed, using fallback")
        return dict(_FALLBACK_EXTRACTION)
