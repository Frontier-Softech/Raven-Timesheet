import frappe
from .aggregator import fetch_timesheets, aggregate
from .formatter import format_summary
from .raven import send_message
from .utils import create_logger

logger = create_logger()


def send_daily_summary():
    """Entry point invoked by the Frappe scheduler at 18:00 daily."""
    logger.info("Daily Summary Started")
    try:
        rows = fetch_timesheets()
        logger.info(f"Timesheets Fetched: {len(rows)}")

        summary = aggregate(rows)
        logger.info("Aggregation Completed")

        message = format_summary(summary)
        send_message(message)
        logger.info("Notification Sent")

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Daily Timesheet Summary - Scheduler")
        logger.error("Scheduler execution failed")
        raise
    finally:
        logger.info("Execution Finished")
