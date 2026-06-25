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
  status          text DEFAULT 'active',
  intake_token            text UNIQUE,         -- טוקן ייחודי לקישור האינטייק
  intake_token_expires    timestamptz,
  intake_submitted_at     timestamptz
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
  ai_assessment      jsonb,    -- תוצאת ה-AI המלאה על שאלון האינטייק
  resilience_score   integer CHECK (resilience_score BETWEEN 0 AND 100),
  score_breakdown    jsonb,    -- פירוט לפי 5 המישורים
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
