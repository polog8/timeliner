# timeliner

Deliverables Gantt planner and scheduler, driven by a Google Sheet.

| Path | What it is |
|---|---|
| `Code/code.gs` | Google Apps Script backend: reads the sheet, writes date changes back. |
| `Code/index.html` | The planner web app served by `doGet`. |
| `Template/` | A ready-to-use reference workbook (`.xlsx`) plus the schema documentation. |
| `CHANGELOG.md` | Everything fixed and added since the first version (in French). |

## Setup

1. Create an Apps Script project containing `code.gs` and an HTML file named `index`.
2. Deploy it as a web app. Choose **Execute as: the user accessing the web app** so
   Google enforces each person's real rights on the sheet — the in-app Read-Only
   switch is a convenience, not an access control.
3. Build your data sheet from `Template/timeliner-planner-template.xlsx` — see
   [`Template/README.md`](Template/README.md) for the schema.
4. Open the web app and paste the sheet URL into the **Connect** dialog.
