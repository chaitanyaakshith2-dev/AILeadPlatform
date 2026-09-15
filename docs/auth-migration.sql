-- LeadFlow AI ownership migration
-- Apply this after docs/database.sql in the Supabase SQL Editor.

alter table public.leads
    add column if not exists user_id uuid;

-- The leads table is currently empty, so ownership can be made mandatory.
alter table public.leads
    alter column user_id set not null;

alter table public.leads
    add constraint leads_user_id_fkey
    foreign key (user_id)
    references auth.users(id)
    on delete cascade;

create index if not exists leads_user_id_idx on public.leads (user_id);

alter table public.leads enable row level security;

drop policy if exists "Users can insert their own leads" on public.leads;
drop policy if exists "Users can select their own leads" on public.leads;
drop policy if exists "Users can update their own leads" on public.leads;
drop policy if exists "Users can delete their own leads" on public.leads;

create policy "Users can insert their own leads"
on public.leads
for insert
to authenticated
with check (user_id = auth.uid());

create policy "Users can select their own leads"
on public.leads
for select
to authenticated
using (user_id = auth.uid());

create policy "Users can update their own leads"
on public.leads
for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy "Users can delete their own leads"
on public.leads
for delete
to authenticated
using (user_id = auth.uid());
