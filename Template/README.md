# Reference workbook

`timeliner-planner-template.xlsx` is a ready-to-use workbook for the Deliverables Gantt
Planner. It carries the five tabs the tool reads, a filled-in sample programme, and a
`README` tab repeating this page inside the file.

## Getting started

1. **Google Sheets** — *File → Import → Upload*, then choose *Replace spreadsheet*.
   **Excel** — just open it.
2. Replace the sample rows with your own. Nothing needs renaming or moving.
3. Share the sheet with the account running the planner: *Editor* to drag bars and have
   the change written back, *Viewer* for read-only.
4. Paste the sheet URL into the planner's **Connect** dialog.

The `README` tab is ignored by the planner and can be deleted.

## Tabs

The tool matches tab names in lowercase and finds them under no other spelling.

| Tab | Header row? | Content |
|---|---|---|
| `plan` | yes, row 1 | One deliverable per row, from row 2. The only mandatory tab. |
| `stages` | **no** | Column A from **row 1**: stage names, in top-to-bottom chart order. |
| `gates-system` | yes, row 1 | `A` = gate name, `B` = date. Red dashed line. |
| `gates-hc` | yes, row 1 | Same shape. Purple dashed line, H/C badge. |
| `mg-hc` | yes, row 1 | Same shape. Orange dotted line, H/C badge. |
| `capacity` | yes, row 1 | **Optional.** `A` = unit, `B` = from, `C` = to, `D` = FTE. |
| `baseline` | written by the tool | **Optional.** Filled in by “Capture baseline”. |

`stages` is the one tab with no header: row 1 is already data. A stage with no deliverable
is simply not drawn. Extra tabs of your own are safe — only these five are read.

## Columns of `plan`

| Col | Header | Meaning |
|---|---|---|
| A | Ref | Your own reference. Used as the track ID only when `C` is empty. |
| B | Title | Shown on the bar. Square brackets are stripped. |
| C | **Track** | One chart row per distinct value. See below. |
| D | Stage | Which band the track sits in. Fill on the track's first row; the rest inherit. |
| E | Amount | A number: man-hours, or money when `K` says `EUR`. |
| F | Start | A real date, or `N/A` to park the row. |
| G | End | A real date, inclusive. |
| H | Comment | Free text; appears in the tooltip and after the title. |
| I | Owner | Free column, **ignored** by the planner. |
| J | Status | Free column, **ignored** by the planner. |
| K | Currency | `EUR` (or `euro`, `€`) marks a monetary item. Anything else, blank included, means man-hours. |
| L | Unit | Department or team. Drives the filter chips and colours. Blank becomes `Unassigned`. |

Columns can be moved if you rename the header — the planner recognises `Title/Titre`,
`Track/ID`, `Stage/Phase`, `Amount/Montant`, `Start/Debut`, `End/Fin`, `Currency/Devise`,
`Unit/Departement` among others. Leave the layout alone and you never have to think about it.

## The four rules that matter

**A track is a chart row.** Deliverables sharing a value in column `C` stack on the same
line. Two that overlap in time are flagged as a **collision** (red, pulsing) — that is the
point of the field: it tells you the same thread of work is booked twice.

**A track belongs to exactly one stage.** The stage is taken from the first row of that
track that declares one, and applied to all of its deliverables. Leave `D` blank on the
follow-up rows — that is the intended use. Do not spread one track across several stages;
give the later work its own track instead.

**A row is only plotted when both dates are readable.** `N/A` or blank parks it; the count
of skipped rows is reported when the sheet loads. Type real dates — `dd/mm/yyyy` and
`yyyy-mm-dd` text are also understood, but real dates remove any ambiguity.

**Effort is spread evenly over a deliverable's days.** That is how the monthly FTE curve and
the per-year summary are built. The conversion is **1580 h/year = 1 FTE** (131.7 h/month),
fixed in the code — not a cell you can change.

## What the sample shows

A fictitious product-development programme, Jan 2026 → Dec 2027: 26 rows over 5 stages,
19 tracks and 7 units, 12 gates across the three gate tabs. It deliberately includes a
follow-up row inheriting its stage (`TRK-01`), four `EUR` items, two zero-effort
deliverables (hidden until the *0-Mh* toggle is on), and one parked `N/A` row. It contains
no collision, so a clean import shows no red.

Colour coding on the `plan` tab is conditional formatting, purely for your benefit in the
spreadsheet — the planner does not read it:

- amber — parked row, no usable dates
- red — the end date precedes the start date
- green — monetary item

The `README` tab also carries a live cross-check block (totals, FTE-years, horizon)
recomputed from `plan` with formulas, so you can confirm the numbers the planner displays.

## The optional tabs

**`capacity`** declares how many people each unit actually has, as periods rather
than a month grid — a ramp-up is one row, not twelve. Rows for the same unit **add
up**, so a baseline team plus a contractor is two rows. The planner compares this
with the effort the plan demands and flags the months where a unit is short.

A shortfall is judged **per unit and never netted across units**: an idle person in
Purchasing does not cover a missing engineer in Software, so the deficits are summed
rather than cancelled. A month is over capacity when at least one unit is short, even
if the programme balances once every unit is added together. For the same reason the
monthly curve shows demand only — a single capacity line would imply an
interchangeability that does not exist.

Only man-hour deliverables create demand: a line in EUR buys an outcome, it does not
occupy anyone. Delete the tab and the feature switches off.

**`baseline`** is written by the tool, not by hand. Pressing *Capture baseline* in the
Drift view freezes today's dates and amounts here. From then on each bar shows a
hollow ghost where it used to sit, and the Drift view lists what slipped, by how many
days, and how much effort was added or removed.

## Editing from the chart

The planner writes back to the `plan` tab:

- drag a bar sideways to reschedule it, or **onto another track** to move it there —
  the target track's stage wins, since a track lives under exactly one stage;
- double-click an empty spot on a track to create a deliverable there, on that day;
- the editor changes title, track, stage, dates, **amount, currency and unit**;
- *Remove from chart* blanks the two date cells only. The row, its title and its
  amount stay in the sheet, and setting dates again brings it straight back — nothing
  is deleted and no row number shifts under anyone else's open session;
- when deliverables overlap on a track, the collision badge proposes a forward-only
  cascade that clears every overlap while keeping each duration, previewed before it
  is applied and undone in one step.

## Rebuilding

`build_template.py` regenerates the workbook from scratch:

```sh
pip install openpyxl
python3 build_template.py
```

Edit that script rather than the binary when the schema changes, so the template stays
reviewable in git.
