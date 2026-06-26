from .utils import format_hours


def format_summary(summary):
    """Convert aggregated dict into a Raven-friendly markdown summary."""
    data = summary.get("data") or {}
    total = summary.get("total") or 0

    if not data:
        return "📅 **Daily Timesheet Summary**\n\n_No timesheets submitted today._"

    lines = ["📅 **Daily Timesheet Summary**", ""]

    for project, tasks in data.items():
        lines.append(f"**Project: {project}**")
        for task, employees in tasks.items():
            lines.append(f"• {task}")
            for emp, hrs in employees.items():
                lines.append(f"    {emp} – {format_hours(hrs)} Hours")
        lines.append("")

    lines.append(f"**Total Hours Worked Today: {format_hours(total)}**")
    return "\n".join(lines)
