import html

from .utils import format_hours, format_date

# Raven's Tiptap renderer runs with Highlight.configure({multicolor: true}),
# which is the one mark that preserves an inline background-color when
# parsing <mark data-color="..." style="background-color:...">. Plain
# <span style="color:..."> has no matching schema rule and gets stripped.
COLOR_BLUE = "#60a5fa"
COLOR_GREEN = "#4ade80"
COLOR_RED = "#f87171"


def _badge(value, color):
    return f'<mark data-color="{color}" style="background-color: {color}"><strong>{value}</strong></mark>'


GAP_ALERT_THRESHOLD = 5


def format_per_employee_messages(summary, stats=None):
    """Return one formatted HTML message string per employee.

    Raven Message.text is rendered as HTML (Tiptap), not markdown/plain
    text, so lines must be wrapped in block tags to get line breaks and
    user-supplied text must be escaped. Each display line gets its own
    <p> rather than <br>-joining multiple lines into one <p> — Tiptap
    has been observed to drop <br> breaks inside a multi-line <p>,
    collapsing lines together.

    Entries are grouped by the work date they were logged against, oldest
    first, so an entry filled today for yesterday's work is shown before
    today's own entries. An <hr> separates date blocks when an employee
    has more than one, so backfilled/multi-day messages don't run
    together.

    `stats`, if given, is { employee_name: {"present", "filled", "window_days"} }
    (see aggregator.fetch_employee_stats) and is rendered as a Present vs
    Timesheet Filled comparison for the trailing window. An employee whose
    gap exceeds GAP_ALERT_THRESHOLD gets their name badge-colored red so
    they stand out on a quick mobile scan.
    """
    employees = summary.get("employees") or {}
    stats = stats or {}
    messages = []

    for emp, emp_data in employees.items():
        emp_total = emp_data.get("total", 0)
        emp_stats = stats.get(emp)
        gap = None
        if emp_stats:
            gap = emp_stats.get("present", 0) - emp_stats.get("filled", 0)

        name_html = html.escape(emp)
        if gap is not None and gap > GAP_ALERT_THRESHOLD:
            name_html = f'<mark data-color="{COLOR_RED}" style="background-color: {COLOR_RED}"><strong>{name_html}</strong></mark>'
        else:
            name_html = f"<strong>{name_html}</strong>"

        blocks = [f"<p>{name_html} <em>({format_hours(emp_total)} hrs)</em></p>"]

        if emp_stats:
            window_days = emp_stats.get("window_days", 30)
            present = emp_stats.get("present", 0)
            filled = emp_stats.get("filled", 0)
            gap_color = COLOR_GREEN if gap <= 0 else COLOR_RED
            blocks.append(
                f"<p><em>{window_days}d</em> — "
                f"P: {_badge(present, COLOR_BLUE)} "
                f"F: {_badge(filled, COLOR_BLUE)} "
                f"Gap: {_badge(max(gap, 0), gap_color)}</p>"
            )

        dates = list(emp_data.get("dates", {}).items())
        for idx, (work_date, date_data) in enumerate(dates):
            if idx > 0:
                blocks.append("<hr>")

            day_total = date_data.get("total", 0)
            date_badge = f'<mark data-color="{COLOR_BLUE}" style="background-color: {COLOR_BLUE}">{html.escape(format_date(work_date))}</mark>'
            blocks.append(
                f"<p>🗓 {date_badge} "
                f"<em>({format_hours(day_total)} hrs)</em></p>"
            )

            for project, entries in date_data.get("projects", {}).items():
                blocks.append(f"<p><strong><em>{html.escape(project)}</em></strong></p>")
                for entry in entries:
                    task = entry.get("task")
                    subject = entry.get("subject")
                    hours = entry.get("hours", 0)
                    descriptions = entry.get("descriptions", [])

                    if task:
                        task_label = html.escape(subject if subject else task)
                        blocks.append(
                            f"<p>• <strong>{task_label}</strong> "
                            f"<em>({format_hours(hours)}h)</em></p>"
                        )
                    else:
                        blocks.append(f"<p>• <em>({format_hours(hours)}h)</em></p>")

                    if descriptions:
                        desc = html.escape("; ".join(descriptions)).replace("\n", "<br>")
                        blocks.append(f"<p><em>{desc}</em></p>")

        messages.append("".join(blocks))

    return messages
