-- supabase_force_upgrade.sql
-- This script dynamically drops all policies on the tables that depend on user_id,
-- alters the user_id column to text (for Firebase Auth), and restores public access policies.

DO $$ 
DECLARE 
    r RECORD;
BEGIN 
    -- 1. Dynamically drop all policies on prep_kits, resumes, chat_sessions, chat_messages, resume_embeddings
    FOR r IN (
        SELECT schemaname, tablename, policyname 
        FROM pg_policies 
        WHERE tablename IN ('prep_kits', 'resumes', 'chat_sessions', 'chat_messages', 'resume_embeddings')
    ) LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I.%I', r.policyname, r.schemaname, r.tablename);
    END LOOP;
END $$;

-- 2. Drop foreign key constraints on user_id (if any exist)
ALTER TABLE public.prep_kits DROP CONSTRAINT IF EXISTS prep_kits_user_id_fkey;
ALTER TABLE public.resumes DROP CONSTRAINT IF EXISTS resumes_user_id_fkey;
ALTER TABLE public.chat_sessions DROP CONSTRAINT IF EXISTS chat_sessions_user_id_fkey;

-- 3. Alter user_id columns back to TEXT to support Firebase Auth UIDs
ALTER TABLE public.prep_kits ALTER COLUMN user_id TYPE text;
ALTER TABLE public.resumes ALTER COLUMN user_id TYPE text;
ALTER TABLE public.chat_sessions ALTER COLUMN user_id TYPE text;

-- 4. Re-enable public read/write access (RLS) so Firebase anonymous/client requests can query and write
CREATE POLICY "Enable public access to prep kits" ON public.prep_kits FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Enable public access to resumes" ON public.resumes FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Enable public access to chat sessions" ON public.chat_sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Enable public access to chat messages" ON public.chat_messages FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Enable public access to resume embeddings" ON public.resume_embeddings FOR ALL USING (true) WITH CHECK (true);
