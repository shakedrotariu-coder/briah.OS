# Briah.OS — בריאה · מעטפת לחיים עצמם
## AI Operating System for Mental Health & Resilience
### Course 55308 | Claude Code Build Guide

---

## What is Briah.OS?

Briah.OS is an AI platform that helps organizations deliver continuous, personalized mental-health care.
The core promise: **one assessment → a living care journey.**

Instead of episodic therapy, Briah creates a continuous loop:
a participant fills a single assessment → the AI generates a personalized Resilience Score →
the AI builds an 8-step care journey → a Care Manager oversees progress →
a WhatsApp bot checks in daily → the AI Companion is available 24/7.

The platform serves three user types:
- **Participant** — fills the assessment, follows their journey, chats with the AI Companion via web or WhatsApp
- **Care Manager** — sees all participants in a CRM, gets risk alerts, reviews AI-generated session summaries
- **Org Admin** — sees organization-wide Resilience Index, engagement stats, aggregate insights

---

## The Five Layers of Briah (brand context — use in AI prompts and UI copy)

Briah's model is built on five sequential planes (חמשת המישורים), from Dr. Bessel van der Kolk's research:

1. **קרקוע · Grounding** — physiological safety. Somatic yoga, shiatsu, sound healing.
2. **פריקה · Release** — letting stored tension out. Ecstatic dance, voice expression, rebirthing.
3. **אינטגרציה · Integration** — bridging body and mind. Integrative writing, therapy, processing circles.
4. **קהילה · Community** — from individual to belonging. Lectures, dialog circles, gatherings.
5. **משמעות · Meaning** — returning to action from inner clarity. Meditation, ceremonies, guided imagery.

The AI agents must reference these layers when generating journeys and companion responses.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 + Flask |
| Database & Auth | Supabase (PostgreSQL + Row Level Security) |
| AI Agent | Claude API — model: `claude-sonnet-4-6` |
| Python AI SDK | `anthropic` pip package |
| WhatsApp | Twilio WhatsApp API — `twilio` pip package |
| Frontend | HTML + CSS + Jinja2 templates (no JS framework) |
| Deployment | Railway — git push → auto-deploy |
| Version Control | Git + GitHub |

---

## The Core Flow (MVP)

```
Login → Assessment (10 questions) → AI Resilience Score → AI Journey (8 steps)
     → Care Manager Dashboard → Participant Dashboard → WhatsApp daily check-in
```

---

## Full Architecture

```
┌─────────────────────────────────────────────────────────┐
│  USERS                                                  │
│  Participant · Care Manager · Org Admin                 │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS
┌────────────────────▼────────────────────────────────────┐
│  SUPABASE AUTH — JWT + Row Level Security               │
│  role: participant | care_manager | org_admin           │
└────────────────────┬────────────────────────────────────┘
                     │ authenticated request
┌────────────────────▼────────────────────────────────────┐
│  FLASK BACKEND (Python · Railway)                       │
│                                                         │
│  POST /assessment      → receives questionnaire         │
│  GET  /score/<id>      → returns Resilience Score       │
│  GET  /journey/<id>    → returns/updates AI journey     │
│  POST /companion       → AI Companion chat              │
│  GET  /dashboard       → participant view               │
│  GET  /care-manager    → CRM all participants           │
│  GET  /care-manager/<id> → single participant profile   │
│  GET  /org             → org-wide intelligence          │
│  POST /whatsapp        → Twilio webhook                 │
└──────┬───────────────────────────────┬──────────────────┘
       │ calls AI agents               │ read/write
┌──────▼────────────────┐   ┌──────────▼──────────────────┐
│  AI AGENTS            │   │  SUPABASE DATABASE          │
│  (Claude API)         │   │                             │
│                       │   │  users                      │
│  assessment_agent.py  │   │  assessments                │
│  → analyzes answers   │   │  journeys                   │
│  → computes score     │   │  companion_logs             │
│  → returns JSON       │   │  sessions                   │
│                       │   │  organizations              │
│  journey_agent.py     │   │  wa_messages                │
│  → builds 8-step plan │   │                             │
│  → adapts to profile  │   └─────────────────────────────┘
│                       │
│  companion_agent.py   │
│  → 24/7 support chat  │
│  → uses journey ctx   │
│  → logs every msg     │
└──────────────────┬────┘
                   │
┌──────────────────▼────────────────────────────────────┐
│  WHATSAPP (Twilio) — required external integration    │
│                                                       │
│  OUTBOUND (Flask → Twilio → User):                    │
│  · Daily check-in 9:00 AM: "איך את מרגישה היום? 1-5"  │
│  · Journey reminders: "היום: תרגיל נשימה 5 דקות"      │
│  · Milestone: "סיימת שלב 3! הצלחה גדולה"              │
│                                                       │
│  INBOUND (User → Twilio → POST /whatsapp):            │
│  1. Twilio sends POST to /whatsapp                    │
│  2. Flask looks up phone_number → user_id             │
│  3. companion_agent responds, saves to companion_logs │
│  4. Flask returns TwiML response                      │
│                                                       │
│  Setup: Twilio sandbox (free for development)         │
│  User sends "join [code]" once to activate            │
└───────────────────────────────────────────────────────┘
```

---

## Project Folder Structure

```
briah-os/
├── app.py                         # Flask entry point
├── requirements.txt
├── Procfile                       # Railway: web: gunicorn app:app
├── .env                           # NEVER commit
├── CLAUDE.md                      # this file
│
├── routes/
│   ├── auth.py                    # login, logout, register
│   ├── assessment.py              # POST /assessment, GET /score
│   ├── journey.py                 # GET /journey, PUT /journey/step
│   ├── companion.py               # POST /companion
│   ├── dashboard.py               # GET /dashboard (participant)
│   ├── care_manager.py            # GET /care-manager
│   ├── org.py                     # GET /org
│   └── whatsapp.py                # POST /whatsapp (Twilio webhook)
│
├── agents/
│   ├── assessment_agent.py        # answers → Resilience Score (JSON)
│   ├── journey_agent.py           # score + profile → 8-step journey
│   └── companion_agent.py        # conversation → empathetic response
│
├── services/
│   ├── supabase_client.py         # Supabase connection singleton
│   └── whatsapp_service.py        # Twilio send/receive helpers
│
├── templates/
│   ├── base.html                  # shared layout + nav
│   ├── login.html
│   ├── assessment.html            # multi-step questionnaire
│   ├── participant_dashboard.html # score + journey + companion
│   ├── care_manager.html          # CRM + risk alerts
│   ├── companion.html             # AI chat interface
│   └── org_dashboard.html
│
└── static/
    ├── style.css                  # import Briah design tokens
    └── script.js                  # minimal JS only
```

---

## Database Schema (Supabase — PostgreSQL)

### users
```sql
CREATE TABLE users (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email           text UNIQUE NOT NULL,
  role            text NOT NULL CHECK (role IN ('participant','care_manager','org_admin')),
  org_id          uuid REFERENCES organizations(id),
  phone           text,
  wa_opted_in     boolean DEFAULT false,
  wa_chat_id      text,
  created_at      timestamptz DEFAULT now()
);
```

### assessments
```sql
CREATE TABLE assessments (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid REFERENCES users(id) NOT NULL,
  answers         jsonb NOT NULL,
  resilience_score integer CHECK (resilience_score BETWEEN 0 AND 100),
  score_breakdown jsonb,
  created_at      timestamptz DEFAULT now()
);
```

### journeys
```sql
CREATE TABLE journeys (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid REFERENCES users(id) NOT NULL,
  assessment_id   uuid REFERENCES assessments(id),
  steps           jsonb NOT NULL,
  current_step    integer DEFAULT 0,
  status          text DEFAULT 'active' CHECK (status IN ('active','paused','completed')),
  updated_at      timestamptz DEFAULT now()
);
```

### companion_logs
```sql
CREATE TABLE companion_logs (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid REFERENCES users(id) NOT NULL,
  role            text NOT NULL CHECK (role IN ('user','assistant')),
  content         text NOT NULL,
  channel         text DEFAULT 'web' CHECK (channel IN ('web','whatsapp')),
  created_at      timestamptz DEFAULT now()
);
```

### sessions
```sql
CREATE TABLE sessions (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  participant_id    uuid REFERENCES users(id) NOT NULL,
  care_manager_id   uuid REFERENCES users(id) NOT NULL,
  scheduled_at      timestamptz NOT NULL,
  notes             text,
  ai_summary        text,
  status            text DEFAULT 'scheduled'
);
```

### organizations
```sql
CREATE TABLE organizations (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name              text NOT NULL,
  resilience_index  float,
  created_at        timestamptz DEFAULT now()
);
```

### wa_messages
```sql
CREATE TABLE wa_messages (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid REFERENCES users(id),
  direction       text CHECK (direction IN ('inbound','outbound')),
  body            text NOT NULL,
  message_type    text DEFAULT 'text',
  sent_at         timestamptz DEFAULT now()
);
```

---

## AI Agents — Implementation Guide

### assessment_agent.py

```python
import anthropic, json

def analyze_assessment(answers: dict) -> dict:
    """
    Input:  answers dict — {q1: "...", q2: "...", ...}
    Output: {resilience_score: 72, breakdown: {...}, journey_type: "moderate"}
    """
    client = anthropic.Anthropic()

    prompt = f"""
You are a compassionate mental health assessment AI for Briah.OS, a wellness platform
based on the five layers of healing: קרקוע (grounding), פריקה (release),
אינטגרציה (integration), קהילה (community), משמעות (meaning).

Analyze these questionnaire answers and return ONLY valid JSON (no markdown):
{{
  "resilience_score": <integer 0-100>,
  "breakdown": {{
    "grounding": <0-100>,
    "release": <0-100>,
    "integration": <0-100>,
    "community": <0-100>,
    "meaning": <0-100>
  }},
  "primary_focus": "<which of the 5 layers needs most attention>",
  "journey_type": "<gentle|moderate|intensive>",
  "summary_he": "<2-3 sentences in warm Hebrew about what you see>"
}}

Answers: {json.dumps(answers, ensure_ascii=False)}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return json.loads(response.content[0].text)
```

### journey_agent.py

```python
def build_journey(score: int, breakdown: dict, user_profile: dict) -> list:
    """
    Input:  Resilience Score + breakdown + user profile
    Output: list of 8 journey steps
    """
    prompt = f"""
You are a care journey architect for Briah.OS.
Build a personalized 8-step healing journey based on:

Resilience Score: {score}/100
Layer breakdown: {json.dumps(breakdown, ensure_ascii=False)}
User profile: {json.dumps(user_profile, ensure_ascii=False)}

Return ONLY valid JSON (no markdown):
{{
  "steps": [
    {{
      "step": 1,
      "layer": "<one of the 5 layers>",
      "title_he": "<step title in Hebrew>",
      "description_he": "<what to do, warm and specific>",
      "duration_days": <3-7>,
      "practice_type": "<breathwork|writing|movement|community|meditation>"
    }}
  ]
}}

Prioritize the layers with lowest scores. Steps should progress from
grounding → release → integration → community → meaning.
Use the warm, soulful voice of the Briah brand.
"""
    # ... call Claude API, parse JSON, return steps
```

### companion_agent.py

```python
def get_companion_response(user_id: str, user_message: str,
                           history: list, journey_context: dict) -> str:
    """
    Input:  user message + last 10 messages + journey context
    Output: warm, empathetic response string
    """
    system_prompt = f"""
You are the Briah AI Companion — a warm, soulful, grounded presence
supporting {journey_context.get('name', 'the participant')} on their healing journey.

Their current journey step: {journey_context.get('current_step_title', 'beginning')}
Their Resilience Score: {journey_context.get('score', 'not yet assessed')}
Primary focus area: {journey_context.get('primary_focus', 'general wellbeing')}

Guidelines:
- Respond in the same language the user writes in (Hebrew or English)
- Warm, direct, second person (את / אתה)
- Never diagnose. Never prescribe medication. Never replace a therapist.
- Ground every response in one of the 5 Briah layers
- Keep responses concise (2-4 sentences) unless more detail is clearly needed
- If distress signals detected, gently suggest speaking with their Care Manager
"""
    # Build messages array with history + new message
    # Call Claude API with system prompt
    # Save response to companion_logs
    # Return response text
```

---

## WhatsApp Service — whatsapp_service.py

```python
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import os

TWILIO_SID   = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM  = os.getenv("TWILIO_WHATSAPP_FROM")  # "whatsapp:+14155238886"

def send_whatsapp(to_phone: str, message: str):
    """Send outbound WhatsApp message via Twilio"""
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    client.messages.create(
        from_=TWILIO_FROM,
        to=f"whatsapp:{to_phone}",
        body=message
    )

def send_daily_checkin(to_phone: str, name: str):
    send_whatsapp(to_phone,
        f"בוקר טוב {name} 🌿\nאיך את/ה מרגיש/ה היום? ענה/י במספר בין 1 ל-5\n(1 = קשה, 5 = מצוין)")

def make_twiml_response(reply_text: str) -> str:
    """Build TwiML response for Twilio webhook"""
    resp = MessagingResponse()
    resp.message(reply_text)
    return str(resp)
```

### Twilio Sandbox Setup (development)
1. Go to twilio.com/console → Messaging → Try it out → Send a WhatsApp message
2. Get sandbox number + join code
3. Set webhook URL in Twilio console: `https://[your-railway-url].up.railway.app/whatsapp`
4. User sends: "join [sandbox-code]" to the Twilio WhatsApp number once
5. All messages now flow through your Flask webhook

---

## Environment Variables (.env — NEVER commit)

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...
ANTHROPIC_API_KEY=sk-ant-...
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=xxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
FLASK_SECRET_KEY=some-random-secret
PORT=5000
```

On Railway: add all of these under project → Variables.

---

## API Routes Reference

| Method | Route | Role | What it does |
|--------|-------|------|-------------|
| POST | /auth/login | all | Supabase auth login |
| POST | /auth/logout | all | Logout |
| POST | /assessment | participant | Submit 10-question form |
| GET | /score/`<user_id>` | participant | Get Resilience Score + breakdown |
| GET | /journey/`<user_id>` | participant | Get full journey |
| PUT | /journey/`<user_id>`/step | participant | Advance to next step |
| POST | /companion | participant | AI Companion message |
| GET | /dashboard | participant | Personal dashboard view |
| GET | /care-manager | care_manager | CRM — all participants |
| GET | /care-manager/`<user_id>` | care_manager | Single participant profile |
| POST | /care-manager/`<user_id>`/note | care_manager | Add session note |
| GET | /org | org_admin | Org Intelligence view |
| POST | /whatsapp | system | Twilio webhook |

---

## MVP — What Must Be Built (course deadline)

### Must Have (ship-blocking)
- [ ] Supabase Auth + role-based access (RLS on all tables)
- [ ] Assessment questionnaire — 10 questions, 5 dimensions
- [ ] assessment_agent.py → Resilience Score
- [ ] journey_agent.py → 8-step personalized journey
- [ ] companion_agent.py → AI Companion chat
- [ ] Participant Dashboard (score + journey + companion)
- [ ] Care Manager CRM (client list + risk flags)
- [ ] WhatsApp daily check-in via Twilio
- [ ] Deployed on Railway

### Nice to Have
- Basic Wellness Library (static content)
- Session booking
- Email notifications
- Progress charts

### Out of Scope (not in MVP)
- Mobile app
- Payments
- Wearables
- Multi-language
- Advanced analytics

---

## Git Strategy — Team Commits

Each member must show commits on GitHub (Yonatan checks git log).

| Member | Owns |
|--------|------|
| 1 | `agents/assessment_agent.py` + `routes/assessment.py` + assessment template |
| 2 | `agents/journey_agent.py` + `routes/journey.py` + participant dashboard |
| 3 | `agents/companion_agent.py` + `services/whatsapp_service.py` + `routes/whatsapp.py` |
| 4 | `routes/care_manager.py` + `routes/org.py` + CRM template + org dashboard |

Branch strategy:
- `main` → Railway auto-deploys
- `dev` → all PRs merge here first
- `feature/[name]` → individual work

---

## NEVER Do

- NEVER commit `.env` or any API keys to GitHub
- NEVER put `ANTHROPIC_API_KEY` in frontend HTML or JS
- NEVER modify Supabase migrations without team approval
- NEVER use `print()` for debugging in production — use `import logging`
- NEVER skip `try/except` on Claude API calls (the API can fail)
- NEVER skip RLS — every table must have Row Level Security enabled

## ALWAYS Do

- ALWAYS validate user role in Flask before returning data
- ALWAYS save AI agent responses to Supabase before returning to user
- ALWAYS handle `/whatsapp` webhook with `try/except`
- ALWAYS commit after every working feature with a clear message
- ALWAYS test with a real dummy user before pushing to Railway

---

## Briah Brand — Design Guidelines for UI

### Core Philosophy
Briah is a conscious-living wellness platform. The UI must feel:
**soulful, editorial, warm, grounded** — never clinical, cold, or corporate.

### Colors (use these exact values)
```css
--briah-cream:       #fff0db;   /* page background — warm, soft */
--briah-brown:       #634734;   /* text, headings, navbar */
--briah-olive:       #a3a877;   /* cards, sections, soft elements */
--briah-terracotta:  #a3502e;   /* CTA only — buttons, links, actions */
--briah-sage:        #cbc6a9;   /* gradient start */

/* The brand gradient — use on every page background */
--bg-gradient: linear-gradient(90deg, #cbc6a9 0%, #fff0db 100%);

/* Extended palette */
--briah-clay-100:    #e8c9b3;   /* badges, soft tags */
--briah-clay-300:    #a3502e;   /* = terracotta, CTA */
--briah-clay-400:    #823d22;   /* hover state */
--briah-brown-100:   #b89a83;   /* muted text */
--briah-brown-200:   #8c6b54;   /* secondary text */
--briah-cream-200:   #f7e6cf;   /* card hover bg */
```

### Fonts
```css
/* Display / Headlines */
font-family: "Shlomo", "Frank Ruhl Libre", Georgia, serif;

/* Body / UI / Labels */
font-family: "Hadkeren", "Assistant", "Heebo", sans-serif;

/* Load from Google Fonts (until licensed files arrive): */
/* @import url("https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@300;400;500;700&family=Assistant:wght@300;400;500;600;700&display=swap"); */
```

### Page Background
```css
/* Every page: sage → cream gradient */
body {
  background: linear-gradient(90deg, #cbc6a9 0%, #fff0db 100%);
  background-attachment: fixed;
  color: #634734;
}
```

### Buttons
```css
/* Primary CTA */
.btn-primary {
  background: #a3502e;       /* terracotta */
  color: #fff0db;            /* cream text */
  border-radius: 999px;      /* always pill shape */
  padding: 14px 28px;
  font-family: "Hadkeren", "Assistant", sans-serif;
  font-size: 15px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: background 280ms cubic-bezier(0.45,0,0.55,1);
}
.btn-primary:hover { background: #823d22; }

/* Secondary */
.btn-secondary {
  background: transparent;
  color: #634734;
  border: 1px solid #8c6b54;
  border-radius: 999px;
  padding: 14px 28px;
}
.btn-secondary:hover { background: #634734; color: #fff0db; }
```

### Cards
```css
.card {
  background: #fffaf0;         /* cream-50, slightly elevated */
  border: 1px solid rgba(99,71,52,0.14);
  border-radius: 28px;         /* --radius-lg */
  padding: 32px;
  box-shadow: 0 6px 18px -8px rgba(99,71,52,0.18),
              0 2px 4px rgba(99,71,52,0.05);
}
```

### Corner Radii
```
Cards: 28px
Buttons / chips / badges: 999px (pill)
Form fields: 18px
Large hero panels: 44px
Organic accent shapes: 62% 38% 70% 30% / 40% 64% 36% 60% (blob)
```

### Shadows (always warm-toned — never gray)
```css
--shadow-sm: 0 1px 2px rgba(99,71,52,0.06);
--shadow-md: 0 6px 18px -8px rgba(99,71,52,0.18), 0 2px 4px rgba(99,71,52,0.05);
--shadow-lg: 0 20px 50px -20px rgba(99,71,52,0.28);
```

### RTL — Hebrew First
```html
<html dir="rtl" lang="he">
```
All templates use RTL. Text aligns right. Arrows point left (←) not right.

### Voice & Copy Tone
- Warm, direct, second-person plural: **אתם / אתן / לכם**
- Never clinical. Never salesy. Speak alongside the user, not at them.
- Hebrew first. English only for technical terms or accents.
- No emoji in UI. Symbol accents only: `＋` `·` `—`
- Stats are sparse and serious. No decorative numbers.

### What to Avoid
- No pure white (`#ffffff`) or pure black (`#000000`)
- No cool / blue tones anywhere in the palette
- No harsh shadows (always warm `rgba(99,71,52,...)`)
- No corporate stock photography
- No gradients beyond the brand sage→cream gradient
- No rounded corners below 6px
- Terracotta (`#a3502e`) is **accent only** — never a background

---

## How to Start Building with Claude Code

Open Claude Code in the project folder and run these prompts in order:

### Step 1 — Scaffold
```
Read CLAUDE.md fully. Then scaffold the complete folder structure:
all folders, empty Python files, requirements.txt, Procfile, .env.example.
Do not write any logic yet — just the structure.
```

### Step 2 — Database
```
Create services/supabase_client.py with the Supabase connection.
Then write all 7 SQL CREATE TABLE statements from CLAUDE.md
as a single file: database/schema.sql
```

### Step 3 — Auth
```
Build routes/auth.py with login, logout, register using Supabase Auth.
Build templates/login.html using the Briah design system:
sage-to-cream gradient background, Frank Ruhl Libre serif headings,
terracotta CTA button, RTL Hebrew layout.
```

### Step 4 — Core AI Agent (most important)
```
Build agents/assessment_agent.py using the Claude API.
It must take a dict of answers, call claude-sonnet-4-6,
and return a JSON with resilience_score, breakdown (5 dimensions),
primary_focus, journey_type, and summary_he.
Include proper error handling.
```

### Step 5 — Assessment Flow
```
Build routes/assessment.py and templates/assessment.html.
The form has 10 questions across 5 dimensions (2 questions each):
קרקוע, פריקה, אינטגרציה, קהילה, משמעות.
On submit, call assessment_agent, save to Supabase, redirect to dashboard.
Use Briah design: warm cards, olive accents, pill buttons.
```

### Step 6 — Journey Agent
```
Build agents/journey_agent.py.
It takes the score + breakdown + user profile, calls Claude API,
and returns 8 journey steps as JSON, each with layer, title_he,
description_he, duration_days, practice_type.
```

### Step 7 — Participant Dashboard
```
Build routes/dashboard.py and templates/participant_dashboard.html.
Show: Resilience Score (visual circle), current journey step,
next 3 steps preview, AI Companion chat widget.
Full Briah branding: cream background, brown text, olive cards.
```

### Step 8 — AI Companion
```
Build agents/companion_agent.py and routes/companion.py.
The companion gets the last 10 messages from companion_logs,
the user's journey context, and calls Claude with a warm system prompt
rooted in the 5 Briah layers.
Save every message (both directions) to companion_logs.
```

### Step 9 — WhatsApp
```
Build services/whatsapp_service.py and routes/whatsapp.py.
Outbound: send_daily_checkin() sends "איך את מרגישה היום? 1-5" at 9 AM.
Inbound: POST /whatsapp webhook receives Twilio message,
looks up user by phone, calls companion_agent, returns TwiML.
Save all messages to wa_messages table.
```

### Step 10 — Care Manager CRM
```
Build routes/care_manager.py and templates/care_manager.html.
Show: stats row (avg score, open risks, WhatsApp engagement, sessions),
participant table with risk dots, score bars, last contact,
risk alerts panel, upcoming sessions, WhatsApp check-in feed.
Role-protected: only care_manager role can access.
```

### Step 11 — Deploy
```
Create Procfile: web: gunicorn app:app
Push to GitHub. Connect Railway to the repo.
Add all environment variables from .env to Railway.
Set Twilio webhook URL to the Railway deployment URL.
```

---

*Briah.OS · Course 55308 · AI Developer Program · יונתן זועארי*
*מעטפת לחיים עצמם · An envelope for life itself*
