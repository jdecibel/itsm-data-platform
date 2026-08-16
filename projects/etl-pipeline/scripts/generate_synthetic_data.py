"""
Generates the managed-services and professional-services synthetic sources,
plus the augmented helpdesk ticket source, all sharing one staff/client
reference pool and one date range so the three sub-domains read as one company.

Input:  data/source/it_service_tickets.csv   (real: Kaggle "IT Service Ticket
        Classification" dataset, adisongoh — columns Document, Topic_group)
Output: data/synthetic/*.csv                 (one file per raw source table)

Deterministic: fixed seed, so re-running produces identical output.
"""
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

SEED = 42
random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE_CSV = BASE_DIR / "data" / "source" / "it_service_tickets.csv"
OUT_DIR = BASE_DIR / "data" / "synthetic"

START_DATE = date(2023, 1, 1)
END_DATE = date(2024, 12, 31)

N_EMPLOYEES = 900  # non-technician staff — helpdesk requesters only
TECHNICIAN_ROLES = {
    "Helpdesk Technician": 15,
    "Field Engineer": 12,
    "Project Manager": 8,
    "Account Manager": 5,
}  # sums to 40 — the cross-domain staff pool
N_CLIENTS = 25
N_ASSETS = 600
N_INCIDENTS = 4000
N_PROJECTS = 100
N_TIMESHEETS = 15000
N_INVOICES = 400


def random_date(start: date, end: date) -> date:
    span = max((end - start).days, 0)
    return start + timedelta(days=random.randint(0, span))


def random_datetime(start: date, end: date) -> datetime:
    d = random_date(start, end)
    return datetime.combine(d, datetime.min.time()) + timedelta(
        hours=random.randint(0, 23), minutes=random.randint(0, 59)
    )


def generate_staff() -> pd.DataFrame:
    rows = []
    staff_id = 1
    for role, count in TECHNICIAN_ROLES.items():
        for _ in range(count):
            rows.append({"staff_id": f"EMP-{staff_id:05d}", "name": fake.name(), "role": role})
            staff_id += 1
    for _ in range(N_EMPLOYEES):
        rows.append({"staff_id": f"EMP-{staff_id:05d}", "name": fake.name(), "role": "Employee"})
        staff_id += 1
    return pd.DataFrame(rows)


def generate_clients() -> pd.DataFrame:
    industries = ["Retail", "Manufacturing", "Healthcare", "Finance", "Logistics", "Education", "Legal", "Real Estate"]
    tiers = ["Basic", "Standard", "Premium"]
    rows = []
    for i in range(1, N_CLIENTS + 1):
        rows.append({
            "client_id": f"CLI-{i:04d}",
            "client_name": fake.company(),
            "industry": random.choice(industries),
            "contract_tier": random.choices(tiers, weights=[0.4, 0.4, 0.2])[0],
        })
    return pd.DataFrame(rows)


def generate_assets(clients_df: pd.DataFrame) -> pd.DataFrame:
    asset_types = ["Server", "Laptop", "Desktop", "Network Switch", "Firewall", "Printer"]
    client_ids = clients_df["client_id"].tolist()
    rows = []
    for i in range(1, N_ASSETS + 1):
        rows.append({
            "asset_id": f"AST-{i:05d}",
            "client_id": random.choice(client_ids),
            "asset_type": random.choice(asset_types),
            "hostname": f"{fake.word()}-{i:04d}",
            "install_date": random_date(START_DATE, END_DATE),
            "status": random.choices(["Active", "Decommissioned"], weights=[0.9, 0.1])[0],
        })
    return pd.DataFrame(rows)


def generate_incidents(assets_df: pd.DataFrame, technicians_df: pd.DataFrame) -> pd.DataFrame:
    severities = ["Low", "Medium", "High", "Critical"]
    statuses = ["Open", "In Progress", "Resolved", "Closed"]
    tech_ids = technicians_df["staff_id"].tolist()
    asset_records = assets_df.to_dict("records")
    rows = []
    for i in range(1, N_INCIDENTS + 1):
        asset = random.choice(asset_records)
        opened = random_datetime(START_DATE, END_DATE)
        status = random.choices(statuses, weights=[0.05, 0.1, 0.35, 0.5])[0]
        closed = opened + timedelta(hours=random.randint(1, 72)) if status in ("Resolved", "Closed") else None
        rows.append({
            "incident_id": f"INC-{i:06d}",
            "asset_id": asset["asset_id"],
            "client_id": asset["client_id"],
            "opened_at": opened,
            "closed_at": closed,
            "severity": random.choices(severities, weights=[0.4, 0.35, 0.2, 0.05])[0],
            "source": random.choices(["monitoring_alert", "manual"], weights=[0.7, 0.3])[0],
            "assigned_technician_id": random.choice(tech_ids),
            "status": status,
        })
    return pd.DataFrame(rows)


def generate_projects(clients_df: pd.DataFrame, pms_df: pd.DataFrame) -> pd.DataFrame:
    contract_types = ["Fixed-Bid", "Time-and-Materials"]
    statuses = ["Planned", "Active", "Completed", "On Hold"]
    client_ids = clients_df["client_id"].tolist()
    pm_ids = pms_df["staff_id"].tolist()
    rows = []
    for i in range(1, N_PROJECTS + 1):
        start = random_date(START_DATE, END_DATE - timedelta(days=60))
        end = start + timedelta(days=random.randint(30, 400))
        rows.append({
            "project_id": f"PRJ-{i:04d}",
            "client_id": random.choice(client_ids),
            "project_name": fake.bs().title(),
            "start_date": start,
            "end_date": end,
            "contract_type": random.choice(contract_types),
            "project_manager_id": random.choice(pm_ids),
            "status": random.choices(statuses, weights=[0.1, 0.4, 0.4, 0.1])[0],
        })
    return pd.DataFrame(rows)


def generate_timesheets(projects_df: pd.DataFrame, technicians_df: pd.DataFrame) -> pd.DataFrame:
    tech_ids = technicians_df["staff_id"].tolist()
    project_records = projects_df.to_dict("records")
    rows = []
    for i in range(1, N_TIMESHEETS + 1):
        project = random.choice(project_records)
        work_end = min(project["end_date"], END_DATE)
        rows.append({
            "timesheet_id": f"TS-{i:06d}",
            "project_id": project["project_id"],
            "employee_id": random.choice(tech_ids),
            "work_date": random_date(project["start_date"], work_end),
            "hours": round(random.uniform(0.5, 8), 1),
            "billable": random.choices([True, False], weights=[0.85, 0.15])[0],
            "task_description": fake.sentence(nb_words=6),
        })
    return pd.DataFrame(rows)


def generate_invoices(projects_df: pd.DataFrame) -> pd.DataFrame:
    statuses = ["Sent", "Paid", "Overdue"]
    project_records = projects_df.to_dict("records")
    rows = []
    for i in range(1, N_INVOICES + 1):
        project = random.choice(project_records)
        rows.append({
            "invoice_id": f"INV-{i:05d}",
            "project_id": project["project_id"],
            "client_id": project["client_id"],
            "invoice_date": random_date(project["start_date"], END_DATE),
            "amount": round(random.uniform(2000, 50000), 2),
            "status": random.choices(statuses, weights=[0.3, 0.6, 0.1])[0],
        })
    return pd.DataFrame(rows)


def generate_helpdesk_tickets(source_df: pd.DataFrame, staff_df: pd.DataFrame, technicians_df: pd.DataFrame) -> pd.DataFrame:
    statuses = ["Open", "In Progress", "Resolved", "Closed"]
    priorities = ["Low", "Medium", "High", "Critical"]
    staff_ids = staff_df["staff_id"].tolist()
    tech_ids = technicians_df["staff_id"].tolist()
    rows = []
    for i, record in enumerate(source_df.itertuples(index=False), start=1):
        created = random_datetime(START_DATE, END_DATE)
        status = random.choices(statuses, weights=[0.05, 0.1, 0.35, 0.5])[0]
        resolved = created + timedelta(hours=random.randint(1, 96)) if status in ("Resolved", "Closed") else None
        if status == "Open":
            assigned = random.choice(tech_ids) if random.random() < 0.6 else None
        else:
            assigned = random.choice(tech_ids)
        rows.append({
            "ticket_id": f"TCK-{i:06d}",
            "created_at": created,
            "resolved_at": resolved,
            "category": record.Topic_group,
            "description": record.Document,
            "requested_by_employee_id": random.choice(staff_ids),
            "assigned_technician_id": assigned,
            "priority": random.choices(priorities, weights=[0.3, 0.4, 0.2, 0.1])[0],
            "status": status,
        })
    return pd.DataFrame(rows)


def main() -> None:
    if not SOURCE_CSV.exists():
        raise FileNotFoundError(
            f"Expected the real ticket dataset at {SOURCE_CSV}.\n"
            "Download 'IT Service Ticket Classification' (Kaggle, adisongoh) and place it there."
        )
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    source_df = pd.read_csv(SOURCE_CSV)

    staff_df = generate_staff()
    technicians_df = staff_df[staff_df["role"] != "Employee"]
    pms_df = staff_df[staff_df["role"] == "Project Manager"]

    clients_df = generate_clients()
    assets_df = generate_assets(clients_df)
    incidents_df = generate_incidents(assets_df, technicians_df)
    projects_df = generate_projects(clients_df, pms_df)
    timesheets_df = generate_timesheets(projects_df, technicians_df)
    invoices_df = generate_invoices(projects_df)
    tickets_df = generate_helpdesk_tickets(source_df, staff_df, technicians_df)

    outputs = {
        "staff.csv": staff_df,
        "clients.csv": clients_df,
        "assets.csv": assets_df,
        "incidents.csv": incidents_df,
        "projects.csv": projects_df,
        "timesheets.csv": timesheets_df,
        "invoices.csv": invoices_df,
        "helpdesk_tickets.csv": tickets_df,
    }
    for filename, df in outputs.items():
        path = OUT_DIR / filename
        df.to_csv(path, index=False)
        print(f"wrote {len(df):>7,} rows -> {path.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
