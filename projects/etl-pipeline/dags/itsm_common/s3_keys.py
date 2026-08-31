"""
S3 key convention for landed raw files: <table>/dt=<YYYY-MM-DD>/<table>_<YYYYMMDD>.csv

One function, used by both the extract task (writes the key) and the load task
(reads it back) so the format only exists in one place.

`dt=` is the landing/extraction date, not a signal that the file itself is an
incremental delta. In Phase 1, `_extract_to_s3` always re-uploads the full
synthetic source file regardless of `ds` — there's no real incremental source
system to extract deltas from yet. Every daily run adds a full snapshot under
a new `dt=` partition. True incremental extraction is Phase 3's job; don't
read a `dt=` partition here as "the new rows for that day."
"""


def s3_key_for(table_name: str, ds: str) -> str:
    return f"{table_name}/dt={ds}/{table_name}_{ds.replace('-', '')}.csv"
