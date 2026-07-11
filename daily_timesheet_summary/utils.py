import frappe
from frappe.utils import getdate, nowdate
import logging


def get_today():
    """Return today's date in server timezone."""
    return getdate(nowdate())


def format_hours(hours):
    """Format float hours into a clean string (e.g. 4.0 -> '4', 4.5 -> '4.5')."""
    hours = float(hours or 0)
    if hours.is_integer():
        return str(int(hours))
    return f"{hours:.2f}".rstrip("0").rstrip(".")


def format_date(d):
    """Format a date value as 'DD-Mon-YYYY' for display in messages."""
    return getdate(d).strftime("%d-%b-%Y")


def create_logger():
    """Return a frappe logger scoped to this app."""
    logger = frappe.logger("daily_timesheet_summary", allow_site=True, file_count=5)
    logger.setLevel(logging.INFO)
    return logger


def validate_timesheet(ts):
    """Basic sanity check on a Timesheet record."""
    return bool(ts.get("name")) and ts.get("docstatus") == 1
