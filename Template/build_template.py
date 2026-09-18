"""Builds the reference workbook for the Deliverables Gantt Planner.

Tab names, column positions and the N/A convention are dictated by
Code/code.gs (SHEET_NAMES, PLAN_DEFAULT_COLS, COLUMN_ALIASES, parseDateVal).
"""
import datetime as dt
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

OUT = "timeliner-planner-template.xlsx"   # written next to this script
LAST = 120                      # rows reserved for data on the plan tab
FONT = "Arial"

INK        = "1F2937"
MUTED      = "6B7280"
HEADER_BG  = "1E3A8A"
HEADER_FG  = "FFFFFF"
INPUT_BG   = "FFF9DB"           # cells the user fills in
EUR_BG     = "ECFDF5"
SKIP_BG    = "FEF3C7"
ERR_BG     = "FEE2E2"
RULE       = "CBD5E1"

thin = Side(style="thin", color=RULE)
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

STAGES = [
    "Stage 1 - Concept & Requirements",
    "Stage 2 - Design & Architecture",
    "Stage 3 - Industrialisation",
    "Stage 4 - Validation & Qualification",
    "Stage 5 - Ramp-up & Closure",
]

UNITS = ["Program", "Systems", "Mechanical", "Electronics", "Software", "Quality", "Purchasing"]

D = dt.date
# Ref, Title, Track, Stage, Amount, Start, End, Comment, Owner, Status, Currency, Unit
PLAN = [
    ("D-001", "Market & customer requirements",      "TRK-01", STAGES[0],    320, D(2026,1,5),  D(2026,2,27),  "Voice-of-customer workshops",              "A. Martin", "Done",        "",    "Program"),
    ("D-002", "System requirements specification",   "TRK-01", "",           480, D(2026,3,2),  D(2026,4,30),  "Stage left blank: inherited from D-001",   "A. Martin", "In progress", "",    "Systems"),
    ("D-003", "Feasibility & concept trade-off",     "TRK-02", STAGES[0],    260, D(2026,1,12), D(2026,3,13),  "Three concepts compared",                  "L. Dubois", "Done",        "",    "Systems"),
    ("D-004", "Regulatory & homologation study",     "TRK-03", STAGES[0],  18000, D(2026,2,2),  D(2026,3,31),  "External consultancy, fixed price",        "C. Nguyen", "Done",        "EUR", "Quality"),
    ("D-005", "Mechanical architecture & CAD",       "TRK-04", STAGES[1],    960, D(2026,4,6),  D(2026,7,31),  "",                                         "P. Roy",    "In progress", "",    "Mechanical"),
    ("D-006", "Detailed mechanical drawings",        "TRK-04", "",           640, D(2026,8,3),  D(2026,10,30), "Follows D-005 on the same track",          "P. Roy",    "Not started", "",    "Mechanical"),
    ("D-007", "Electronics board design",            "TRK-05", STAGES[1],    720, D(2026,4,6),  D(2026,8,28),  "Two board revisions planned",              "S. Keller", "In progress", "",    "Electronics"),
    ("D-008", "Prototype PCB manufacturing",         "TRK-05", "",         45000, D(2026,9,1),  D(2026,10,16), "Supplier quote Q-2291",                    "S. Keller", "Not started", "EUR", "Purchasing"),
    ("D-009", "Embedded firmware v1",                "TRK-06", STAGES[1],    880, D(2026,5,4),  D(2026,9,30),  "",                                         "M. Okafor", "In progress", "",    "Software"),
    ("D-010", "Diagnostics & test software",         "TRK-07", STAGES[1],    400, D(2026,6,1),  D(2026,9,30),  "",                                         "M. Okafor", "Not started", "",    "Software"),
    ("D-011", "Design review documentation pack",    "TRK-08", STAGES[1],      0, D(2026,7,1),  D(2026,7,31),  "Zero effort: hidden until the 0-Mh toggle","C. Nguyen", "Not started", "",    "Quality"),
    ("D-012", "Tooling specification",               "TRK-09", STAGES[2],    300, D(2026,10,1), D(2026,12,18), "",                                         "P. Roy",    "Not started", "",    "Mechanical"),
    ("D-013", "Injection tooling purchase",          "TRK-09", "",        128000, D(2027,1,4),  D(2027,4,30),  "Long-lead item",                           "J. Silva",  "Not started", "EUR", "Purchasing"),
    ("D-014", "Assembly line concept",               "TRK-10", STAGES[2],    540, D(2026,11,2), D(2027,2,26),  "",                                         "J. Silva",  "Not started", "",    "Mechanical"),
    ("D-015", "Supplier qualification",              "TRK-11", STAGES[2],    380, D(2026,11,2), D(2027,3,31),  "Six suppliers in scope",                   "J. Silva",  "Not started", "",    "Purchasing"),
    ("D-016", "Firmware v2 - production intent",     "TRK-12", STAGES[2],    520, D(2026,11,2), D(2027,3,31),  "",                                         "M. Okafor", "Not started", "",    "Software"),
    ("D-017", "Environmental & EMC test campaign",   "TRK-13", STAGES[3],    620, D(2027,3,1),  D(2027,6,30),  "",                                         "C. Nguyen", "Not started", "",    "Quality"),
    ("D-018", "External EMC laboratory",             "TRK-14", STAGES[3],  34000, D(2027,4,1),  D(2027,5,31),  "Accredited lab, fixed price",              "C. Nguyen", "Not started", "EUR", "Quality"),
    ("D-019", "Durability & life testing",           "TRK-13", "",           480, D(2027,7,1),  D(2027,9,30),  "Follows D-017 on the same track",          "C. Nguyen", "Not started", "",    "Quality"),
    ("D-020", "Software validation & release",       "TRK-15", STAGES[3],    460, D(2027,4,1),  D(2027,7,30),  "",                                         "M. Okafor", "Not started", "",    "Software"),
    ("D-021", "Safety case & certification file",    "TRK-16", STAGES[3],    340, D(2027,5,3),  D(2027,8,31),  "",                                         "L. Dubois", "Not started", "",    "Systems"),
    ("D-022", "Pilot run & process capability",      "TRK-17", STAGES[4],    700, D(2027,9,1),  D(2027,11,30), "200 units built",                          "J. Silva",  "Not started", "",    "Mechanical"),
    ("D-023", "Production ramp-up support",          "TRK-18", STAGES[4],    520, D(2027,10,1), D(2027,12,31), "",                                         "J. Silva",  "Not started", "",    "Program"),
    ("D-024", "Project closure & lessons learned",   "TRK-17", "",           120, D(2027,12,1), D(2027,12,23), "Follows D-022 on the same track",          "A. Martin", "Not started", "",    "Program"),
    ("D-025", "Spare parts catalogue",               "TRK-19", STAGES[4],      0, D(2027,11,1), D(2027,12,15), "Zero-effort deliverable",                  "J. Silva",  "Not started", "",    "Purchasing"),
    ("D-026", "Post-launch marketing kit",           "TRK-20", STAGES[4],    150, "N/A",        "N/A",         "Dates not fixed: ignored until both are set","A. Martin","Not started", "",    "Program"),
]

GATES = {
    "gates-system": [("SR1 - Concept freeze", D(2026,4,15)), ("SR2 - Design freeze", D(2026,10,15)),
                     ("SR3 - Industrialisation gate", D(2027,3,15)), ("SR4 - Production release", D(2027,10,15))],
    "gates-hc":     [("HC-R1 - Requirements review", D(2026,3,16)), ("HC-R2 - Preliminary design review", D(2026,7,15)),
                     ("HC-R3 - Critical design review", D(2026,11,16)), ("HC-R4 - Test readiness review", D(2027,5,14))],
    "mg-hc":        [("MG1 - Maturity level 1", D(2026,6,15)), ("MG2 - Maturity level 2", D(2026,12,15)),
                     ("MG3 - Maturity level 3", D(2027,6,15)), ("MG4 - Maturity level 4", D(2027,11,15))],
}

wb = Workbook()


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(name=FONT, bold=True, color=HEADER_FG, size=10)
        cell.fill = PatternFill("solid", fgColor=HEADER_BG)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BOX


# ---------------------------------------------------------------- README ---
readme = wb.active
readme.title = "README"
readme.sheet_view.showGridLines = False
readme.column_dimensions["A"].width = 3
readme.column_dimensions["B"].width = 26
readme.column_dimensions["C"].width = 15
readme.column_dimensions["D"].width = 86
for col in "EF":
    readme.column_dimensions[col].width = 16

def put(ref, value, *, bold=False, size=10, color=INK, fill=None, italic=False, wrap=False, fmt=None):
    cell = readme[ref]
    cell.value = value
    cell.font = Font(name=FONT, bold=bold, size=size, color=color, italic=italic)
    if fill:
        cell.fill = PatternFill("solid", fgColor=fill)
    cell.alignment = Alignment(vertical="top", wrap_text=wrap)
    if fmt:
        cell.number_format = fmt
    return cell

put("B2", "Deliverables Gantt Planner - reference workbook", bold=True, size=16)
put("B3", "Import this file into Google Sheets (File > Import > Upload), then paste the sheet URL into the planner's \"Connect\" dialog.",
    color=MUTED)

put("B5", "How to use this file", bold=True, size=12)
rows_intro = [
    ("1.", "Keep the tab names exactly as they are: plan, stages, gates-system, gates-hc, mg-hc. They are matched in lowercase and the planner will not find them under any other name."),
    ("2.", "Replace the sample rows with your own. Nothing else has to be renamed or moved."),
    ("3.", "Yellow cells are the ones you fill in. This README tab is ignored by the planner - you may delete it once you are comfortable with the format."),
    ("4.", "Share the Google Sheet with the account running the planner (Editor if you want to drag bars and have the change written back; Viewer is enough for read-only)."),
]
r = 6
for num, text in rows_intro:
    put(f"B{r}", num, bold=True)
    put(f"C{r}", text, wrap=True)
    readme.merge_cells(f"C{r}:F{r}")
    readme.row_dimensions[r].height = 30
    r += 1

# --- tab reference table
r += 1
tab_head = r
put(f"B{r}", "Tab")
put(f"C{r}", "Header row?")
put(f"D{r}", "What the planner reads")
style_header(readme, r, 4)
readme.merge_cells(start_row=r, start_column=4, end_row=r, end_column=6)
r += 1
tabs = [
    ("plan", "Yes, row 1", "One row per deliverable, from row 2 down. This is the only mandatory tab."),
    ("stages", "NO", "Column A, from row 1: the stage names in the order they should appear top-to-bottom in the chart. Duplicates are ignored."),
    ("gates-system", "Yes, row 1", "A = gate name, B = date, from row 2. Drawn as a red dashed line."),
    ("gates-hc", "Yes, row 1", "Same shape. Drawn as a purple dashed line with an H/C badge."),
    ("mg-hc", "Yes, row 1", "Same shape. Drawn as an orange dotted line with an H/C badge."),
]
for name, hdr, desc in tabs:
    put(f"B{r}", name, bold=True)
    put(f"C{r}", hdr, color="B45309" if hdr == "NO" else MUTED)
    put(f"D{r}", desc, wrap=True)
    readme.merge_cells(start_row=r, start_column=4, end_row=r, end_column=6)
    for c in range(2, 7):
        readme.cell(row=r, column=c).border = BOX
    readme.row_dimensions[r].height = 28
    r += 1

# --- column reference table
r += 1
put(f"B{r}", "Columns of the \"plan\" tab", bold=True, size=12)
r += 1
col_head = r
put(f"B{r}", "Column")
put(f"C{r}", "Header")
put(f"D{r}", "Meaning")
style_header(readme, r, 4)
readme.merge_cells(start_row=r, start_column=4, end_row=r, end_column=6)
r += 1
cols = [
    ("A", "Ref", "Your own reference. Used as the track ID only when column C is empty; otherwise free text."),
    ("B", "Title", "Shown on the bar. Square brackets are stripped out."),
    ("C", "Track", "THE KEY FIELD. One chart row per distinct value. Deliverables sharing a track stack on the same line, and two that overlap in time are flagged as a collision."),
    ("D", "Stage", "Which band the track belongs to. Fill it on the track's first row only - the other rows inherit it. A track belongs to exactly one stage, so do not spread one track across several stages."),
    ("E", "Amount", "A number. Man-hours when column K is empty, a monetary amount when column K says EUR."),
    ("F", "Start", "A real date. Type N/A (or leave blank) to park a deliverable: the row is then skipped."),
    ("G", "End", "A real date, inclusive. If it is earlier than the start the planner swaps the two."),
    ("H", "Comment", "Free text, shown in the tooltip and in brackets after the title."),
    ("I", "Owner", "Free column, IGNORED by the planner. Yours to use."),
    ("J", "Status", "Free column, IGNORED by the planner. Yours to use."),
    ("K", "Currency", "EUR (or euro / the euro sign) marks a monetary item, drawn in green and totalled separately. Anything else, including blank, means man-hours."),
    ("L", "Unit", "Department or team. Drives the filter chips and the per-unit colour. Blank becomes \"Unassigned\"."),
]
for letter, hdr, desc in cols:
    put(f"B{r}", letter, bold=True)
    put(f"C{r}", hdr, bold=True, color="1D4ED8" if letter not in "IJ" else MUTED)
    put(f"D{r}", desc, wrap=True)
    readme.merge_cells(start_row=r, start_column=4, end_row=r, end_column=6)
    for c in range(2, 7):
        readme.cell(row=r, column=c).border = BOX
    readme.row_dimensions[r].height = 26
    r += 1

# --- rules
r += 1
put(f"B{r}", "Rules worth knowing", bold=True, size=12)
r += 1
notes = [
    "Dates: type them as real dates. The planner also reads dd/mm/yyyy and yyyy-mm-dd text, but real dates avoid any ambiguity.",
    "A row is only plotted when BOTH dates are readable. Everything else is skipped and reported in the status bar.",
    "Effort is spread evenly over the days of a deliverable, which is how the monthly FTE curve and the yearly summary are built.",
    "Conversion used by the tool: 1560 h/year = 1 FTE (130 h/month). This is a fixed convention in the code, not a cell you can change here.",
    "Columns can be moved if you rename the header: the planner recognises, among others, Title/Titre, Track/ID, Stage/Phase, Amount/Montant, Start/Debut, End/Fin, Currency/Devise, Unit/Departement. Leave the layout as-is and you never have to think about it.",
    "Adding extra tabs is safe - only the five named tabs are read.",
]
for text in notes:
    put(f"B{r}", "-", bold=True)
    put(f"C{r}", text, wrap=True)
    readme.merge_cells(start_row=r, start_column=3, end_row=r, end_column=6)
    readme.row_dimensions[r].height = 26
    r += 1

# --- live cross-check
r += 1
put(f"B{r}", "Cross-check (recomputed from the plan tab)", bold=True, size=12)
r += 1
put(f"B{r}", "These cells mirror what the planner should display. If a figure looks wrong, the data is wrong.", italic=True, color=MUTED, wrap=True)
readme.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
r += 2

# Plain SUMIFS/COUNTIFS wherever possible: dates are numbers, so ">=1" selects a
# readable date and rejects "N/A", which is exactly the planner's skipping rule.
checks = [
    ("Deliverables listed",     f'=COUNTA(plan!$B$2:$B${LAST})', "0"),
    # Both dates readable is exactly the planner's rule for drawing a row.
    ("Deliverables plotted",    f'=COUNTIFS(plan!$F$2:$F${LAST},">=1",plan!$G$2:$G${LAST},">=1")', "0"),
    ("Rows skipped (no dates)", None, "0"),
    ("Distinct tracks plotted", None, "0"),
    ("Total effort (Mh)",       f'=SUMIFS(plan!$E$2:$E${LAST},plan!$K$2:$K${LAST},"<>EUR",plan!$F$2:$F${LAST},">=1",plan!$G$2:$G${LAST},">=1")', "#,##0"),
    ("Equivalent FTE-years",    None, "0.00"),
    ("Total budget (EUR)",      f'=SUMIFS(plan!$E$2:$E${LAST},plan!$K$2:$K${LAST},"EUR",plan!$F$2:$F${LAST},">=1",plan!$G$2:$G${LAST},">=1")', "#,##0"),
    ("Earliest start",          f'=MIN(plan!$F$2:$F${LAST})', "yyyy-mm-dd"),
    ("Latest end",              f'=MAX(plan!$G$2:$G${LAST})', "yyyy-mm-dd"),
]

# Distinct plotted tracks. PLOTTED is 1 for a row the planner draws and 0 otherwise;
# adding (1 - PLOTTED) to the denominator keeps it >= 1, so a parked or empty row
# contributes 0/1 instead of 0/0.
PLOTTED = (f'(plan!$C$2:$C${LAST}<>"")*ISNUMBER(plan!$F$2:$F${LAST})*ISNUMBER(plan!$G$2:$G${LAST})')
DISTINCT = (
    f'=SUMPRODUCT({PLOTTED}/('
    f'COUNTIFS(plan!$C$2:$C${LAST},plan!$C$2:$C${LAST}&"",'
    f'plan!$F$2:$F${LAST},">=1",plan!$G$2:$G${LAST},">=1")+1-{PLOTTED}))'
)

check_first = r
for label, formula, fmt in checks:
    put(f"B{r}", label)
    readme.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
    cell = readme[f"D{r}"]
    if label == "Rows skipped (no dates)":
        cell.value = f"=D{check_first}-D{check_first + 1}"
    elif label == "Distinct tracks plotted":
        cell.value = DISTINCT
    elif label == "Equivalent FTE-years":
        cell.value = f"=D{check_first + 4}/1560"
    else:
        cell.value = formula
    cell.font = Font(name=FONT, bold=True, size=10, color="1D4ED8")
    cell.number_format = fmt
    cell.alignment = Alignment(horizontal="left")
    for c in (2, 3, 4):
        readme.cell(row=r, column=c).border = BOX
    r += 1

r += 1
put(f"B{r}", "Sample data is illustrative only - a fictitious product-development programme. Replace it entirely.",
    italic=True, color=MUTED)
readme.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)


# ------------------------------------------------------------------ plan ---
plan = wb.create_sheet("plan")
headers = ["Ref", "Title", "Track", "Stage", "Amount", "Start", "End", "Comment", "Owner", "Status", "Currency", "Unit"]
widths  = [10, 40, 11, 34, 11, 12, 12, 42, 12, 13, 11, 14]
for i, (h, w) in enumerate(zip(headers, widths), start=1):
    plan.cell(row=1, column=i, value=h)
    plan.column_dimensions[get_column_letter(i)].width = w
style_header(plan, 1, len(headers))
plan.row_dimensions[1].height = 24
plan.freeze_panes = "C2"

for ri, row in enumerate(PLAN, start=2):
    for ci, value in enumerate(row, start=1):
        cell = plan.cell(row=ri, column=ci, value=value if value != "" else None)
        cell.font = Font(name=FONT, size=10, color=INK)
        cell.border = BOX
        cell.alignment = Alignment(vertical="center",
                                   horizontal="right" if ci == 5 else ("center" if ci in (3, 6, 7, 10, 11) else "left"))
        if ci == 5:
            cell.number_format = "#,##0"
        if ci in (6, 7) and isinstance(value, dt.date):
            cell.number_format = "yyyy-mm-dd"

# Blank rows stay ready to type into.
for ri in range(2 + len(PLAN), LAST + 1):
    for ci in range(1, len(headers) + 1):
        cell = plan.cell(row=ri, column=ci)
        cell.font = Font(name=FONT, size=10, color=INK)
        cell.border = BOX
        if ci == 5:
            cell.number_format = "#,##0"
        if ci in (6, 7):
            cell.number_format = "yyyy-mm-dd"

dv_currency = DataValidation(type="list", formula1='"EUR,MH"', allow_blank=True, showErrorMessage=False)
dv_currency.prompt = "EUR = monetary item. Blank or MH = man-hours."
dv_currency.promptTitle = "Currency"
plan.add_data_validation(dv_currency)
dv_currency.add(f"K2:K{LAST}")

dv_unit = DataValidation(type="list", formula1='"' + ",".join(UNITS) + '"', allow_blank=True, showErrorMessage=False)
dv_unit.prompt = "Department or team. Blank becomes Unassigned."
dv_unit.promptTitle = "Unit"
plan.add_data_validation(dv_unit)
dv_unit.add(f"L2:L{LAST}")

dv_stage = DataValidation(type="list", formula1=f"=stages!$A$1:$A${len(STAGES) + 10}",
                          allow_blank=True, showErrorMessage=False)
dv_stage.prompt = "Pick a stage from the stages tab. Leave blank to inherit the track's stage."
dv_stage.promptTitle = "Stage"
plan.add_data_validation(dv_stage)
dv_stage.add(f"D2:D{LAST}")

body = f"A2:L{LAST}"
# Monetary rows in green, parked rows in amber, an end before its start in red.
plan.conditional_formatting.add(body, FormulaRule(
    formula=[f'AND($B2<>"",OR($F2="",$G2="",UPPER($F2&"")="N/A",UPPER($G2&"")="N/A"))'],
    fill=PatternFill("solid", fgColor=SKIP_BG), stopIfTrue=False))
plan.conditional_formatting.add(body, FormulaRule(
    formula=[f'AND(ISNUMBER($F2),ISNUMBER($G2),$G2<$F2)'],
    fill=PatternFill("solid", fgColor=ERR_BG), stopIfTrue=False))
plan.conditional_formatting.add(body, FormulaRule(
    formula=[f'UPPER($K2&"")="EUR"'],
    fill=PatternFill("solid", fgColor=EUR_BG), stopIfTrue=False))

plan["B1"].comment = Comment(
    "One row per deliverable, from row 2 down.\n"
    "Amber = parked (no usable dates, skipped by the planner).\n"
    "Red = the end date precedes the start date.\n"
    "Green = monetary item (column K = EUR).", "Template", height=120, width=300)
plan["C1"].comment = Comment(
    "Deliverables sharing a track are drawn on the same chart row.\n"
    "Two that overlap in time are flagged as a collision.", "Template", height=90, width=280)


# ---------------------------------------------------------------- stages ---
stages = wb.create_sheet("stages")
stages.column_dimensions["A"].width = 40
stages.column_dimensions["C"].width = 60
for i, name in enumerate(STAGES, start=1):
    cell = stages.cell(row=i, column=1, value=name)
    cell.font = Font(name=FONT, size=10, color=INK)
    cell.fill = PatternFill("solid", fgColor=INPUT_BG)
    cell.border = BOX
for i in range(len(STAGES) + 1, len(STAGES) + 11):
    cell = stages.cell(row=i, column=1)
    cell.fill = PatternFill("solid", fgColor=INPUT_BG)
    cell.border = BOX
note = stages.cell(row=1, column=3,
                   value="NO HEADER ROW on this tab: row 1 is already the first stage. "
                         "The order here is the top-to-bottom order of the bands in the chart. "
                         "A stage with no deliverable is simply not drawn.")
note.font = Font(name=FONT, size=10, italic=True, color=MUTED)
note.alignment = Alignment(vertical="top", wrap_text=True)
stages.merge_cells("C1:C4")
stages["A1"].comment = Comment("Row 1 is data, not a header. Do not insert a title row above it.",
                               "Template", height=70, width=260)


# ----------------------------------------------------------------- gates ---
GATE_NOTE = {
    "gates-system": "System review gates - red dashed line.",
    "gates-hc": "H/C review gates - purple dashed line with an H/C badge.",
    "mg-hc": "H/C maturity gates - orange dotted line with an H/C badge.",
}
for tab, entries in GATES.items():
    ws = wb.create_sheet(tab)
    ws.column_dimensions["A"].width = 36
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["D"].width = 58
    ws.cell(row=1, column=1, value="Gate")
    ws.cell(row=1, column=2, value="Date")
    style_header(ws, 1, 2)
    ws.freeze_panes = "A2"
    for i, (name, date) in enumerate(entries, start=2):
        c1 = ws.cell(row=i, column=1, value=name)
        c2 = ws.cell(row=i, column=2, value=date)
        c2.number_format = "yyyy-mm-dd"
        for c in (c1, c2):
            c.font = Font(name=FONT, size=10, color=INK)
            c.border = BOX
        c2.alignment = Alignment(horizontal="center")
    for i in range(2 + len(entries), 2 + len(entries) + 10):
        for col in (1, 2):
            cell = ws.cell(row=i, column=col)
            cell.border = BOX
            cell.font = Font(name=FONT, size=10)
            if col == 2:
                cell.number_format = "yyyy-mm-dd"
    n = ws.cell(row=2, column=4,
                value=GATE_NOTE[tab] + " Header row in row 1, one gate per row from row 2. "
                      "A gate without a name or without a readable date is ignored. "
                      "Drag a gate tag in the planner (read-only off) and the date is written back here.")
    n.font = Font(name=FONT, size=10, italic=True, color=MUTED)
    n.alignment = Alignment(vertical="top", wrap_text=True)
    ws.merge_cells(start_row=2, start_column=4, end_row=5, end_column=4)

wb.save(OUT)
print("written:", OUT)
