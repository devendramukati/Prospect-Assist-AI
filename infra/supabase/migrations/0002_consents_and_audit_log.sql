-- Phase 6/7: Account Aggregator consent tracking + compliance audit trail.
--
-- The application currently keeps consent state in-memory (MockAAClient)
-- and audit events in structured logs (app/core/audit.py) — this migration
-- defines the target schema for when real persistence replaces both, so
-- that swap is a storage-backend change, not a redesign. See
-- docs/compliance.md for the honest status of what's live vs. planned.

create table if not exists consents (
    id text primary key,
    customer_id uuid references customers(id) on delete cascade,
    external_ref text not null,
    aa_handle text not null,
    fip_id text not null,
    fip_name text not null,
    purpose text not null,
    status text not null check (status in ('pending', 'approved', 'denied', 'expired', 'revoked')),
    data_range_from date not null,
    data_range_to date not null,
    requested_at timestamptz not null,
    approved_at timestamptz,
    expires_at timestamptz not null,
    data_fetched boolean not null default false
);

create index if not exists consents_external_ref_idx on consents (external_ref);

create table if not exists audit_log (
    id bigint generated always as identity primary key,
    entity_type text not null,
    entity_id text not null,
    actor text not null,
    action text not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists audit_log_entity_idx on audit_log (entity_type, entity_id);

alter table consents enable row level security;
alter table audit_log enable row level security;

-- ---------------------------------------------------------------------------
-- RLS policies
--
-- These assume two Supabase custom-claim roles set on the JWT
-- (app_metadata.role): 'loan_officer' and 'admin'. No Supabase Auth is
-- wired into the application yet — these policies are authored and ready
-- to apply once it is, not tested against a live project. Until then, RLS
-- being enabled with no policies for a role means that role is denied by
-- default, which is the safe failure mode.
-- ---------------------------------------------------------------------------

create policy "loan_officers_can_read_customers"
    on customers for select
    to authenticated
    using (auth.jwt() -> 'app_metadata' ->> 'role' in ('loan_officer', 'admin'));

create policy "loan_officers_can_read_consents"
    on consents for select
    to authenticated
    using (auth.jwt() -> 'app_metadata' ->> 'role' in ('loan_officer', 'admin'));

create policy "loan_officers_can_read_audit_log"
    on audit_log for select
    to authenticated
    using (auth.jwt() -> 'app_metadata' ->> 'role' in ('loan_officer', 'admin'));

-- customer_pii (Phase 0) is restricted to admins only. A loan officer
-- reviewing a lead sees the masked KYC fields the API returns (read via the
-- backend's service-role key, which bypasses RLS) — never a direct table
-- grant to raw PII.
create policy "admins_can_read_customer_pii"
    on customer_pii for select
    to authenticated
    using (auth.jwt() -> 'app_metadata' ->> 'role' = 'admin');
