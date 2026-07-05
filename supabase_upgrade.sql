-- 1. Drop the old insecure public access policy on prep_kits
drop policy if exists "Enable public access to prep kits" on public.prep_kits;
drop policy if exists "Enable public access to prep kits" on prep_kits;

-- 2. Convert user_id column from TEXT to UUID and link it to auth.users
-- Note: If you have existing test records with invalid UUID format, you may want to truncate the table first: truncate table public.prep_kits;
alter table public.prep_kits 
  alter column user_id type uuid using user_id::uuid;

-- Add the foreign key constraint
alter table public.prep_kits 
  add constraint prep_kits_user_id_fkey 
  foreign key (user_id) references auth.users(id) on delete cascade;

-- 3. Add resume_id column referencing the resumes table
alter table public.prep_kits 
  add column if not exists resume_id uuid references public.resumes(id) on delete cascade;

-- 4. Create the new secure, user-locked policy
create policy "Users can manage their own prep kits" 
on public.prep_kits 
for all 
using (auth.uid() = user_id)
with check (auth.uid() = user_id);
