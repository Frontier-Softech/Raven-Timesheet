import frappe
from collections import defaultdict
from frappe.utils import add_days
from .utils import get_today, create_logger

logger = create_logger()

PRESENT_STATUSES = ("Present", "Half Day", "Work From Home")


def fetch_timesheets(filled_date=None):
    """Fetch all submitted Timesheet Detail rows filled (entered) on the given date,
    regardless of which work date they log time against (an employee may log
    yesterday's work today)."""
    filled_date = filled_date or get_today()

    rows = frappe.db.sql(
        """
        SELECT
            ts.name                                       AS timesheet,
            ts.employee_name                              AS employee,
            DATE(tsd.from_time)                           AS work_date,
            tsd.project                                   AS project_id,
            COALESCE(p.project_name, tsd.project)        AS project,
            tsd.task                                      AS task,
            t.subject                                     AS task_subject,
            tsd.hours                                     AS hours,
            tsd.description                               AS description
        FROM `tabTimesheet` ts
        INNER JOIN `tabTimesheet Detail` tsd ON tsd.parent = ts.name
        LEFT JOIN `tabProject` p ON p.name = tsd.project
        LEFT JOIN `tabTask` t ON t.name = tsd.task
        WHERE ts.docstatus = 1
          AND DATE(tsd.creation) = %(d)s
        """,
        {"d": filled_date},
        as_dict=True,
    )

    logger.info(f"Fetched {len(rows)} timesheet rows filled on {filled_date}")
    return rows


def fetch_employee_stats(end_date=None, window_days=30):
    """Return { employee_name: {"present": int, "filled": int, "window_days": int} }
    for the trailing `window_days` window ending on `end_date` (inclusive):
      - present: distinct Attendance days marked Present/Half Day/Work From Home
      - filled: distinct days a submitted Timesheet entry was filled (by creation date)
    """
    end_date = end_date or get_today()
    start_date = add_days(end_date, -(window_days - 1))

    present_rows = frappe.db.sql(
        """
        SELECT employee_name, COUNT(DISTINCT attendance_date) AS present_days
        FROM `tabAttendance`
        WHERE docstatus = 1
          AND status IN %(statuses)s
          AND attendance_date BETWEEN %(start)s AND %(end)s
        GROUP BY employee_name
        """,
        {"statuses": PRESENT_STATUSES, "start": start_date, "end": end_date},
        as_dict=True,
    )

    filled_rows = frappe.db.sql(
        """
        SELECT ts.employee_name AS employee_name, COUNT(DISTINCT DATE(tsd.creation)) AS filled_days
        FROM `tabTimesheet` ts
        INNER JOIN `tabTimesheet Detail` tsd ON tsd.parent = ts.name
        WHERE ts.docstatus = 1
          AND DATE(tsd.creation) BETWEEN %(start)s AND %(end)s
        GROUP BY ts.employee_name
        """,
        {"start": start_date, "end": end_date},
        as_dict=True,
    )

    stats = defaultdict(lambda: {"present": 0, "filled": 0, "window_days": window_days})
    for r in present_rows:
        stats[r["employee_name"]]["present"] = r["present_days"]
    for r in filled_rows:
        stats[r["employee_name"]]["filled"] = r["filled_days"]

    return dict(stats)


def aggregate(rows):
    """
    Group rows as:
        { employee: { total, dates: { work_date: { total, projects: { project: [
            { task, subject, hours, descriptions } ] } } } } }
    Dates within each employee are ordered oldest first, so entries logged
    today for a previous day's work appear before today's own entries.
    Also returns grand total.
    """
    entry_map = defaultdict(lambda: {"hours": 0.0, "descriptions": [], "subject": None})
    emp_totals = defaultdict(float)
    day_totals = defaultdict(float)
    total = 0.0

    for r in rows:
        employee = r.get("employee") or "(Unknown)"
        work_date = r.get("work_date")
        project = r.get("project") or "(No Project)"
        task = r.get("task") or None
        subject = r.get("task_subject") or None
        hours = float(r.get("hours") or 0)
        description = (r.get("description") or "").strip()

        key = (employee, work_date, project, task)
        entry_map[key]["hours"] += hours
        entry_map[key]["subject"] = subject
        if description:
            entry_map[key]["descriptions"].append(description)
        emp_totals[employee] += hours
        day_totals[(employee, work_date)] += hours
        total += hours

    employees = defaultdict(
        lambda: {"total": 0.0, "dates": defaultdict(lambda: {"total": 0.0, "projects": defaultdict(list)})}
    )
    for (employee, work_date, project, task), entry in entry_map.items():
        employees[employee]["total"] = emp_totals[employee]
        day = employees[employee]["dates"][work_date]
        day["total"] = day_totals[(employee, work_date)]
        day["projects"][project].append({
            "task": task,
            "subject": entry["subject"],
            "hours": entry["hours"],
            "descriptions": entry["descriptions"],
        })

    clean = {}
    for emp, data in employees.items():
        clean[emp] = {
            "total": data["total"],
            "dates": {
                work_date: {"total": day["total"], "projects": dict(day["projects"])}
                for work_date, day in sorted(data["dates"].items(), key=lambda kv: kv[0])
            },
        }
    return {"employees": clean, "total": total}


