-- Enable required extensions
create extension if not exists "pgcrypto"; -- for UUIDs
create extension if not exists "vector";   -- for AI vector embeddings

-- USERS
create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text not null unique,
  role text check (role in ('founder', 'contributor', 'mentor')) not null,
  stage text,
  created_at timestamp default now()
);

-- PLAYBOOKS
create table if not exists playbooks (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  description text,
  tags text[] default '{}',
  stage text,
  owner_id uuid references users(id) on delete cascade,
  version text default 'v1',
  created_at timestamp default now()
);

-- FILES per playbook
create table if not exists playbook_files (
  id uuid primary key default gen_random_uuid(),
  playbook_id uuid references playbooks(id) on delete cascade,
  file_name text not null,
  file_type text check (file_type in ('md', 'pdf', 'csv', 'docx', 'txt')) not null,
  storage_path text not null,
  uploaded_by uuid references users(id),
  created_at timestamp default now()
);

-- FORKS
create table if not exists forks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  playbook_id uuid references playbooks(id) on delete cascade,
  fork_name text,
  created_at timestamp default now()
);

-- PULL REQUESTS
create table if not exists pull_requests (
  id uuid primary key default gen_random_uuid(),
  fork_id uuid references forks(id) on delete cascade,
  user_id uuid references users(id) on delete cascade,
  file_changes jsonb,
  summary text,
  status text check (status in ('open', 'approved', 'rejected', 'merged')) default 'open',
  created_at timestamp default now()
);

-- PR COMMENTS
create table if not exists pr_comments (
  id uuid primary key default gen_random_uuid(),
  pr_id uuid references pull_requests(id) on delete cascade,
  user_id uuid references users(id) on delete cascade,
  file_name text,
  line_number integer,
  comment text,
  emoji text,
  created_at timestamp default now()
);

-- VERSION HISTORY
create table if not exists version_history (
  id uuid primary key default gen_random_uuid(),
  playbook_id uuid references playbooks(id) on delete cascade,
  pr_id uuid references pull_requests(id) on delete cascade,
  version text,
  created_at timestamp default now()
);

-- RECOMMENDATIONS
create table if not exists recommendations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  recommended_pb uuid references playbooks(id) on delete cascade,
  reason text,
  status text check (status in ('new', 'viewed', 'forked')) default 'new',
  created_at timestamp default now()
);

-- EMBEDDINGS (chunk-aware)
create table if not exists embeddings (
  id uuid primary key default gen_random_uuid(),
  file_id uuid references playbook_files(id) on delete cascade,
  pr_id uuid references pull_requests(id) on delete cascade,
  chunk_index integer,
  content text,
  embedding vector(1536),
  type text check (type in ('playbook', 'pr')) not null,
  created_at timestamp default now()
);
