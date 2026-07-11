import frappe
from .scheduler import send_daily_summary
from .aggregator import fetch_timesheets, aggregate, fetch_employee_stats
from .formatter import format_per_employee_messages


@frappe.whitelist()
def trigger_daily_summary():
    """Manually trigger the full daily summary flow. Requires System Manager."""
    frappe.only_for("System Manager")
    send_daily_summary()
    return {"status": "ok"}


@frappe.whitelist()
def preview_daily_summary():
    """Return the formatted summary without sending to Raven (for debugging)."""
    frappe.only_for("System Manager")
    rows = fetch_timesheets()
    summary = aggregate(rows)
    stats = fetch_employee_stats()
    return {
        "row_count": len(rows),
        "total_hours": summary["total"],
        "messages": format_per_employee_messages(summary, stats),
    }
