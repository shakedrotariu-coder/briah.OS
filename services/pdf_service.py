import logging

logger = logging.getLogger(__name__)


def generate_tochnit_pdf(lakoach_name: str, tochnit: dict, ai_result: dict = None) -> bytes:
    """
    Generate a branded Briah personal plan PDF.
    Returns PDF as bytes (empty bytes if WeasyPrint isn't available or generation fails).
    """
    tochnit = tochnit or {}
    ai_result = ai_result or {}

    try:
        from weasyprint import HTML

        html_content = f"""
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@300;400;500&family=Assistant:wght@400;500;600&display=swap');

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Assistant', Arial, sans-serif;
    color: #634734;
    background: #fff0db;
    padding: 40px;
    direction: rtl;
  }}

  .logo {{
    font-family: 'Frank Ruhl Libre', Georgia, serif;
    font-size: 2.4rem;
    font-weight: 400;
    color: #634734;
    margin-bottom: 4px;
  }}

  .tagline {{
    font-size: 13px;
    color: #8c6b54;
    margin-bottom: 40px;
  }}

  .title {{
    font-family: 'Frank Ruhl Libre', Georgia, serif;
    font-size: 1.8rem;
    font-weight: 400;
    color: #634734;
    margin-bottom: 8px;
  }}

  .subtitle {{
    font-size: 14px;
    color: #8c6b54;
    margin-bottom: 32px;
  }}

  .card {{
    background: white;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    border: 1px solid rgba(99,71,52,0.12);
  }}

  .section-title {{
    font-family: 'Frank Ruhl Libre', Georgia, serif;
    font-size: 1.1rem;
    font-weight: 500;
    color: #634734;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(99,71,52,0.1);
  }}

  .score-big {{
    font-family: 'Frank Ruhl Libre', Georgia, serif;
    font-size: 3rem;
    font-weight: 400;
    color: #a3502e;
    text-align: center;
    margin: 8px 0;
  }}

  .layer-row {{
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    gap: 12px;
  }}

  .layer-name {{
    width: 100px;
    font-size: 13px;
    font-weight: 500;
  }}

  .bar-bg {{
    flex: 1;
    height: 8px;
    background: rgba(99,71,52,0.1);
    border-radius: 999px;
    overflow: hidden;
  }}

  .bar-fill {{
    height: 8px;
    background: #a3502e;
    border-radius: 999px;
  }}

  .bar-val {{
    width: 36px;
    font-size: 12px;
    color: #8c6b54;
    text-align: left;
  }}

  .tzir-card {{
    background: rgba(163,168,119,0.1);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
  }}

  .activity-row {{
    padding: 8px 0;
    border-bottom: 1px solid rgba(99,71,52,0.07);
    font-size: 13px;
  }}

  .letter {{
    background: #634734;
    color: #fff0db;
    border-radius: 16px;
    padding: 24px;
    line-height: 1.9;
    font-size: 14px;
    white-space: pre-line;
  }}

  .footer {{
    text-align: center;
    margin-top: 40px;
    font-size: 11px;
    color: #b89a83;
  }}
</style>
</head>
<body>
<div class="logo">בריא.ה</div>
<div class="tagline">מעטפת לחיים עצמם</div>
<div class="title">תוכנית אישית</div>
<div class="subtitle">{lakoach_name}</div>
"""

        if ai_result.get("resilience_score"):
            score = ai_result["resilience_score"]
            breakdown = ai_result.get("breakdown", {})
            html_content += f"""
<div class="card">
  <div class="section-title">Resilience Score</div>
  <div class="score-big">{score}<span style="font-size:1.2rem;color:#8c6b54;">/100</span></div>
  <p style="text-align:center;font-size:13px;color:#8c6b54;margin-bottom:16px;">
    {ai_result.get('summary_he', '')}
  </p>
"""
            layers = [
                ("karakoa", "קרקוע"),
                ("preka", "פריקה"),
                ("integrazia", "אינטגרציה"),
                ("kehila", "קהילה"),
                ("mashmaut", "משמעות"),
            ]
            for key, name in layers:
                val = breakdown.get(key, 0)
                html_content += f"""
  <div class="layer-row">
    <div class="layer-name">{name}</div>
    <div class="bar-bg"><div class="bar-fill" style="width:{val}%"></div></div>
    <div class="bar-val">{val}%</div>
  </div>
"""
            html_content += "</div>"

        paaluyot = tochnit.get("paaluyot", [])
        html_content += '<div class="card"><div class="section-title">על מה נתמקד</div>'
        for tzir_key in ["tzir_1", "tzir_2", "tzir_3"]:
            tzir = tochnit.get(tzir_key)
            if tzir:
                if isinstance(tzir, dict):
                    name = tzir.get("name", tzir_key)
                    hesber = tzir.get("hesber", "")
                else:
                    name = str(tzir)
                    hesber = ""
                html_content += f"""
  <div class="tzir-card">
    <strong>{name}</strong>
    {'<p style="font-size:13px;color:#8c6b54;margin-top:4px;">' + hesber + '</p>' if hesber else ''}
  </div>
"""
        html_content += "</div>"

        if paaluyot:
            html_content += '<div class="card"><div class="section-title">הפעילויות שלך</div>'
            for act in paaluyot[:8]:
                if isinstance(act, dict):
                    name = act.get("name", "")
                    support = act.get("support", "")
                    freq = act.get("tifkud", act.get("frequency", ""))
                else:
                    name = str(act)
                    support = ""
                    freq = ""
                html_content += f"""
  <div class="activity-row">
    <strong>{name}</strong>
    {' · ' + freq if freq else ''}
    {'<br><span style="color:#8c6b54;font-size:12px;">' + support + '</span>' if support else ''}
  </div>
"""
            html_content += "</div>"

        letter = tochnit.get("mikhtav_ishishi") or ai_result.get("personal_letter") or ""
        if letter:
            html_content += f"""
<div class="letter">{letter}</div>
"""

        from datetime import date

        html_content += f"""
<div class="footer">
  בריאה — מעטפת לחיים עצמם · briah.co<br>
  מסמך זה נוצר ב-{date.today().strftime('%d.%m.%Y')}
</div>
</body>
</html>
"""

        return HTML(string=html_content).write_pdf()
    except ImportError:
        logger.warning("WeasyPrint not installed — cannot generate PDF.")
        return b""
    except Exception:
        logger.exception("PDF generation failed for %s", lakoach_name)
        return b""
