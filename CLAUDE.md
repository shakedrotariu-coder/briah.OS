# Briah.OS — בריאה · מעטפת לחיים עצמם
## AI Operating System for Mental Health & Resilience
### Course 55308 | Claude Code Build Guide — Full Frontend + Flask Skeleton

---

## מה זה בריאה? (קונטקסט לכל סוכן AI)

בריאה היא מערכת ליווי טיפולית-קהילתית. כל אדם מקבל מלווה אישי שמנהל איתו שיחת אינטייק,
בונה תוכנית אישית, ומשבץ אותו לסדנאות ומטפלים 1:1 — הכל בתוך מסגרת שמחזיקה אותו לאורך זמן.

### חמשת המישורים של בריאה (לפי ד"ר בסל ואן דר קולק)

1. **קרקוע** — ביטחון פיזיולוגי במערכת העצבים
2. **פריקה** — שחרור מתח ואנרגיה אצורה מהגוף
3. **אינטגרציה** — חיבור בין החוויה הגופנית להבנה תודעתית
4. **קהילה** — מעבר מהאינדיבידואל לתחושת שייכות
5. **משמעות** — חזרה לפעולה מתוך ערך ובהירות פנימית

---

## הזרימה האנושית הקיימת (מה קורה היום, ידנית)

**שלב 1 — רישום**
אדם נרשם לבריאה ← איינב מחליטה מי המלווה שלו/ה

**שלב 2 — שיחת אינטייק (קורה בטלפון/זום)**
המלווה מנהל שיחה חופשית עם הלקוח.
בסיום: המלווה בונה ידנית תוכנית אישית (לפי הפורמט) ושולח ללקוח + לבריאה.

**שלב 3 — שיבוץ**
בריאה (איינב) רושמת את הלקוח לסדנאות ב-Arbox לפי התוכנית.
מטפל 1:1 משובץ — 2 פגישות לחודש.

**שלב 4 — ליווי שוטף**
אחרי חודש — שיחת עדכון עם המלווה (זום, חצי שעה).
לקראת סוף — שיחת סיכום/בדיקת המשך.
המלווה מעלה סיכום קצר אחת לשני טיפולים לתיקיית המטופל בדרייב.

**שלב 5 — העברת מידע לצוות**
כל מטופל מקבל תיקייה: אינטייק + תוכנית אישית + תיקיית סיכומי טיפול.
מטפל 1:1 קורא את האינטייק לפני הפגישה הראשונה.
דגשים: "זקוקה לקרקוע", "רגישות גבוהה למגע", "קושי במרחבים גדולים" וכו'.

---

## מה המערכת הדיגיטלית הזו עושה

### מה משתנה (ידני → דיגיטלי)

| ידני היום | דיגיטלי במערכת |
|---|---|
| המלווה מסכם ידנית שיחת אינטייק | הקלטת השיחה → AI מתמלל → שאלון אינטייק אוטומטי |
| המלווה בונה תוכנית אישית | AI בונה תוכנית אישית לפי פורמט בריאה |
| המלווה שולח תוכנית ל-PDF ידנית | המערכת מייצרת PDF בפורמט בריאה אוטומטית |
| איינב משבצת ידנית ב-Arbox | המערכת מציעה שיבוץ לפי לוז + מטפל זמין |
| תיקיות בדרייב ידנית | CRM מסודר עם כל המסמכים |
| המטפל קורא אינטייק מהדרייב | המטפל רואה דגשים ממוקדים ב-dashboard שלו |

### מה לא משתנה

- השיחה עצמה קורית בין אנשים (לא AI)
- ההחלטה של איינב מי המלווה — ידנית
- קשר אנושי לאורך כל התהליך

---

## ארכיטקטורה — Users & Roles

| Role | מי | רואה |
|---|---|---|
| admin | איינב | כל המערכת, שיבוצים, CRM מלא |
| melave | מלווה | הלקוחות שלו, העלאת הקלטה, עריכת אינטייק |
| metapel | מטפל 1:1 | הלקוחות שלו, דגשים, לוז, העלאת סיכומים |
| lakoach | לקוח | התוכנית שלו, הלוז שלו, AI Companion |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 + Flask |
| Database & Auth | Supabase (PostgreSQL + Row Level Security) |
| AI | Claude API — `claude-sonnet-4-6` |
| WhatsApp | Twilio WhatsApp API |
| Frontend | HTML + CSS + Jinja2 (RTL, Hebrew first) |
| Deployment | Railway |
| PDF | WeasyPrint (לייצור תוכנית אישית PDF) |

---

## מסכים לבנות (Frontend + Flask routes ריקים)

### 1. Login — /login
```
templates/login.html
routes/auth.py → GET/POST /login, GET /logout
```
לוגין עם email + password (Supabase Auth)
Redirect לפי role אחרי לוגין

### 2. Admin Dashboard — /admin
```
templates/admin/dashboard.html
templates/admin/lakoach_new.html      ← הוספת לקוח חדש
templates/admin/shibutz.html          ← מסך שיבוץ מטפל + לוז
routes/admin.py → GET /admin, POST /admin/lakoach, GET /admin/shibutz
```

### 3. מלווה — Melave Dashboard — /melave
```
templates/melave/dashboard.html       ← רשימת הלקוחות שלו
templates/melave/intake.html          ← מסך אינטייק: העלאת הקלטה + עריכה
templates/melave/tochnit.html         ← עריכת תוכנית אישית + שליחה
routes/melave.py → GET /melave, GET/POST /melave/intake/<id>, GET/POST /melave/tochnit/<id>
```

### 4. מטפל 1:1 — Metapel Dashboard — /metapel
```
templates/metapel/dashboard.html      ← לקוחות + לוז השבוע
templates/metapel/lakoach.html        ← פרופיל לקוח + דגשים + היסטוריה
templates/metapel/sikum.html          ← העלאת סיכום טיפול
routes/metapel.py → GET /metapel, GET /metapel/lakoach/<id>, POST /metapel/sikum/<id>
```

### 5. לקוח — Lakoach Dashboard — /lakoach
```
templates/lakoach/dashboard.html      ← תוכנית אישית + לוז החודש
templates/lakoach/companion.html      ← AI Companion chat
routes/lakoach.py → GET /lakoach, POST /lakoach/companion
```

---

## Database Schema

```sql
-- organizations
CREATE TABLE organizations (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name            text NOT NULL,
  resilience_index float,
  created_at      timestamptz DEFAULT now()
);

-- users
CREATE TABLE users (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email           text UNIQUE NOT NULL,
  full_name       text,
  role            text NOT NULL CHECK (role IN ('admin','melave','metapel','lakoach')),
  org_id          uuid REFERENCES organizations(id),
  phone           text,
  wa_opted_in     boolean DEFAULT false,
  created_at      timestamptz DEFAULT now()
);

-- lakoach_profiles (רק ללקוחות)
CREATE TABLE lakoach_profiles (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid REFERENCES users(id) UNIQUE,
  melave_id       uuid REFERENCES users(id),         -- המלווה
  metapel_id      uuid REFERENCES users(id),         -- מטפל 1:1
  mashlul         text CHECK (mashlul IN ('ikur','tzmiha','hamakata')),
  start_date      date,
  status          text DEFAULT 'active'
);

-- intakes (שיחת אינטייק מסוכמת)
CREATE TABLE intakes (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lakoach_id      uuid REFERENCES users(id),
  melave_id       uuid REFERENCES users(id),
  recording_url   text,                              -- קישור להקלטה
  transcript      text,                              -- תמליל AI
  raw_summary     jsonb,                             -- מה ה-AI חילץ
  melave_notes    text,                              -- הערות ידניות של המלווה
  status          text DEFAULT 'draft',
  created_at      timestamptz DEFAULT now()
);

-- tochniyot_ishiyot (תוכניות אישיות)
CREATE TABLE tochniyot_ishiyot (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lakoach_id      uuid REFERENCES users(id),
  intake_id       uuid REFERENCES intakes(id),
  tzir_1          text,    -- ציר ראשון + הסבר
  tzir_2          text,
  tzir_3          text,
  paaluyot        jsonb,   -- רשימת סדנאות + מטפל 1:1
  luz_hodshi      jsonb,   -- לוז החודש
  melave_notes    text,
  sent_at         timestamptz,
  pdf_url         text,
  created_at      timestamptz DEFAULT now()
);

-- sessions (פגישות 1:1)
CREATE TABLE sessions (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lakoach_id      uuid REFERENCES users(id),
  metapel_id      uuid REFERENCES users(id),
  scheduled_at    timestamptz,
  sikum           text,          -- סיכום קצר מהמטפל
  degashim        text,          -- דגשים להעברה לצוות
  status          text DEFAULT 'scheduled',
  created_at      timestamptz DEFAULT now()
);

-- companion_logs (AI Companion)
CREATE TABLE companion_logs (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lakoach_id      uuid REFERENCES users(id),
  role            text CHECK (role IN ('user','assistant')),
  content         text,
  channel         text DEFAULT 'web',
  created_at      timestamptz DEFAULT now()
);

-- wa_messages (WhatsApp)
CREATE TABLE wa_messages (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid REFERENCES users(id),
  direction       text CHECK (direction IN ('inbound','outbound')),
  body            text,
  sent_at         timestamptz DEFAULT now()
);
```

---

## Folder Structure

```
briah-os/
├── app.py
├── requirements.txt
├── Procfile
├── .env
├── CLAUDE.md
│
├── routes/
│   ├── auth.py
│   ├── admin.py
│   ├── melave.py
│   ├── metapel.py
│   └── lakoach.py
│
├── agents/                        ← ריק עכשיו, מחברים אחר כך
│   ├── transcription_agent.py
│   ├── intake_agent.py
│   ├── tochnit_agent.py
│   └── companion_agent.py
│
├── services/
│   ├── supabase_client.py
│   └── whatsapp_service.py
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── admin/
│   │   ├── dashboard.html
│   │   ├── lakoach_new.html
│   │   └── shibutz.html
│   ├── melave/
│   │   ├── dashboard.html
│   │   ├── intake.html
│   │   └── tochnit.html
│   ├── metapel/
│   │   ├── dashboard.html
│   │   ├── lakoach.html
│   │   └── sikum.html
│   └── lakoach/
│       ├── dashboard.html
│       └── companion.html
│
└── static/
    ├── style.css
    └── script.js
```

---

## Briah Design System (לכל Template)

### Page background — תמיד

```css
body {
  background: linear-gradient(90deg, #cbc6a9 0%, #fff0db 100%);
  background-attachment: fixed;
  color: #634734;
  font-family: "Assistant", "Heebo", sans-serif;
  direction: rtl;
}
```

### Google Fonts (ב-base.html)

```html
<link href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@300;400;500;700&family=Assistant:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

### צבעים

```
--briah-cream:       #fff0db   ← רקע
--briah-brown:       #634734   ← טקסט ראשי
--briah-olive:       #a3a877   ← כרטיסים, אלמנטים משניים
--briah-terracotta:  #a3502e   ← כפתורי CTA בלבד
--briah-sage:        #cbc6a9   ← גרדיאנט start
--briah-clay-100:    #e8c9b3   ← badges, tags
--briah-brown-100:   #b89a83   ← טקסט משני/מותש
```

### כפתורים

```css
.btn-primary {
  background: #a3502e; color: #fff0db;
  border-radius: 999px; padding: 14px 28px;
  font-family: "Assistant", sans-serif; font-size: 15px;
  font-weight: 500; border: none; cursor: pointer;
}
.btn-primary:hover { background: #823d22; }

.btn-secondary {
  background: transparent; color: #634734;
  border: 1px solid #8c6b54; border-radius: 999px; padding: 14px 28px;
}
```

### כרטיסים

```css
.card {
  background: #fffaf0;
  border: 1px solid rgba(99,71,52,0.14);
  border-radius: 28px; padding: 32px;
  box-shadow: 0 6px 18px -8px rgba(99,71,52,0.18);
}
```

### חוקים

- `dir="rtl" lang="he"` על כל דף
- אין pure white (`#fff`) — רק cream
- אין צבעים קרים/כחולים
- Terracotta רק לכפתורי action, אף פעם לרקע
- פינות: 28px לכרטיסים, 999px לכפתורים, 18px לשדות
- צללים תמיד warm: `rgba(99,71,52,...)`

---

## 11 פרומפטים — בצע בסדר הזה ב-Claude Code

### פרומפט 1 — Scaffold
```
Read CLAUDE.md fully.
Scaffold the complete folder structure for briah-os:
- Create all folders: routes/, agents/, services/, templates/admin/,
  templates/melave/, templates/metapel/, templates/lakoach/, static/
- Create empty Python files with just imports and a TODO comment:
  app.py, routes/auth.py, routes/admin.py, routes/melave.py,
  routes/metapel.py, routes/lakoach.py, services/supabase_client.py,
  services/whatsapp_service.py, agents/transcription_agent.py,
  agents/intake_agent.py, agents/tochnit_agent.py, agents/companion_agent.py
- Create requirements.txt with: flask, supabase, anthropic, twilio,
  python-dotenv, gunicorn, weasyprint
- Create Procfile: web: gunicorn app:app
- Create .env.example with all required keys
- Create database/schema.sql with all 8 CREATE TABLE statements from CLAUDE.md
Do NOT write any logic yet. Structure only.
```

### פרומפט 2 — Base Template + CSS
```
Read CLAUDE.md design system section.
Create static/style.css with the complete Briah design system:
- CSS variables for all colors
- Body: sage→cream gradient background, rtl, Assistant font
- Typography: Frank Ruhl Libre for h1-h3, Assistant for body/UI
- .card, .card-olive (on olive background), .card-brown (inverted)
- .btn-primary (terracotta pill), .btn-secondary, .btn-ghost
- .nav (top navbar), .sidebar, .main-content
- Form fields: input, textarea, select — radius 18px, warm borders
- .badge, .badge-risk-high (red), .badge-risk-med (amber), .badge-ok (olive)
- .avatar circle (initials)
- .status-dot (8px circle, colored)
- Responsive: mobile friendly

Create templates/base.html:
- <!DOCTYPE html><html dir="rtl" lang="he">
- Google Fonts: Frank Ruhl Libre + Assistant
- Link to style.css
- Top navbar with logo text "בריא.ה" and user name + logout
- Sidebar navigation (links change per role using Jinja2 if/elif)
- Main content block
- Flash messages block (success/error)
All text in Hebrew. Warm, soulful feel — not clinical or corporate.
```

### פרומפט 3 — Login
```
Build the Login page.

Create templates/login.html:
- Extends base.html but WITHOUT sidebar (full page layout)
- Centered card (max-width 420px)
- Logo: "בריא.ה" in Frank Ruhl Libre + tagline "מעטפת לחיים עצמם"
- Email field (label: "כתובת מייל")
- Password field (label: "סיסמה")
- Submit button (btn-primary): "כניסה"
- Flash error message area
- Sage→cream gradient background (same as body)

Create routes/auth.py:
- GET /login → render login.html
- POST /login → authenticate with Supabase Auth
  - On success: store user in session (id, role, full_name)
  - Redirect by role:
    admin → /admin
    melave → /melave
    metapel → /metapel
    lakoach → /lakoach
  - On failure: flash("שם משתמש או סיסמה שגויים", "error"), redirect /login
- GET /logout → clear session, redirect /login
- @login_required decorator for protecting routes

Register blueprint in app.py.
```

### פרומפט 4 — Admin Dashboard + הוספת לקוח
```
Build the Admin screens.

Create templates/admin/dashboard.html (extends base.html):
Stats row (4 metric cards):
- סה"כ לקוחות פעילים
- מלווים פעילים
- מטפלים פעילים
- לקוחות ממתינים לשיבוץ

Main table: כל הלקוחות
Columns: שם | מסלול | מלווה | מטפל 1:1 | שלב | תאריך התחלה | סטטוס | פעולות
- Status dots: ירוק=פעיל, כתום=ממתין לשיבוץ, אפור=הסתיים
- Action buttons: "צפה בפרופיל" + "ערוך שיבוץ"
- "+ לקוח חדש" button (btn-primary) top right

Create templates/admin/lakoach_new.html:
Form to add new participant:
- שם מלא, מייל, טלפון
- מסלול (עוגן/צמיחה/העמקה) — dropdown
- מלווה — dropdown (populated from users where role=melave)
- תאריך התחלה
- Submit: "צור לקוח ושלח הזמנה"

Create templates/admin/shibutz.html:
Participant assignment screen:
- Participant name + intake summary (read only)
- מטפל 1:1 — dropdown (populated from users where role=metapel)
- לוז שבועי: table showing available slots per therapist
- Submit: "אשר שיבוץ"

Create routes/admin.py:
- GET /admin → fetch all users/profiles from Supabase, render dashboard
- GET /admin/lakoach/new → render form
- POST /admin/lakoach → insert user + lakoach_profile in Supabase
- GET /admin/shibutz/<lakoach_id> → render shibutz screen
- POST /admin/shibutz/<lakoach_id> → update metapel_id in lakoach_profiles

All routes protected with @login_required + role check (admin only).
```

### פרומפט 5 — מלווה Dashboard + מסך אינטייק
```
Build the Melave (guide) screens. This is the core workflow screen.

Create templates/melave/dashboard.html (extends base.html):
Header: "שלום [שם מלווה], הלקוחות שלך"
Cards grid (one card per participant):
- שם לקוח + אווטר ראשיות
- מסלול (badge)
- שלב בתהליך: "אינטייק" / "תוכנית נשלחה" / "תהליך פעיל" / "שיחת עדכון נדרשת"
- תאריך התחלה
- כפתור: "פתח פרופיל"

Create templates/melave/intake.html (extends base.html):
This is the most important screen — where the human process becomes digital.
Layout: 2 columns

RIGHT column — "העלאת הקלטת השיחה":
  - Drag & drop upload area for audio file (MP3/M4A/WAV)
  - OR paste transcript text manually in textarea
  - Button: "עבד הקלטה עם AI" (btn-primary) → POST to /melave/intake/<id>/process
  - Status indicator: "ממתין" / "מעבד..." / "הושלם"

LEFT column — "תוצאות האינטייק" (appears after processing):
  - Section: "מה עלה בשיחה" — AI generated summary (editable textarea)
  - Section: "רצון עמוק שעלה" — AI extracted (editable)
  - Section: "נושאים מרכזיים" — AI extracted bullet list (editable)
  - Section: "הערות ודגשים של המלווה" — free text textarea
  - Section: "דגשים להעברה לצוות" — checkboxes:
    □ זקוקה לקרקוע    □ רגישות גבוהה למגע
    □ קושי במרחבים גדולים    □ יש לשים לב במצבים חברתיים
    + שדה פתוח לדגש נוסף
  - Button: "שמור אינטייק" (secondary)
  - Button: "המשך לבניית תוכנית אישית ←" (primary)

Create templates/melave/tochnit.html (extends base.html):
Personal plan builder — matching the PDF format from CLAUDE.md.

Section 1: "על מה נתמקד"
  - 3 dropdown fields: בחר ציר (חיבור לגוף / ויסות רגשי / מערכות יחסים / ביטחון עצמי / תנועה ויציאה מתקיעות)
  - For each selected axis: textarea for short explanation

Section 2: "איך זה נראה בפועל"
  - Dynamic list: add activities
    Each row: שם הפעילות | סוג (סדנה קבוצתית / טיפול 1:1 / מדיטציה) | תדירות | "איך זה תומך בתהליך"
  - "+ הוסף פעילות" button

Section 3: "לוז החודש"
  - Weekly calendar grid (ראשון–שישי)
  - Each cell: time + activity name + facilitator

Section 4: "מכתב אישי ללקוח"
  - Pre-filled template from CLAUDE.md (editable):
    "[שם] יקרה,
    תודה על הפתיחות והלב שהבאת לשיחת האינטייק.
    מהשיחה עלה ש___
    ובמקביל יש בך רצון עמוק ל___
    מתוך זה, בנינו עבורך את התוכנית האישית שלך בבריאה 🤍"
  - Editable textarea

Bottom actions:
  - "שמור טיוטה" (secondary)
  - "שלח ללקוח + לבריאה" (primary) → generates PDF + sends

Create routes/melave.py:
- GET /melave → fetch this melave's lakochim, render dashboard
- GET /melave/intake/<lakoach_id> → render intake screen (empty)
- POST /melave/intake/<lakoach_id>/save → save intake data to Supabase intakes table
- POST /melave/intake/<lakoach_id>/process → placeholder (returns mock data for now, AI added later)
- GET /melave/tochnit/<lakoach_id> → render tochnit builder, pre-fill from intake if exists
- POST /melave/tochnit/<lakoach_id>/save → save to tochniyot_ishiyot table
- POST /melave/tochnit/<lakoach_id>/send → mark as sent, update sent_at

All routes: @login_required + melave role check.
```

### פרומפט 6 — מטפל 1:1 Dashboard
```
Build the Metapel (therapist) screens.

Create templates/metapel/dashboard.html (extends base.html):
Left panel: "הלקוחות שלי"
  - List of assigned participants
  - Each: avatar + name + next session date + last summary date
  - Status: "דורש סיכום" (amber badge) if last session > 2 sessions ago without summary
  - Click → opens lakoach profile

Right panel: "לוז השבוע"
  - Week grid showing scheduled sessions
  - Each session: time + client name + session number
  - Status: upcoming / completed / needs summary

Create templates/metapel/lakoach.html (extends base.html):
Full participant profile for therapist:

TOP SECTION — "דגשים חשובים" (highlighted card in cream-50):
  - Extracted from intake by melave: listed prominently
  - E.g. "זקוקה לקרקוע", "רגישות גבוהה למגע"
  - Alert if any risk flags

MIDDLE SECTION — "תוכנית אישית":
  - The 3 axes + explanations (read only from tochniyot_ishiyot)
  - Current activity plan

BOTTOM SECTION — "היסטוריית טיפולים":
  - Table: תאריך | פגישה מספר | סיכום קצר | דגשים
  - "העלה סיכום" button for latest session

Create templates/metapel/sikum.html (extends base.html):
Session summary upload form:
  - Date (auto-filled to today)
  - Session number (auto-calculated)
  - "סיכום קצר" — textarea (NOT for deep personal content)
  - "דגשים לצוות" — what should be shared:
    Examples shown: "זקוקה לקרקוע", "רגישות גבוהה למגע"
    Checkbox list + free text
  - Submit: "שמור סיכום"

Create routes/metapel.py:
- GET /metapel → fetch this metapel's lakochim + upcoming sessions
- GET /metapel/lakoach/<lakoach_id> → full profile with intake + summaries
- GET /metapel/sikum/<lakoach_id> → summary form
- POST /metapel/sikum/<lakoach_id> → save to sessions table

All: @login_required + metapel role.
```

### פרומפט 7 — לקוח Dashboard
```
Build the Lakoach (participant) screens.

Create templates/lakoach/dashboard.html (extends base.html):
HERO SECTION (full width warm card):
  - "שלום [שם], ברוכה הבאה למסע שלך בבריאה 🌿"
  - Resilience Score circle (visual, placeholder number for now)
  - 3 core axes from tochnit (displayed as pills)

SECTION: "התוכנית האישית שלך"
  - Warm card per axis: icon area + title + short description
  - Progress indicator: שלב X מתוך Y

SECTION: "החודש שלך בבריאה"
  - Weekly calendar grid (like the PDF luz example)
  - ראשון עד שישי columns
  - Each cell: time + activity name + facilitator name
  - Color coding: קרקוע=sage, פריקה=terracotta, קהילה=olive, אינטגרציה=clay, משמעות=brown

SECTION: "הצוות שלך"
  - Avatar card: מלווה (name + "לשאלות על התהליך")
  - Avatar card: מטפל/ת 1:1 (name + next session date)
  - Contact info for Briah logistics

BOTTOM: "AI Companion — כאן בשבילך"
  - Card with short intro text
  - Button: "פתחי שיחה" → /lakoach/companion

Create templates/lakoach/companion.html (extends base.html):
AI Companion chat interface:
  - Header: "AI Companion בריאה" + subtitle "כאן לתמוך, להקשיב ולהחזיק אותך בין המפגשים"
  - Chat messages area (scrollable):
    - Bubble right: user messages (cream bg)
    - Bubble left: AI messages (olive/sage bg)
    - Timestamp on each
  - Opening message from AI (hardcoded for now):
    "שלום [שם] 🤍 איך את מרגישה היום?"
  - Input area: textarea + "שלח" button
  - Small disclaimer: "זהו כלי תמיכה, לא תחליף לטיפול אנושי"

Create routes/lakoach.py:
- GET /lakoach → fetch tochnit + luz + team info, render dashboard
- GET /lakoach/companion → render chat with history from companion_logs
- POST /lakoach/companion → save message to DB, return placeholder response (AI connected later)

All: @login_required + lakoach role.
```

### פרומפט 8 — app.py + Supabase Client
```
Build the Flask application core.

Create services/supabase_client.py:
  - Import supabase, os, dotenv
  - Load .env
  - Create supabase client singleton: url + key from env
  - Export: supabase (client instance)

Create app.py:
  - Flask app init
  - Load .env
  - Secret key from env
  - Register all blueprints:
    from routes.auth import auth_bp → app.register_blueprint(auth_bp)
    from routes.admin import admin_bp → app.register_blueprint(admin_bp)
    from routes.melave import melave_bp → app.register_blueprint(melave_bp)
    from routes.metapel import metapel_bp → app.register_blueprint(metapel_bp)
    from routes.lakoach import lakoach_bp → app.register_blueprint(lakoach_bp)
  - Root route: redirect to /login if not logged in, else to role dashboard
  - if __name__ == '__main__': app.run(debug=True)

Add @login_required decorator in routes/auth.py:
  - Check session['user_id'] exists
  - If not: redirect to /login with flash message
  - Helper: get_current_user() → returns session dict

Create .env.example:
  SUPABASE_URL=
  SUPABASE_KEY=
  ANTHROPIC_API_KEY=
  TWILIO_ACCOUNT_SID=
  TWILIO_AUTH_TOKEN=
  TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
  FLASK_SECRET_KEY=
  PORT=5000
```

### פרומפט 9 — Database Schema + Supabase Setup
```
Create database/schema.sql with all 8 CREATE TABLE statements from CLAUDE.md.

Also create database/seed.sql with test data:
  - 1 organization: "בריאה תל אביב"
  - 1 admin user: admin@briah.co
  - 2 melave users: melave1@briah.co, melave2@briah.co
  - 2 metapel users: metapel1@briah.co, metapel2@briah.co
  - 3 lakoach users with profiles:
    - lakoach1: assigned to melave1, metapel1, mashlul=tzmiha
    - lakoach2: assigned to melave1, metapel2, mashlul=hamakata
    - lakoach3: assigned to melave2, metapel1, mashlul=ikur (waiting for metapel)
  - 1 completed intake for lakoach1
  - 1 tochnit for lakoach1
  - 2 sessions for lakoach1

Create database/README.md explaining:
  - How to run schema.sql in Supabase SQL editor
  - How to enable Row Level Security
  - Which tables need RLS policies and what they should be
```

### פרומפט 10 — Testing + Polish
```
Review all templates and routes for consistency.

1. Make sure every template that extends base.html renders correctly:
   - base.html nav shows correct links per role
   - Flash messages display with correct styling (success=olive, error=terracotta)
2. Add basic form validation to all POST routes:
   - Required field checks
   - Flash error messages in Hebrew
3. Make the dashboard pages show real data from Supabase (not hardcoded):
   - /admin → real counts from DB
   - /melave → real lakoach list for this melave
   - /metapel → real sessions and clients
   - /lakoach → real tochnit and luz if exists, else onboarding message
4. Add 404 and 500 error pages in templates/errors/:
   - Hebrew, branded with Briah design
   - Link back to dashboard
5. Test the full user journey manually:
   admin creates lakoach → lakoach logs in → sees dashboard
   melave logs in → sees their clients → opens intake screen
   metapel logs in → sees clients → opens profile → uploads summary
```

### פרומפט 11 — Deploy to Railway
```
Prepare for Railway deployment.

1. Verify Procfile: web: gunicorn app:app
2. Create railway.json:
{
  "build": {"builder": "NIXPACKS"},
  "deploy": {"startCommand": "gunicorn app:app", "healthcheckPath": "/login"}
}
3. Make sure all env variables are read from os.environ (not hardcoded).
4. Test locally:
   pip install -r requirements.txt
   python app.py
   Open http://localhost:5000 → should redirect to /login
5. Push to GitHub. Connect Railway to the repo.
   Add all variables from .env.example to Railway → Variables.
6. After deploy: test login with each role.
   Share the Railway URL.
```

---

## ה-AI מתחבר בשלב הבא (לא עכשיו)

אחרי שכל הפרונטנד והשלד רצים — מחברים את ה-AI:

- `agents/transcription_agent.py` — מקבל audio file URL, קורא ל-Claude API
  עם הקלטה, מחזיר transcript + structured intake JSON
- `agents/intake_agent.py` — מקבל transcript + melave notes,
  מחזיר: מה עלה בשיחה, רצון עמוק, נושאים מרכזיים, דגשים לצוות
- `agents/tochnit_agent.py` — מקבל intake JSON + lakoach profile,
  מחזיר תוכנית אישית מלאה בפורמט בריאה (3 צירים + פעילויות + מכתב אישי)
- `agents/companion_agent.py` — מקבל conversation history + tochnit context,
  מחזיר תגובה חמה בעברית בטון בריאה

---

## NEVER

- אל תשים API keys בקוד
- אל תשכח `dir="rtl" lang="he"` על כל HTML
- אל תשתמש ב-pure white (`#fff`) — תמיד cream
- אל תשתמש בצבעים כחולים/קרים
- אל תשים לוגיקת AI בשלב הזה — רק placeholder routes
