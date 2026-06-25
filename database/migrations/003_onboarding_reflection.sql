-- Onboarding steps (שמירת התקדמות בתהליך הקליטה החדש)
CREATE TABLE IF NOT EXISTS onboarding_steps (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lakoach_id uuid REFERENCES users(id),
  token text,
  step_completed int DEFAULT 0,
  step1_data jsonb,
  step2_data jsonb,
  step3_data jsonb,
  step4_data jsonb,
  step5_data jsonb,
  completed_at timestamptz,
  created_at timestamptz DEFAULT now()
);

-- Monthly reflections (רפלקציה חודשית)
CREATE TABLE IF NOT EXISTS monthly_reflections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lakoach_id uuid REFERENCES users(id),
  month_num int NOT NULL,
  month_year text NOT NULL,
  reflection_data jsonb NOT NULL,
  ai_analysis jsonb,
  overall_status text,
  avg_belonging float,
  avg_wellbeing float,
  submitted_at timestamptz DEFAULT now()
);
