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


def format_per_employee_messages(summary, stats=None):
    """Return one formatted HTML message string per employee.

    Raven Message.text is rendered as HTML (Tiptap), not markdown/plain
    text, so lines must be wrapped in block tags to get line breaks and
    user-supplied text must be escaped.

    Entries are grouped by the work date they were logged against, oldest
    first, so an entry filled today for yesterday's work is shown before
    today's own entries.

    `stats`, if given, is { employee_name: {"present", "filled", "window_days"} }
    (see aggregator.fetch_employee_stats) and is rendered as a Present vs
    Timesheet Filled comparison for the trailing window.
    """
    employees = summary.get("employees") or {}
    stats = stats or {}
    messages = []

    for emp, emp_data in employees.items():
        emp_total = emp_data.get("total", 0)
        blocks = [
            f"<p><strong>{html.escape(emp)}</strong> "
            f"<em>({format_hours(emp_total)} hrs)</em></p>"
        ]

        emp_stats = stats.get(emp)
        if emp_stats:
            window_days = emp_stats.get("window_days", 30)
            present = emp_stats.get("present", 0)
            filled = emp_stats.get("filled", 0)
            gap = present - filled
            filled_color = COLOR_GREEN if gap <= 0 else COLOR_RED
            gap_color = COLOR_GREEN if gap <= 0 else COLOR_RED
            blocks.append(
                f"<p>📊 <em>Last {window_days} days</em> — "
                f"Present: {_badge(present, COLOR_BLUE)} | "
                f"Timesheet Filled: {_badge(filled, filled_color)} | "
                f"Gap: {_badge(max(gap, 0), gap_color)}</p>"
            )

        for work_date, date_data in emp_data.get("dates", {}).items():
            day_total = date_data.get("total", 0)
            blocks.append(
                f"<p><strong>Date: {html.escape(format_date(work_date))}</strong> "
                f"<em>({format_hours(day_total)} hrs)</em></p>"
            )

            for project, entries in date_data.get("projects", {}).items():
                blocks.append(f"<p><strong>{html.escape(project)}</strong></p>")
                for entry in entries:
                    task = entry.get("task")
                    subject = entry.get("subject")
                    hours = entry.get("hours", 0)
                    descriptions = entry.get("descriptions", [])

                    entry_lines = []
                    if task:
                        task_label = subject if subject else task
                        entry_lines.append(f"Task: {html.escape(task_label)}")
                    entry_lines.append(f"Time: {format_hours(hours)} hrs")
                    if descriptions:
                        desc = html.escape("; ".join(descriptions)).replace("\n", "<br>")
                        entry_lines.append(f"Description: {desc}")

                    blocks.append(f"<p>{'<br>'.join(entry_lines)}</p>")

        messages.append("".join(blocks))

    return messages
