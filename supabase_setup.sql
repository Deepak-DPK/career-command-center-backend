-- 1. Enable pgvector extension
create extension if not exists vector;

-- 2. Create resumes table
create table if not exists public.resumes (
  id uuid primary key default gen_random_uuid(),
  user_id text not null, -- Stores Firebase UID
  resume_name text not null,
  resume_text text not null,
  resume_summary jsonb,
  created_at timestamp default now()
);

-- 3. Create prep_kits table (linked to resumes)
create table if not exists public.prep_kits (
  id uuid primary key default gen_random_uuid(),
  user_id text not null, -- Stores Firebase UID
  resume_id uuid references public.resumes(id) on delete cascade,
  job_description text not null,
  resume_filename text not null,
  prep_kit jsonb not null,
  created_at timestamp default now()
);

-- 4. Create chat_sessions table
create table if not exists public.chat_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id text not null, -- Stores Firebase UID
  resume_id uuid references public.resumes(id) on delete cascade,
  title text not null,
  created_at timestamp default now()
);

-- 5. Create chat_messages table
create table if not exists public.chat_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references public.chat_sessions(id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'system')),
  content text not null,
  created_at timestamp default now()
);

-- 6. Create resume_embeddings table (pgvector)
create table if not exists public.resume_embeddings (
  id bigint generated always as identity primary key,
  resume_id uuid references public.resumes(id) on delete cascade,
  chunk_text text not null,
  embedding vector(768) not null
);

-- 7. Add indexes for performance
create index if not exists resume_embeddings_resume_id_idx on public.resume_embeddings (resume_id);
create index if not exists chat_sessions_resume_id_idx on public.chat_sessions (resume_id);
create index if not exists chat_messages_session_id_idx on public.chat_messages (session_id);

-- Create an HNSW index on the vector column for fast similarity search
create index if not exists resume_embeddings_hnsw_idx 
on public.resume_embeddings 
using hnsw (embedding vector_cosine_ops);

-- 8. Enable Row Level Security (RLS) for privacy
alter table public.resumes enable row level security;
alter table public.prep_kits enable row level security;
alter table public.chat_sessions enable row level security;
alter table public.chat_messages enable row level security;
alter table public.resume_embeddings enable row level security;

-- 9. Public Read/Write Access Policies (Since frontend authenticates via Firebase Auth, Supabase sees requests as anonymous)
create policy "Enable public access to prep kits" on public.prep_kits for all using (true) with check (true);
create policy "Enable public access to resumes" on public.resumes for all using (true) with check (true);
create policy "Enable public access to chat sessions" on public.chat_sessions for all using (true) with check (true);
create policy "Enable public access to chat messages" on public.chat_messages for all using (true) with check (true);
create policy "Enable public access to resume embeddings" on public.resume_embeddings for all using (true) with check (true);

-- 10. Hybrid Search Function (70% Semantic vector matching, 30% Keyword Matching)
create or replace function hybrid_search_resume_chunks(
  query_text text,
  query_embedding vector(768),
  match_count int,
  p_resume_id uuid
)
returns table (
  id bigint,
  chunk_text text,
  similarity float
)
language plpgsql
stable
as $$
begin
  return query
  with vector_matches as (
    select
      re.id,
      re.chunk_text,
      1 - (re.embedding <=> query_embedding) as score
    from public.resume_embeddings re
    where re.resume_id = p_resume_id
    order by re.embedding <=> query_embedding
    limit match_count * 2
  ),
  fts_matches as (
    select
      re.id,
      re.chunk_text,
      ts_rank_cd(to_tsvector('english', re.chunk_text), plainto_tsquery('english', query_text)) as score
    from public.resume_embeddings re
    where re.resume_id = p_resume_id
      and to_tsvector('english', re.chunk_text) @@ plainto_tsquery('english', query_text)
    limit match_count * 2
  )
  select
    coalesce(v.id, f.id) as id,
    coalesce(v.chunk_text, f.chunk_text) as chunk_text,
    -- Apply 70% weight to vector similarity and 30% weight to FTS score
    (coalesce(v.score, 0.0) * 0.7 + coalesce(f.score, 0.0) * 0.3)::float as similarity
  from vector_matches v
  full outer join fts_matches f on v.id = f.id
  order by similarity desc
  limit match_count;
end;
$$;
