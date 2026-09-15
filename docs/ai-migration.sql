-- LeadFlow AI analysis migration
-- Apply this after docs/database.sql and docs/auth-migration.sql.

alter table public.leads
    add column if not exists analysis jsonb;

comment on column public.leads.analysis is
    'Structured AI analysis: lead_score, business_type, budget, timeline, requirements, priority, reasoning.';
