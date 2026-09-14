function doGet(e) {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('Deliverables Gantt Planner')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1.0')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function getSpreadsheet(sheetIdOrUrl) {
  if (sheetIdOrUrl && String(sheetIdOrUrl).trim() !== "") {
    var str = String(sheetIdOrUrl).trim();
    var match = str.match(/\/d\/([a-zA-Z0-9-_]+)/);
    var id = match ? match[1] : str;
    try {
      return SpreadsheetApp.openById(id);
    } catch (e) {
      throw new Error("Could not open sheet with ID '" + id + "'. Please check sharing permissions.");
    }
  }
  var activeSs = SpreadsheetApp.getActiveSpreadsheet();
  if (activeSs) return activeSs;
  throw new Error("No active Google Sheet found. Please connect a valid Sheet URL or ID.");
}

function getPlannerData(sheetIdOrUrl) {
  const ss = getSpreadsheet(sheetIdOrUrl);
  
  // 1. Fetch Stages Order from 'stages' sheet
  const stagesSheet = ss.getSheetByName("stages");
  const stages = [];
  if (stagesSheet && stagesSheet.getLastRow() >= 1) {
    const stageValues = stagesSheet.getRange(1, 1, stagesSheet.getLastRow(), 1).getValues();
    stageValues.forEach(row => {
      const val = String(row[0] || '').trim();
      if (val !== '' && !stages.includes(val)) {
        stages.push(val);
      }
    });
  }

  // 2. Fetch Deliverables from 'plan' sheet
  const planSheet = ss.getSheetByName("plan");
  if (!planSheet) throw new Error("Sheet 'plan' not found in spreadsheet '" + ss.getName() + "'!");
  const planLastRow = planSheet.getLastRow();
  if (planLastRow < 2) return { tasks: [], gates: [], yRows: [], stages: stages, units: [], sheetName: ss.getName(), sheetId: ss.getId() };

  const planLastCol = Math.max(12, planSheet.getLastColumn());
  const headerRow = planSheet.getRange(1, 1, 1, planLastCol).getValues()[0];
  let currencyColIdx = 10;
  let unitColIdx = 11;

  headerRow.forEach((h, idx) => {
    const colName = String(h || '').trim().toLowerCase();
    if (colName === 'currency' || colName === 'moneda' || colName === 'curr') {
      currencyColIdx = idx;
    }
    if (colName === 'unit' || colName === 'unidad' || colName === 'dept' || colName === 'department') {
      unitColIdx = idx;
    }
  });

  const fetchCols = Math.max(8, currencyColIdx + 1, unitColIdx + 1);
  const planData = planSheet.getRange(2, 1, planLastRow - 1, fetchCols).getValues();
  const validTasks = [];
  const yRows = [];
  const trackStageMap = {};
  const units = [];

  planData.forEach((row, index) => {
    const rowNum = index + 2;
    const title = row[1];
    const rawId = row[2] || row[0];
    const rawStage = row[3];
    const rawAmount = row[4];
    const startVal = row[5];
    const endVal = row[6];
    const comment = row[7];
    const rawCurrency = row[currencyColIdx] ? String(row[currencyColIdx]).trim() : '';
    const rawUnit = row[unitColIdx] ? String(row[unitColIdx]).trim() : '';
    const unit = rawUnit || 'Unassigned';

    if (!startVal || String(startVal).toUpperCase() === 'N/A' || !endVal || String(endVal).toUpperCase() === 'N/A') {
      return;
    }

    const startDate = parseDateVal(startVal);
    const endDate = parseDateVal(endVal);
    if (!startDate || !endDate) return;

    const trackId = String(rawId || ("Track_" + (index + 1))).trim();
    if (!yRows.includes(trackId)) {
      yRows.push(trackId);
    }

    const itemStage = rawStage ? String(rawStage).trim() : '';
    if (!trackStageMap[trackId]) {
      trackStageMap[trackId] = itemStage;
    }

    if (!units.includes(unit)) {
      units.push(unit);
    }

    let cleanTitle = String(title || '').replace(/\[|\]/g, "").trim();
    const numAmount = typeof rawAmount === 'number' ? rawAmount : (parseFloat(rawAmount) || 0);
    const isEuro = /^(euro|eur|€)$/i.test(rawCurrency);
    const currency = isEuro ? 'EUR' : 'MH';

    validTasks.push({
      rowNum: rowNum,
      id: 'task_' + rowNum + '_' + Math.random().toString(36).substr(2, 5),
      trackId: trackId,
      stage: itemStage,
      unit: unit,
      title: cleanTitle,
      amount: numAmount,
      currency: currency,
      mh: isEuro ? 0 : numAmount,
      start: formatDateISO(startDate),
      end: formatDateISO(endDate),
      comment: comment ? String(comment).trim() : ''
    });
  });

  validTasks.forEach(task => {
    if (trackStageMap[task.trackId]) {
      task.stage = trackStageMap[task.trackId];
    }
  });

  const extractGatesFromSheet = (sheetName, gateType, isHc) => {
    const sheet = ss.getSheetByName(sheetName);
    const list = [];
    if (sheet && sheet.getLastRow() >= 2) {
      const gData = sheet.getRange(2, 1, sheet.getLastRow() - 1, 2).getValues();
      gData.forEach((g, index) => {
        const rowNum = index + 2;
        const gName = g[0];
        const gDate = parseDateVal(g[1]);
        if (gName && gDate) {
          list.push({
            rowNum: rowNum,
            sheetName: sheetName,
            name: String(gName).trim(),
            date: formatDateISO(gDate),
            type: gateType,
            isHc: isHc
          });
        }
      });
    }
    return list;
  };

  const validGates = [
    ...extractGatesFromSheet("gates-system", "sys_review", false),
    ...extractGatesFromSheet("gates-hc", "hc_review", true),
    ...extractGatesFromSheet("mg-hc", "hc_maturity", true)
  ];

  return {
    tasks: validTasks,
    gates: validGates,
    yRows: yRows,
    stages: stages,
    units: units,
    trackStageMap: trackStageMap,
    sheetName: ss.getName(),
    sheetId: ss.getId()
  };
}

function shiftAllDates(deltaDays, sheetIdOrUrl) {
  if (!deltaDays || deltaDays === 0) return { success: true, count: 0, deltaDays: 0 };
  const ss = getSpreadsheet(sheetIdOrUrl);
  const msOffset = deltaDays * 86400000;
  let taskCount = 0;

  const planSheet = ss.getSheetByName("plan");
  if (planSheet && planSheet.getLastRow() >= 2) {
    const numRows = planSheet.getLastRow() - 1;
    const dateRange = planSheet.getRange(2, 6, numRows, 2);
    const dateValues = dateRange.getValues();
    for (let i = 0; i < dateValues.length; i++) {
      const sVal = dateValues[i][0];
      const eVal = dateValues[i][1];
      if (sVal && String(sVal).toUpperCase() !== 'N/A') {
        const sD = parseDateVal(sVal);
        if (sD) {
          dateValues[i][0] = formatDateISO(new Date(sD.getTime() + msOffset));
          taskCount++;
        }
      }
      if (eVal && String(eVal).toUpperCase() !== 'N/A') {
        const eD = parseDateVal(eVal);
        if (eD) {
          dateValues[i][1] = formatDateISO(new Date(eD.getTime() + msOffset));
        }
      }
    }
    dateRange.setValues(dateValues);
  }

  const gateSheets = ["gates-system", "gates-hc", "mg-hc"];
  gateSheets.forEach(name => {
    const gSheet = ss.getSheetByName(name);
    if (gSheet && gSheet.getLastRow() >= 2) {
      const numRows = gSheet.getLastRow() - 1;
      const gRange = gSheet.getRange(2, 2, numRows, 1);
      const gValues = gRange.getValues();
      for (let i = 0; i < gValues.length; i++) {
        const gD = parseDateVal(gValues[i][0]);
        if (gD) {
          gValues[i][0] = formatDateISO(new Date(gD.getTime() + msOffset));
        }
      }
      gRange.setValues(gValues);
    }
  });

  return { success: true, count: taskCount, deltaDays: deltaDays };
}

function updateGateDate(sheetName, rowNum, dateStr, sheetIdOrUrl) {
  const ss = getSpreadsheet(sheetIdOrUrl);
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) throw new Error("Sheet '" + sheetName + "' not found.");
  sheet.getRange(rowNum, 2).setValue(dateStr);
  return { success: true };
}

function updateTaskDetails(rowNum, title, trackId, stage, startStr, endStr, comment, sheetIdOrUrl) {
  const ss = getSpreadsheet(sheetIdOrUrl);
  const planSheet = ss.getSheetByName("plan");
  if (!planSheet) throw new Error("Sheet 'plan' not found.");
  if (title !== undefined) planSheet.getRange(rowNum, 2).setValue(title);
  if (trackId !== undefined) planSheet.getRange(rowNum, 3).setValue(trackId);
  if (stage !== undefined) planSheet.getRange(rowNum, 4).setValue(stage);
  if (startStr !== undefined) planSheet.getRange(rowNum, 6).setValue(startStr);
  if (endStr !== undefined) planSheet.getRange(rowNum, 7).setValue(endStr);
  if (comment !== undefined) planSheet.getRange(rowNum, 8).setValue(comment);
  return { success: true };
}

function updateTaskDates(rowNum, startStr, endStr, sheetIdOrUrl) {
  const ss = getSpreadsheet(sheetIdOrUrl);
  const planSheet = ss.getSheetByName("plan");
  if (!planSheet) throw new Error("Sheet 'plan' not found.");
  planSheet.getRange(rowNum, 6).setValue(startStr);
  planSheet.getRange(rowNum, 7).setValue(endStr);
  return { success: true };
}

function parseDateVal(val) {
  if (!val) return null;
  if (val instanceof Date) {
    return isNaN(val.getTime()) ? null : new Date(val.getFullYear(), val.getMonth(), val.getDate());
  }
  if (typeof val === 'number') {
    const d = new Date(val);
    return isNaN(d.getTime()) ? null : new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }
  if (typeof val === 'string' && val.trim() !== '') {
    const str = val.trim();
    if (str.toUpperCase() === 'N/A') return null;
    const parts = str.split(/[\/\-\.]/);
    if (parts.length === 3) {
      const p1 = parseInt(parts[0], 10);
      const p2 = parseInt(parts[1], 10) - 1;
      const p3 = parseInt(parts[2], 10);
      if (p1 > 1000) {
        const d = new Date(p1, p2, p3);
        if (!isNaN(d.getTime())) return d;
      } else {
        const d = new Date(p3, p2, p1);
        if (!isNaN(d.getTime())) return d;
      }
    }
    const d = new Date(str);
    if (!isNaN(d.getTime())) return new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }
  return null;
}

function formatDateISO(d) {
  if (!d || isNaN(d.getTime())) return '';
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return year + '-' + month + '-' + day;
}
