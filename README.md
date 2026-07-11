### Daily Timesheet Summary

Frappe app that posts a daily per-employee timesheet digest into a Raven chat
channel, so managers can see who filled time entries without opening ERPNext.

Runs automatically every day at **19:00** via the Frappe scheduler
(`hooks.py` cron `0 19 * * *`) and posts one message per employee into the
Raven channel named `general`.

### How it works

1. **Fetch** — `aggregator.fetch_timesheets(filled_date=None)` pulls all
   submitted Timesheet Detail rows *entered* on the given date (default:
   today), keyed off `Timesheet Detail.creation`, not the work date itself.
   This matters because an employee may log yesterday's work today — that
   entry is still picked up by today's run.
2. **Aggregate** — `aggregator.aggregate(rows)` groups rows per employee,
   then per work date (oldest first), then per project/task, summing hours
   and collecting descriptions at each level.
3. **Stats** — `aggregator.fetch_employee_stats(end_date=None, window_days=30)`
   computes, per employee over the trailing 30 days:
   - **Present** — distinct Attendance days marked `Present` / `Half Day` /
     `Work From Home`
   - **Filled** — distinct days a submitted Timesheet entry was filled
   - **Gap** — Present − Filled, i.e. days the employee was in but didn't
     log time
4. **Format** — `formatter.format_per_employee_messages(summary, stats)`
   renders one HTML message per employee: name + total hours, the 30-day
   Present/Filled/Gap line (color-coded — green when there's no gap, red
   when there is), then a `Date:` block per work date with project → task
   → time → description.
5. **Send** — `raven.send_message(text, channel_name="general")` inserts a
   `Raven Message` doc into the channel.

Raven's `text` field is rendered by a Tiptap editor, not treated as
markdown/plain text — so the formatter builds real HTML (`<p>`, `<br>`,
`<strong>`, `<em>`) and escapes all user-supplied content. Color badges use
`<mark data-color="..." style="background-color:...">` because that's the
one inline style Raven's Tiptap schema (`Highlight.configure({multicolor:
true})`) actually preserves — a plain `<span style="color:...">` gets
stripped.

### Files

| File | Purpose |
|---|---|
| `scheduler.py` | Entry point run by the cron job; wires fetch → aggregate → stats → format → send |
| `aggregator.py` | SQL fetch + grouping of timesheet rows; attendance-vs-filled stats |
| `formatter.py` | Turns aggregated data into per-employee HTML message strings |
| `raven.py` | Resolves the Raven channel and inserts the message doc |
| `api.py` | Whitelisted endpoints: `trigger_daily_summary`, `preview_daily_summary` |
| `utils.py` | Small helpers: date/hour formatting, logger |

### Manual trigger / preview

Both require System Manager:

```python
# Post today's summary to Raven right now
frappe.call("daily_timesheet_summary.api.trigger_daily_summary")

# Build today's messages without sending, for debugging
frappe.call("daily_timesheet_summary.api.preview_daily_summary")
```

Or from a bench console:

```bash
bench --site your-site.local execute daily_timesheet_summary.api.preview_daily_summary
```

### Configuration

- **Target channel**: `ADMIN_CHANNEL_NAME` in `raven.py` (default `"general"`)
- **Send time**: cron expression in `hooks.py` → `scheduler_events`
- **Attendance/stats window**: `window_days` param on
  `aggregator.fetch_employee_stats` (default 30)

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch version-16
bench install-app daily_timesheet_summary
```

Requires the `raven` app (for the target channel) and `hrms`/ERPNext
Attendance data (for the Present/Filled stats) to be installed on the site.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/daily_timesheet_summary
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
