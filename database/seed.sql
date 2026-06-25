-- Briah.OS Test Data
-- Run AFTER schema.sql (and after rls_policies.sql / migrations if applicable)

-- Organization
INSERT INTO organizations (id, name) VALUES
  ('00000000-0000-0000-0000-000000000001', 'בריאה תל אביב');

-- Admin
INSERT INTO users (id, email, full_name, role, org_id) VALUES
  ('00000000-0000-0000-0000-000000000010', 'admin@briah.co', 'איינב', 'admin',
   '00000000-0000-0000-0000-000000000001');

-- Melavim (guides)
INSERT INTO users (id, email, full_name, role, org_id) VALUES
  ('00000000-0000-0000-0000-000000000020', 'melave1@briah.co', 'רוני כהן', 'melave',
   '00000000-0000-0000-0000-000000000001'),
  ('00000000-0000-0000-0000-000000000021', 'melave2@briah.co', 'נועה לוי', 'melave',
   '00000000-0000-0000-0000-000000000001');

-- Metaplim (therapists)
INSERT INTO users (id, email, full_name, role, org_id) VALUES
  ('00000000-0000-0000-0000-000000000030', 'metapel1@briah.co', 'עמית שמיר', 'metapel',
   '00000000-0000-0000-0000-000000000001'),
  ('00000000-0000-0000-0000-000000000031', 'metapel2@briah.co', 'יערה גולן', 'metapel',
   '00000000-0000-0000-0000-000000000001');

-- Lakochim (participants)
INSERT INTO users (id, email, full_name, role, org_id, phone) VALUES
  ('00000000-0000-0000-0000-000000000040', 'lakoach1@test.co', 'מיכל אברהם', 'lakoach',
   '00000000-0000-0000-0000-000000000001', '+972501234567'),
  ('00000000-0000-0000-0000-000000000041', 'lakoach2@test.co', 'שירה מזרחי', 'lakoach',
   '00000000-0000-0000-0000-000000000001', '+972502345678'),
  ('00000000-0000-0000-0000-000000000042', 'lakoach3@test.co', 'דנה שפירא', 'lakoach',
   '00000000-0000-0000-0000-000000000001', '+972503456789');

-- Profiles
INSERT INTO lakoach_profiles
  (user_id, melave_id, metapel_id, mashlul, start_date, status,
   intake_token, intake_token_expires) VALUES
  ('00000000-0000-0000-0000-000000000040',
   '00000000-0000-0000-0000-000000000020',
   '00000000-0000-0000-0000-000000000030',
   'tzmiha', '2024-01-01', 'active',
   'test-token-lakoach1',
   now() + interval '7 days'),
  ('00000000-0000-0000-0000-000000000041',
   '00000000-0000-0000-0000-000000000020',
   '00000000-0000-0000-0000-000000000031',
   'hamakata', '2024-01-05', 'active',
   'test-token-lakoach2',
   now() + interval '7 days'),
  ('00000000-0000-0000-0000-000000000042',
   '00000000-0000-0000-0000-000000000021',
   '00000000-0000-0000-0000-000000000030',
   'ikur', '2024-01-10', 'active',
   'test-token-lakoach3',
   now() + interval '7 days');

-- Sample intake for lakoach1
INSERT INTO intakes
  (lakoach_id, melave_id, status, resilience_score, score_breakdown, ai_assessment) VALUES
  ('00000000-0000-0000-0000-000000000040',
   '00000000-0000-0000-0000-000000000020',
   'completed', 68,
   '{"karakoa":72,"preka":55,"integrazia":65,"kehila":80,"mashmaut":62}',
   '{"resilience_score":68,"breakdown":{"karakoa":72,"preka":55,"integrazia":65,"kehila":80,"mashmaut":62},"primary_focus":"preka","strengths":["קשר עמוק לאחרים","מודעות עצמית","רצון לשינוי"],"growth_areas":["שחרור ופריקה","חיבור לגוף"],"journey_type":"moderate","recommended_activities":["יוגה סומטית","ריברסינג","מעגל נשים"],"summary_he":"השאלון מגלה אדם עם חוסן בסיסי חזק ויכולת קשר טובה.","personal_letter":"מיכל יקרה,\n\nתודה על הפתיחות.\n\nאנחנו כאן איתך 🤍\n\nבריאה"}');

-- Sample session
INSERT INTO sessions
  (lakoach_id, metapel_id, scheduled_at, status, session_number) VALUES
  ('00000000-0000-0000-0000-000000000040',
   '00000000-0000-0000-0000-000000000030',
   now() + interval '3 days',
   'scheduled', 1);
