-- Phase 1 raw landing schema — typed columns only.
-- No PRIMARY KEY / NOT NULL / FK constraints here on purpose: not_null, unique,
-- and relationships checks are Phase 2's job (dbt schema tests), per
-- docs/phase-roadmap.md. A landing zone should accept whatever the source sends,
-- even if it's temporarily incomplete or out of order.

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.staff (
    staff_id     VARCHAR(20),
    name         VARCHAR(255),
    role         VARCHAR(50),
    _ingested_at TIMESTAMP DEFAULT now(),
    _source_key  VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS raw.clients (
    client_id      VARCHAR(20),
    client_name    VARCHAR(255),
    industry       VARCHAR(50),
    contract_tier  VARCHAR(20),
    _ingested_at   TIMESTAMP DEFAULT now(),
    _source_key    VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS raw.assets (
    asset_id      VARCHAR(20),
    client_id     VARCHAR(20),
    asset_type    VARCHAR(50),
    hostname      VARCHAR(100),
    install_date  DATE,
    status        VARCHAR(20),
    _ingested_at  TIMESTAMP DEFAULT now(),
    _source_key   VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS raw.incidents (
    incident_id             VARCHAR(20),
    asset_id                VARCHAR(20),
    client_id               VARCHAR(20),
    opened_at               TIMESTAMP,
    closed_at               TIMESTAMP,
    severity                VARCHAR(20),
    source                  VARCHAR(30),
    assigned_technician_id  VARCHAR(20),
    status                  VARCHAR(20),
    _ingested_at            TIMESTAMP DEFAULT now(),
    _source_key             VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS raw.projects (
    project_id           VARCHAR(20),
    client_id            VARCHAR(20),
    project_name         VARCHAR(255),
    start_date           DATE,
    end_date             DATE,
    contract_type        VARCHAR(30),
    project_manager_id   VARCHAR(20),
    status               VARCHAR(20),
    _ingested_at         TIMESTAMP DEFAULT now(),
    _source_key          VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS raw.timesheets (
    timesheet_id      VARCHAR(20),
    project_id        VARCHAR(20),
    employee_id       VARCHAR(20),
    work_date         DATE,
    hours             NUMERIC(3,1),
    billable          BOOLEAN,
    task_description  TEXT,
    _ingested_at      TIMESTAMP DEFAULT now(),
    _source_key       VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS raw.invoices (
    invoice_id     VARCHAR(20),
    project_id     VARCHAR(20),
    client_id      VARCHAR(20),
    invoice_date   DATE,
    amount         NUMERIC(10,2),
    status         VARCHAR(20),
    _ingested_at   TIMESTAMP DEFAULT now(),
    _source_key    VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS raw.helpdesk_tickets (
    ticket_id                  VARCHAR(20),
    created_at                 TIMESTAMP,
    resolved_at                TIMESTAMP,
    category                   VARCHAR(100),
    description                TEXT,
    requested_by_employee_id   VARCHAR(20),
    assigned_technician_id     VARCHAR(20),
    priority                   VARCHAR(20),
    status                     VARCHAR(20),
    _ingested_at               TIMESTAMP DEFAULT now(),
    _source_key                VARCHAR(500)
);
