FROM apache/airflow:2.10.0

# dbt checks for git as a general system requirement (needed for git-sourced
# packages) regardless of whether a given project actually uses one — not
# currently needed here, but `dbt debug` reports it as a failed check without
# it, so installing it keeps that check honestly green rather than leaving a
# permanent, ignorable-looking red line.
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
USER airflow

# dbt-core's own pinned dependencies (jinja2, protobuf, etc.) conflict with
# Airflow's — a separate venv keeps dbt fully isolated instead of fighting
# Airflow's dependency tree. Placed under /opt/airflow (AIRFLOW_HOME, already
# owned by the non-root airflow user) rather than bare /opt, which isn't.
# Versions pinned, same reproducibility reasoning as the rest of this stack.
RUN python3 -m venv /opt/airflow/dbt_venv && \
    /opt/airflow/dbt_venv/bin/pip install --no-cache-dir \
        dbt-core==1.8.8 \
        dbt-postgres==1.8.2
