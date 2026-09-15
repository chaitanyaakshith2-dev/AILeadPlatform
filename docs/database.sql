-- LeadFlow AI leads table
-- Apply this script in the Supabase SQL Editor.

create extension if not exists pgcrypto;

create table if not exists public.leads (
    id uuid primary key default gen_random_uuid(),
    name text not null check (char_length(trim(name)) > 0),
    email text,
    company text,
    message text not null check (char_length(trim(message)) > 0),
    status text not null default 'new' check (char_length(trim(status)) > 0),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists leads_status_idx on public.leads (status);
create index if not exists leads_created_at_idx on public.leads (created_at desc);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists set_leads_updated_at on public.leads;
create trigger set_leads_updated_at
before update on public.leads
for each row
execute function public.set_updated_at();

-- RLS is enabled before application policies are defined.
-- No policies are created yet, so anon/authenticated clients cannot access rows.
alter table public.leads enable row level security;
