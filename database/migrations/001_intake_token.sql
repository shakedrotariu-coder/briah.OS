ALTER TABLE lakoach_profiles
ADD COLUMN IF NOT EXISTS intake_token text UNIQUE,
ADD COLUMN IF NOT EXISTS intake_token_expires timestamptz,
ADD COLUMN IF NOT EXISTS intake_submitted_at timestamptz;

ALTER TABLE intakes
ADD COLUMN IF NOT EXISTS ai_assessment jsonb,
ADD COLUMN IF NOT EXISTS resilience_score integer,
ADD COLUMN IF NOT EXISTS score_breakdown jsonb;
