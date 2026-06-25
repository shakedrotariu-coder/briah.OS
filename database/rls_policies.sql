-- ===========================
-- ENABLE RLS ON ALL TABLES
-- ===========================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE lakoach_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE intakes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tochniyot_ishiyot ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE companion_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE wa_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- ===========================
-- SERVICE ROLE BYPASS (Flask uses service key — full access)
-- ===========================
-- The Flask backend uses the Supabase SERVICE KEY (not anon key).
-- The service key bypasses RLS automatically.
-- RLS below only blocks direct anon/user access (e.g. browser calling Supabase directly).

-- ===========================
-- USERS TABLE
-- ===========================
-- Users can only read their own row
CREATE POLICY "users_read_own" ON users
  FOR SELECT USING (auth.uid() = id);

-- Service role (Flask) can do everything — handled by service key bypass

-- ===========================
-- LAKOACH_PROFILES
-- ===========================
-- Lakoach can only see their own profile
CREATE POLICY "lakoach_profiles_own" ON lakoach_profiles
  FOR SELECT USING (
    auth.uid() = user_id
  );

-- Melave can see profiles where they are the melave
CREATE POLICY "lakoach_profiles_melave" ON lakoach_profiles
  FOR SELECT USING (
    auth.uid() = melave_id
  );

-- ===========================
-- INTAKES
-- ===========================
CREATE POLICY "intakes_lakoach_own" ON intakes
  FOR SELECT USING (auth.uid() = lakoach_id);

CREATE POLICY "intakes_melave_own" ON intakes
  FOR SELECT USING (auth.uid() = melave_id);

-- ===========================
-- COMPANION_LOGS
-- ===========================
CREATE POLICY "companion_logs_own" ON companion_logs
  FOR SELECT USING (auth.uid() = lakoach_id);

-- ===========================
-- SESSIONS
-- ===========================
CREATE POLICY "sessions_lakoach" ON sessions
  FOR SELECT USING (auth.uid() = lakoach_id);

CREATE POLICY "sessions_metapel" ON sessions
  FOR SELECT USING (auth.uid() = metapel_id);

-- ===========================
-- WA_MESSAGES
-- ===========================
CREATE POLICY "wa_messages_own" ON wa_messages
  FOR SELECT USING (auth.uid() = user_id);
