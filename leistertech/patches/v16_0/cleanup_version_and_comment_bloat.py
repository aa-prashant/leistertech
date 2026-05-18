import time

import frappe
from frappe.utils import cint, flt


DEFAULT_BATCH_SIZE = 10000
DEFAULT_SLEEP_SECONDS = 0.05


TARGETS = [
    {
        "label": "Version deleted feed comments",
        "table": "tabComment",
        "where": "reference_doctype=%s and comment_type=%s",
        "values": ("Version", "Deleted"),
        "batch_size": 10000,
    },
    {
        "label": "Deleted Document deleted feed comments",
        "table": "tabComment",
        "where": "reference_doctype=%s and comment_type=%s",
        "values": ("Deleted Document", "Deleted"),
        "batch_size": 10000,
    },
    {
        "label": "Sales Order material_request_child versions",
        "table": "tabVersion",
        "where": "ref_doctype=%s and data like %s",
        "values": ("Sales Order", "%material_request_child%"),
        "batch_size": 5000,
    },
    {
        "label": "Deleted Document recovery rows for Version",
        "table": "tabDeleted Document",
        "where": "deleted_doctype=%s",
        "values": ("Version",),
        "batch_size": 5000,
    },
]


def execute():
    if frappe.conf.get("leistertech_skip_audit_bloat_cleanup"):
        print("Skipping audit bloat cleanup because leistertech_skip_audit_bloat_cleanup is set")
        return

    run_cleanup(dry_run=False)


def dry_run():
    return run_cleanup(dry_run=True)


def run_cleanup(dry_run=False, batch_size=None, sleep_seconds=None, max_batches=None):
    frappe.db.sql("set sql_big_selects=1")

    results = []
    sleep_seconds = _get_sleep_seconds(sleep_seconds)
    batch_size = cint(batch_size) if batch_size else None
    max_batches = cint(max_batches) if max_batches else None

    for target in TARGETS:
        effective_batch_size = batch_size or target.get("batch_size") or DEFAULT_BATCH_SIZE

        if dry_run:
            row_count = _count_target_rows(target)
            results.append({"target": target["label"], "rows": row_count})
            print(f"[dry-run] {target['label']}: {row_count} rows")
            continue

        deleted = _delete_target_in_batches(
            target,
            batch_size=effective_batch_size,
            sleep_seconds=sleep_seconds,
            max_batches=max_batches,
        )
        results.append({"target": target["label"], "deleted": deleted})
        print(f"{target['label']}: deleted {deleted} rows")

    return results


def _get_sleep_seconds(sleep_seconds):
    if sleep_seconds is not None:
        return flt(sleep_seconds)

    return flt(
        frappe.conf.get(
            "leistertech_audit_bloat_cleanup_sleep_seconds",
            DEFAULT_SLEEP_SECONDS,
        )
    )


def _count_target_rows(target):
    result = frappe.db.sql(
        f"select count(*) from `{target['table']}` where {target['where']}",
        target["values"],
    )
    return cint(result[0][0]) if result else 0


def _delete_target_in_batches(target, batch_size, sleep_seconds, max_batches=None):
    total_deleted = 0
    batches = 0

    while True:
        frappe.db.sql(
            f"delete from `{target['table']}` where {target['where']} limit {cint(batch_size)}",
            target["values"],
        )
        deleted = cint(frappe.db.sql("select row_count()")[0][0])
        frappe.db.commit()

        if not deleted:
            break

        batches += 1
        total_deleted += deleted
        print(
            f"{target['label']}: deleted {total_deleted} rows "
            f"({batches} batches of up to {batch_size})"
        )

        if max_batches and batches >= max_batches:
            print(f"{target['label']}: stopped after max_batches={max_batches}")
            break

        if sleep_seconds:
            time.sleep(sleep_seconds)

    return total_deleted
