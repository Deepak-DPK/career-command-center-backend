-- 1. Drop foreign key constraints on user_id (since we authenticate via Firebase, not Supabase Auth)
alter table public.prep_kits drop constraint if exists prep_kits_user_id_fkey;
alter table public.resumes drop constraint if exists resumes_user_id_fkey;
alter table public.chat_sessions drop constraint if exists chat_sessions_user_id_fkey;

-- 2. Alter user_id columns back to TEXT to support Firebase Auth UIDs
alter table public.prep_kits alter column user_id type text;
alter table public.resumes alter column user_id type text;
alter table public.chat_sessions alter column user_id type text;

-- 3. Drop restricted RLS policies that require Supabase Auth
drop policy if exists "Users can manage their own prep kits" on public.prep_kits;
drop policy if exists "Users can manage their own resumes" on public.resumes;
drop policy if exists "Users can manage their own chat sessions" on public.chat_sessions;
drop policy if exists "Users can view/write chat messages under their sessions" on public.chat_messages;
drop policy if exists "Users can manage embeddings linked to their own resumes" on public.resume_embeddings;

-- 4. Re-enable public read/write access (RLS) so Firebase anonymous/client requests can query and write
create policy "Enable public access to prep kits" 
on public.prep_kits for all using (true) with check (true);

create policy "Enable public access to resumes" 
on public.resumes for all using (true) with check (true);

create policy "Enable public access to chat sessions" 
on public.chat_sessions for all using (true) with check (true);

create policy "Enable public access to chat messages" 
on public.chat_messages for all using (true) with check (true);

create policy "Enable public access to resume embeddings" 
on public.resume_embeddings for all using (true) with check (true);
