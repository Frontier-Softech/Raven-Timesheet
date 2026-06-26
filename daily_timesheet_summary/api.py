import frappe
from .scheduler import send_daily_summary
from .aggregator import fetch_timesheets, aggregate
from .formatter import format_summary


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
    return {
        "row_count": len(rows),
        "total_hours": summary["total"],
        "message": format_summary(summary),
    }
