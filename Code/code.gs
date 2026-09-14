/**
 * Deliverables Gantt Planner — Google Apps Script backend.
 *
 * Data model (Google Sheet tabs):
 *   plan          Row 1 = headers, rows 2+ = deliverables.
 *                 Default layout: A=ref, B=title, C=track id, D=stage,
 *                 E=amount, F=start, G=end, H=comment, K=currency, L=unit.
 *                 Any of those can be relocated by naming the header cell
 *                 (see COLUMN_ALIASES below) — headers win over positions.
 *   stages        Column A = ordered stage names (no header row).
 *   gates-system  Row 1 = headers, A=gate name, B=date.
 *   gates-hc      Same shape as gates-system.
 *   mg-hc         Same shape as gates-system.
 *
 * Every public function accepts an optional trailing `sheetIdOrUrl`, so the
 * web app can drive any spreadsheet the user has access to, not just the
 * container-bound one.
 */

var SHEET_NAMES = {
  PLAN: 'plan',
  STAGES: 'stages',
  GATES_SYSTEM: 'gates-system',
  GATES_HC: 'gates-hc',
  MG_HC: 'mg-hc'
};

/** Gate tabs, in render order, with the type/flag the UI expects. */
var GATE_SOURCES = [
  { sheet: SHEET_NAMES.GATES_SYSTEM, type: 'sys_review', isHc: false },
  { sheet: SHEET_NAMES.GATES_HC, type: 'hc_review', isHc: true },
  { sheet: SHEET_NAMES.MG_HC, type: 'hc_maturity', isHc: true }
];

/** Zero-based fallback positions in the `plan` sheet. */
var PLAN_DEFAULT_COLS = {
  ref: 0,
  title: 1,
  trackId: 2,
  stage: 3,
  amount: 4,
  start: 5,
  end: 6,
  comment: 7,
  currency: 10,
  unit: 11
};

/** Header labels (lowercase) that relocate a column. */
var COLUMN_ALIASES = {
  title: ['title', 'deliverable', 'titre', 'livrable', 'name', 'nom'],
  trackId: ['track', 'track id', 'trackid', 'id', 'ref', 'reference'],
  stage: ['stage', 'phase', 'etape', 'étape', 'section'],
  amount: ['amount', 'mh', 'effort', 'montant', 'charge', 'quantity', 'qty'],
  start: ['start', 'start date', 'debut', 'début', 'date debut', 'date début'],
  end: ['end', 'end date', 'fin', 'date fin', 'finish'],
  comment: ['comment', 'comments', 'commentaire', 'note', 'notes', 'remark'],
  currency: ['currency', 'moneda', 'curr', 'devise', 'unite monetaire'],
  unit: ['unit', 'unidad', 'unite', 'unité', 'dept', 'department', 'departement', 'département', 'service', 'equipe', 'équipe', 'team']
};

var MS_PER_DAY = 24 * 60 * 60 * 1000;
/** Sheets store dates as days since 1899-12-30. */
var SHEETS_EPOCH_UTC = Date.UTC(1899, 11, 30);

/* ------------------------------------------------------------------ */
/* Web app entry point                                                 */
/* ------------------------------------------------------------------ */

function doGet(e) {
  return createIndexOutput_()
    .setTitle('Deliverables Gantt Planner')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1.0')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * The HTML file may be named `index`, `Index` or `INDEX` depending on how the
 * project was created; `createHtmlOutputFromFile` is case sensitive, so try
 * each spelling instead of hard-failing on one.
 */
function createIndexOutput_() {
  var candidates = ['index', 'Index', 'INDEX'];
  var lastErr = null;
  for (var i = 0; i < candidates.length; i++) {
    try {
      return HtmlService.createHtmlOutputFromFile(candidates[i]);
    } catch (err) {
      lastErr = err;
    }
  }
  throw new Error('HTML file "index" not found in this Apps Script project. ' +
    (lastErr ? String(lastErr) : ''));
}

/* ------------------------------------------------------------------ */
/* Spreadsheet access                                                  */
/* ------------------------------------------------------------------ */

function getSpreadsheet(sheetIdOrUrl) {
  var raw = sheetIdOrUrl === null || sheetIdOrUrl === undefined ? '' : String(sheetIdOrUrl).trim();
  if (raw !== '') {
    var id = extractSpreadsheetId_(raw);
    try {
      return SpreadsheetApp.openById(id);
    } catch (err) {
      throw new Error('Could not open the spreadsheet with ID "' + id + '". ' +
        'Check that the ID is correct and that this account has at least view access.');
    }
  }
  var activeSs = SpreadsheetApp.getActiveSpreadsheet();
  if (activeSs) return activeSs;
  throw new Error('No active Google Sheet found. Connect a Sheet URL or ID first.');
}

/** Accepts a full edit URL, a `/d/<id>/` fragment or a bare ID. */
function extractSpreadsheetId_(str) {
  var match = String(str).match(/\/d\/([a-zA-Z0-9-_]+)/);
  if (match) return match[1];
  match = String(str).match(/[?&]id=([a-zA-Z0-9-_]+)/);
  if (match) return match[1];
  return String(str).replace(/^\s+|\s+$/g, '');
}

/**
 * Reads a rectangular block without ever running past the sheet's real
 * bounds — `getRange` throws when asked for columns the sheet does not have.
 */
function readBlock_(sheet, startRow, startCol, numRows, numCols) {
  if (!sheet) return [];
  var maxRows = sheet.getMaxRows();
  var maxCols = sheet.getMaxColumns();
  if (startRow > maxRows || startCol > maxCols) return [];
  var rows = Math.min(numRows, maxRows - startRow + 1);
  var cols = Math.min(numCols, maxCols - startCol + 1);
  if (rows <= 0 || cols <= 0) return [];
  return sheet.getRange(startRow, startCol, rows, cols).getValues();
}

/* ------------------------------------------------------------------ */
/* Column resolution                                                   */
/* ------------------------------------------------------------------ */

/**
 * Resolves the zero-based index of every logical plan column, starting from
 * the default layout and letting recognised header labels override it.
 */
function resolvePlanColumns_(planSheet) {
  var cols = {};
  for (var key in PLAN_DEFAULT_COLS) {
    if (PLAN_DEFAULT_COLS.hasOwnProperty(key)) cols[key] = PLAN_DEFAULT_COLS[key];
  }
  var headerRow = readBlock_(planSheet, 1, 1, 1, planSheet.getMaxColumns());
  if (!headerRow.length) return cols;

  headerRow[0].forEach(function (cell, idx) {
    var label = normalizeLabel_(cell);
    if (label === '') return;
    for (var key in COLUMN_ALIASES) {
      if (!COLUMN_ALIASES.hasOwnProperty(key)) continue;
      if (COLUMN_ALIASES[key].indexOf(label) !== -1) {
        cols[key] = idx;
        return;
      }
    }
  });
  return cols;
}

function normalizeLabel_(value) {
  return String(value === null || value === undefined ? '' : value)
    .replace(/^\s+|\s+$/g, '')
    .toLowerCase();
}

/* ------------------------------------------------------------------ */
/* Reading                                                             */
/* ------------------------------------------------------------------ */

/**
 * Single round trip that returns everything the planner UI needs: tasks,
 * gates, track order, stage order and the list of units.
 */
function getPlannerData(sheetIdOrUrl) {
  var ss = getSpreadsheet(sheetIdOrUrl);
  var stages = readStages_(ss);
  var planSheet = ss.getSheetByName(SHEET_NAMES.PLAN);

  if (!planSheet) {
    throw new Error('Sheet "' + SHEET_NAMES.PLAN + '" not found in "' + ss.getName() +
      '". Rename your deliverables tab to "plan" (all lowercase).');
  }

  var emptyResult = {
    tasks: [],
    gates: readGates_(ss),
    yRows: [],
    stages: stages,
    units: [],
    trackStageMap: {},
    skippedRows: 0,
    sheetName: ss.getName(),
    sheetId: ss.getId()
  };

  var planLastRow = planSheet.getLastRow();
  if (planLastRow < 2) return emptyResult;

  var cols = resolvePlanColumns_(planSheet);
  var neededCols = 1;
  for (var key in cols) {
    if (cols.hasOwnProperty(key)) neededCols = Math.max(neededCols, cols[key] + 1);
  }

  var planData = readBlock_(planSheet, 2, 1, planLastRow - 1, neededCols);
  var tasks = [];
  var yRows = [];
  var units = [];
  var trackStageMap = {};
  var skippedRows = 0;

  planData.forEach(function (row, index) {
    var rowNum = index + 2;
    var startVal = pick_(row, cols.start);
    var endVal = pick_(row, cols.end);

    if (isBlankOrNA_(startVal) || isBlankOrNA_(endVal)) {
      if (!isRowEmpty_(row)) skippedRows++;
      return;
    }

    var startDate = parseDateVal(startVal);
    var endDate = parseDateVal(endVal);
    if (!startDate || !endDate) {
      skippedRows++;
      return;
    }
    // A backwards range is a data-entry slip, not a reason to drop the row.
    if (endDate.getTime() < startDate.getTime()) {
      var swap = startDate;
      startDate = endDate;
      endDate = swap;
    }

    var rawId = pick_(row, cols.trackId) || pick_(row, cols.ref);
    var trackId = String(rawId === null || rawId === undefined || rawId === ''
      ? 'Track_' + (index + 1)
      : rawId).replace(/^\s+|\s+$/g, '');
    if (yRows.indexOf(trackId) === -1) yRows.push(trackId);

    var itemStage = cleanString_(pick_(row, cols.stage));
    // The first row of a track defines the stage for the whole track.
    if (!trackStageMap[trackId] && itemStage !== '') trackStageMap[trackId] = itemStage;

    var unit = cleanString_(pick_(row, cols.unit)) || 'Unassigned';
    if (units.indexOf(unit) === -1) units.push(unit);

    var rawAmount = pick_(row, cols.amount);
    var numAmount = toNumber_(rawAmount);
    var isEuro = isEuroCurrency_(pick_(row, cols.currency));

    tasks.push({
      rowNum: rowNum,
      id: 'task_' + rowNum,
      trackId: trackId,
      stage: itemStage,
      unit: unit,
      title: cleanString_(pick_(row, cols.title)).replace(/[\[\]]/g, ''),
      amount: numAmount,
      currency: isEuro ? 'EUR' : 'MH',
      mh: isEuro ? 0 : numAmount,
      start: formatDateISO(startDate),
      end: formatDateISO(endDate),
      comment: cleanString_(pick_(row, cols.comment))
    });
  });

  // Normalise every task of a track onto that track's stage.
  tasks.forEach(function (task) {
    if (trackStageMap[task.trackId]) task.stage = trackStageMap[task.trackId];
  });

  units.sort(function (a, b) {
    if (a === 'Unassigned') return 1;
    if (b === 'Unassigned') return -1;
    return a.localeCompare(b);
  });

  return {
    tasks: tasks,
    gates: readGates_(ss),
    yRows: yRows,
    stages: stages,
    units: units,
    trackStageMap: trackStageMap,
    skippedRows: skippedRows,
    sheetName: ss.getName(),
    sheetId: ss.getId()
  };
}

function readStages_(ss) {
  var stagesSheet = ss.getSheetByName(SHEET_NAMES.STAGES);
  var stages = [];
  if (!stagesSheet || stagesSheet.getLastRow() < 1) return stages;
  var values = readBlock_(stagesSheet, 1, 1, stagesSheet.getLastRow(), 1);
  values.forEach(function (row) {
    var val = cleanString_(row[0]);
    if (val !== '' && stages.indexOf(val) === -1) stages.push(val);
  });
  return stages;
}

function readGates_(ss) {
  var gates = [];
  GATE_SOURCES.forEach(function (source) {
    var sheet = ss.getSheetByName(source.sheet);
    if (!sheet || sheet.getLastRow() < 2) return;
    var values = readBlock_(sheet, 2, 1, sheet.getLastRow() - 1, 2);
    values.forEach(function (row, index) {
      var name = cleanString_(row[0]);
      var date = parseDateVal(row[1]);
      if (name === '' || !date) return;
      gates.push({
        rowNum: index + 2,
        sheetName: source.sheet,
        name: name,
        date: formatDateISO(date),
        type: source.type,
        isHc: source.isHc
      });
    });
  });
  return gates;
}

/* ------------------------------------------------------------------ */
/* Writing                                                             */
/* ------------------------------------------------------------------ */

/**
 * Moves every task and gate date by `deltaDays`. Reads and writes each tab in
 * a single batched range so a large plan stays within the execution quota.
 */
function shiftAllDates(deltaDays, sheetIdOrUrl) {
  var delta = Math.round(toNumber_(deltaDays));
  if (!delta) return { success: true, count: 0, gateCount: 0, deltaDays: 0 };

  var ss = getSpreadsheet(sheetIdOrUrl);
  var taskCount = 0;
  var gateCount = 0;

  var planSheet = ss.getSheetByName(SHEET_NAMES.PLAN);
  if (planSheet && planSheet.getLastRow() >= 2) {
    var cols = resolvePlanColumns_(planSheet);
    var startCol = Math.min(cols.start, cols.end) + 1;
    var endCol = Math.max(cols.start, cols.end) + 1;
    var width = endCol - startCol + 1;
    var numRows = planSheet.getLastRow() - 1;
    var maxCols = planSheet.getMaxColumns();

    if (startCol <= maxCols) {
      width = Math.min(width, maxCols - startCol + 1);
      var range = planSheet.getRange(2, startCol, numRows, width);
      var values = range.getValues();
      var startIdx = cols.start + 1 - startCol;
      var endIdx = cols.end + 1 - startCol;

      for (var i = 0; i < values.length; i++) {
        var shiftedStart = shiftCell_(values[i], startIdx, delta);
        var shiftedEnd = shiftCell_(values[i], endIdx, delta);
        if (shiftedStart || shiftedEnd) taskCount++;
      }
      range.setValues(values);
    }
  }

  GATE_SOURCES.forEach(function (source) {
    var sheet = ss.getSheetByName(source.sheet);
    if (!sheet || sheet.getLastRow() < 2 || sheet.getMaxColumns() < 2) return;
    var range = sheet.getRange(2, 2, sheet.getLastRow() - 1, 1);
    var values = range.getValues();
    for (var i = 0; i < values.length; i++) {
      if (shiftCell_(values[i], 0, delta)) gateCount++;
    }
    range.setValues(values);
  });

  SpreadsheetApp.flush();
  return { success: true, count: taskCount, gateCount: gateCount, deltaDays: delta };
}

/** Shifts one cell of a row array in place. Returns true when it moved. */
function shiftCell_(rowArr, idx, deltaDays) {
  if (idx < 0 || idx >= rowArr.length) return false;
  var value = rowArr[idx];
  if (isBlankOrNA_(value)) return false;
  var parsed = parseDateVal(value);
  if (!parsed) return false;
  rowArr[idx] = addDays_(parsed, deltaDays);
  return true;
}

function updateGateDate(sheetName, rowNum, dateStr, sheetIdOrUrl) {
  var ss = getSpreadsheet(sheetIdOrUrl);
  var name = String(sheetName || SHEET_NAMES.GATES_SYSTEM);
  var sheet = ss.getSheetByName(name);
  if (!sheet) throw new Error('Sheet "' + name + '" not found.');

  var row = Math.round(toNumber_(rowNum));
  if (!(row >= 2)) throw new Error('Invalid gate row number: ' + rowNum);
  if (row > sheet.getMaxRows()) throw new Error('Gate row ' + row + ' is past the end of "' + name + '".');

  sheet.getRange(row, 2).setValue(coerceDateForCell_(dateStr));
  return { success: true, sheetName: name, rowNum: row };
}

/**
 * Updates the editable fields of one deliverable. `undefined` fields are left
 * untouched, so the UI can send a partial patch.
 */
function updateTaskDetails(rowNum, title, trackId, stage, startStr, endStr, comment, sheetIdOrUrl) {
  var ss = getSpreadsheet(sheetIdOrUrl);
  var planSheet = requirePlanSheet_(ss);
  var row = requirePlanRow_(planSheet, rowNum);
  var cols = resolvePlanColumns_(planSheet);

  var writes = [
    { idx: cols.title, value: title, isDate: false },
    { idx: cols.trackId, value: trackId, isDate: false },
    { idx: cols.stage, value: stage, isDate: false },
    { idx: cols.start, value: startStr, isDate: true },
    { idx: cols.end, value: endStr, isDate: true },
    { idx: cols.comment, value: comment, isDate: false }
  ];

  writes.forEach(function (w) {
    if (w.value === undefined || w.value === null) return;
    if (w.idx + 1 > planSheet.getMaxColumns()) return;
    planSheet.getRange(row, w.idx + 1).setValue(w.isDate ? coerceDateForCell_(w.value) : w.value);
  });

  SpreadsheetApp.flush();
  return { success: true, rowNum: row };
}

function updateTaskDates(rowNum, startStr, endStr, sheetIdOrUrl) {
  var ss = getSpreadsheet(sheetIdOrUrl);
  var planSheet = requirePlanSheet_(ss);
  var row = requirePlanRow_(planSheet, rowNum);
  var cols = resolvePlanColumns_(planSheet);
  var maxCols = planSheet.getMaxColumns();

  if (cols.start + 1 <= maxCols) {
    planSheet.getRange(row, cols.start + 1).setValue(coerceDateForCell_(startStr));
  }
  if (cols.end + 1 <= maxCols) {
    planSheet.getRange(row, cols.end + 1).setValue(coerceDateForCell_(endStr));
  }

  SpreadsheetApp.flush();
  return { success: true, rowNum: row };
}

function requirePlanSheet_(ss) {
  var planSheet = ss.getSheetByName(SHEET_NAMES.PLAN);
  if (!planSheet) throw new Error('Sheet "' + SHEET_NAMES.PLAN + '" not found.');
  return planSheet;
}

function requirePlanRow_(planSheet, rowNum) {
  var row = Math.round(toNumber_(rowNum));
  if (!(row >= 2)) throw new Error('Invalid plan row number: ' + rowNum);
  if (row > planSheet.getMaxRows()) throw new Error('Plan row ' + row + ' is past the end of the sheet.');
  return row;
}

/**
 * Writes real Date values rather than text, so the cell keeps its number
 * format and reads back as a Date. Unparseable input is written verbatim.
 */
function coerceDateForCell_(value) {
  var parsed = parseDateVal(value);
  return parsed ? parsed : value;
}

/* ------------------------------------------------------------------ */
/* Date & value helpers                                                */
/* ------------------------------------------------------------------ */

/**
 * Accepts Date objects, spreadsheet serial numbers, ISO strings and
 * day/month/year or month/day/year text. Always returns a local-midnight Date
 * (or null), so day arithmetic never drifts across DST.
 */
function parseDateVal(val) {
  if (val === null || val === undefined || val === '') return null;

  if (val instanceof Date) {
    return isNaN(val.getTime()) ? null : atMidnight_(val);
  }

  if (typeof val === 'number') {
    if (!isFinite(val)) return null;
    // Small numbers are spreadsheet serials; very large ones are ms epochs.
    if (Math.abs(val) < 400000) {
      var serial = new Date(SHEETS_EPOCH_UTC + Math.round(val) * MS_PER_DAY);
      return isNaN(serial.getTime())
        ? null
        : new Date(serial.getUTCFullYear(), serial.getUTCMonth(), serial.getUTCDate());
    }
    var fromMs = new Date(val);
    return isNaN(fromMs.getTime()) ? null : atMidnight_(fromMs);
  }

  if (typeof val === 'string') {
    var str = val.replace(/^\s+|\s+$/g, '');
    if (str === '' || str.toUpperCase() === 'N/A') return null;

    var iso = str.match(/^(\d{4})[-\/.](\d{1,2})[-\/.](\d{1,2})/);
    if (iso) return makeDate_(+iso[1], +iso[2] - 1, +iso[3]);

    var parts = str.split(/[\/\-.]/);
    if (parts.length === 3) {
      var p1 = parseInt(parts[0], 10);
      var p2 = parseInt(parts[1], 10);
      var p3 = parseInt(parts[2], 10);
      if (!isNaN(p1) && !isNaN(p2) && !isNaN(p3)) {
        // Day-first unless the first field cannot be a day.
        if (p1 > 12 || p2 <= 12) return makeDate_(expandYear_(p3), p2 - 1, p1);
        return makeDate_(expandYear_(p3), p1 - 1, p2);
      }
    }

    var loose = new Date(str);
    if (!isNaN(loose.getTime())) return atMidnight_(loose);
  }

  return null;
}

function makeDate_(year, monthIdx, day) {
  var d = new Date(year, monthIdx, day);
  if (isNaN(d.getTime())) return null;
  // Reject overflow such as 31/02 silently rolling into March.
  if (d.getFullYear() !== year || d.getMonth() !== monthIdx || d.getDate() !== day) return null;
  return d;
}

function expandYear_(year) {
  if (year >= 100) return year;
  return year < 70 ? 2000 + year : 1900 + year;
}

function atMidnight_(d) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function addDays_(d, days) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() + days);
}

function formatDateISO(d) {
  if (!d || !(d instanceof Date) || isNaN(d.getTime())) return '';
  var year = d.getFullYear();
  var month = String(d.getMonth() + 1);
  var day = String(d.getDate());
  if (month.length < 2) month = '0' + month;
  if (day.length < 2) day = '0' + day;
  return year + '-' + month + '-' + day;
}

function isBlankOrNA_(value) {
  if (value === null || value === undefined) return true;
  if (value instanceof Date) return false;
  var str = String(value).replace(/^\s+|\s+$/g, '');
  return str === '' || str.toUpperCase() === 'N/A' || str === '-';
}

function isRowEmpty_(row) {
  for (var i = 0; i < row.length; i++) {
    if (row[i] !== '' && row[i] !== null && row[i] !== undefined) return false;
  }
  return true;
}

function pick_(row, idx) {
  return (idx >= 0 && idx < row.length) ? row[idx] : '';
}

function cleanString_(value) {
  if (value === null || value === undefined) return '';
  if (value instanceof Date) return formatDateISO(value);
  return String(value).replace(/^\s+|\s+$/g, '');
}

function toNumber_(value) {
  if (typeof value === 'number') return isFinite(value) ? value : 0;
  if (value === null || value === undefined) return 0;
  // Tolerate "1 234,50", "1,234.50" and "€ 1234".
  var str = String(value).replace(/[^\d.,\-]/g, '').replace(/\s/g, '');
  if (str === '') return 0;
  if (str.indexOf(',') !== -1 && str.indexOf('.') !== -1) {
    str = str.lastIndexOf(',') > str.lastIndexOf('.')
      ? str.replace(/\./g, '').replace(',', '.')
      : str.replace(/,/g, '');
  } else if (str.indexOf(',') !== -1) {
    str = str.replace(',', '.');
  }
  var num = parseFloat(str);
  return isNaN(num) ? 0 : num;
}

function isEuroCurrency_(value) {
  return /^(euro|euros|eur|€)$/i.test(cleanString_(value));
}
