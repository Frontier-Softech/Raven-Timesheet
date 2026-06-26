import frappe
from collections import defaultdict
from .utils import get_today, create_logger

logger = create_logger()


def fetch_timesheets(target_date=None):
    """Fetch all submitted Timesheet Detail rows for the given date."""
    target_date = target_date or get_today()

    rows = frappe.db.sql(
        """
        SELECT
            ts.name           AS timesheet,
            ts.employee_name  AS employee,
            tsd.project       AS project,
            tsd.task          AS task,
            tsd.hours         AS hours
        FROM `tabTimesheet` ts
        INNER JOIN `tabTimesheet Detail` tsd ON tsd.parent = ts.name
        WHERE ts.docstatus = 1
          AND DATE(tsd.from_time) = %(d)s
        """,
        {"d": target_date},
        as_dict=True,
    )

    logger.info(f"Fetched {len(rows)} timesheet rows for {target_date}")
    return rows


def aggregate(rows):
    """
    Group rows as:
        { project: { task: { employee: hours } } }
    Also returns totals.
    """
    summary = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    total = 0.0

    for r in rows:
        project = r.get("project") or "(No Project)"
        task = r.get("task") or "(No Task)"
        employee = r.get("employee") or "(Unknown)"
        hours = float(r.get("hours") or 0)

        summary[project][task][employee] += hours
        total += hours

    # convert nested defaultdicts to regular dicts
    clean = {p: {t: dict(e) for t, e in tasks.items()} for p, tasks in summary.items()}
    return {"data": clean, "total": total}
