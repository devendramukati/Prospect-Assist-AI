-- Phase 0 foundation schema: customers with PII split into a separate table
-- so downstream analytics/scoring code only ever touches pseudonymous IDs.

create table if not exists customers (
    id uuid primary key default gen_random_uuid(),
    external_ref text unique,
    employment_type text not null check (employment_type in ('salaried', 'gig', 'self_employed', 'business_owner')),
    created_at timestamptz not null default now()
);

create table if not exists customer_pii (
    customer_id uuid primary key references customers(id) on delete cascade,
    full_name text,
    pan_masked text,
    date_of_birth date,
    phone_masked text,
    created_at timestamptz not null default now()
);

alter table customers enable row level security;
alter table customer_pii enable row level security;
