"""
Declarative config for the 8 source tables the ingestion DAG loads.
No logic here — just the shape each table needs downstream (extract -> S3 key,
load -> target columns).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class TableConfig:
    # `name` doubles as the source CSV stem, the S3 key prefix, and the
    # raw.<name> table name — all three are the same string by convention,
    # so it's stored once here rather than duplicated across three fields.
    name: str
    # Ordered to match both the CSV header and raw.<name>'s business columns
    # (i.e. everything except the _ingested_at/_source_key lineage columns).
    columns: list[str]


TABLES: list[TableConfig] = [
    TableConfig("staff", ["staff_id", "name", "role"]),
    TableConfig("clients", ["client_id", "client_name", "industry", "contract_tier"]),
    TableConfig("assets", ["asset_id", "client_id", "asset_type", "hostname", "install_date", "status"]),
    TableConfig("incidents", [
        "incident_id", "asset_id", "client_id", "opened_at", "closed_at",
        "severity", "source", "assigned_technician_id", "status",
    ]),
    TableConfig("projects", [
        "project_id", "client_id", "project_name", "start_date", "end_date",
        "contract_type", "project_manager_id", "status",
    ]),
    TableConfig("timesheets", [
        "timesheet_id", "project_id", "employee_id", "work_date",
        "hours", "billable", "task_description",
    ]),
    TableConfig("invoices", ["invoice_id", "project_id", "client_id", "invoice_date", "amount", "status"]),
    TableConfig("helpdesk_tickets", [
        "ticket_id", "created_at", "resolved_at", "category", "description",
        "requested_by_employee_id", "assigned_technician_id", "priority", "status",
    ]),
]
