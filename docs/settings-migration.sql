-- LeadFlow AI business settings and public capture migration
-- Apply this after docs/database.sql, docs/auth-migration.sql, and docs/ai-migration.sql.

create table if not exists public.business_settings (
    user_id uuid primary key references auth.users(id) on delete cascade,
    business_name text not null default '',
    services_offered text not null default '',
    reply_signature text not null default '',
    webhook_token text not null unique default encode(gen_random_bytes(24), 'hex'),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists business_settings_webhook_token_idx
    on public.business_settings (webhook_token);

alter table public.business_settings enable row level security;

drop policy if exists "Users can select their own business settings" on public.business_settings;
drop policy if exists "Users can insert their own business settings" on public.business_settings;
drop policy if exists "Users can update their own business settings" on public.business_settings;

create policy "Users can select their own business settings"
on public.business_settings
for select
to authenticated
using (user_id = auth.uid());

create policy "Users can insert their own business settings"
on public.business_settings
for insert
to authenticated
with check (user_id = auth.uid());

create policy "Users can update their own business settings"
on public.business_settings
for update
to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

drop trigger if exists set_business_settings_updated_at on public.business_settings;
create trigger set_business_settings_updated_at
before update on public.business_settings
for each row
execute function public.set_updated_at();
