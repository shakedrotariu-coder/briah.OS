# Database Setup

## Schema

Run `schema.sql` in the Supabase SQL Editor to create all tables.

For databases created before the intake-token / AI-assessment / session-number additions,
run the migrations in `migrations/` in order instead of re-running `schema.sql`.

## RLS Setup

After running `schema.sql`, run `rls_policies.sql` in the Supabase SQL Editor.

**IMPORTANT:** Flask uses `SUPABASE_KEY` (the service role key) — this bypasses RLS entirely.
RLS protects against direct browser/anon access to Supabase (e.g. if a client-side script
ever queries Supabase directly instead of going through the Flask backend).
Never expose the service role key in frontend code.
