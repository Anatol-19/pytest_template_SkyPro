/**
 * @file 01_Utilities.gs.js
 * @description Чистые утилиты без доменной логики.
 *
 * Содержит:
 *  - Парсинг и нормализация (toText, parseNumber, normalizeHeader, normalizeTiming)
 *  - Нормализация доменных значений (normalizeProject, normalizeEnvironment, normalizeSource)
 *  - Форматирование для отображения (formatMetricValue, formatPercent)
 *  - Математические функции (averageNumbers, computeStdDev, computeStabilityScore)
 *  - Sheet I/O (readSheetRecords, getOrCreateSheet, writeHelperSheet)
 *  - Коллекции и хелперы (uniqueNonEmptyValues_, summarizeList_, hasTagToken_)
 */



function toText(value) {
  if (value === null || value === undefined) {
    return '';
  }
  return value.toString();
}

function parseNumber(value) {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  if (typeof value === 'number') {
    return value;
  }
  const cleaned = value.toString().trim().replace(',', '.').replace(/[^\d.\-]/g, '');
  if (!cleaned) {
    return null;
  }
  const parsed = parseFloat(cleaned);
  return Number.isFinite(parsed) ? parsed : null;
}

function normalizeHeader(value) {
  if (value === null || value === undefined) {
    return '';
  }
  return value.toString().trim().toLowerCase().replace(/\s+/g, '_').replace(/[^\w_]/g, '');
}

function getRecordValue(record, candidates) {
  for (const candidate of candidates) {
    const normalized = normalizeHeader(candidate);
    if (!normalized) {
      continue;
    }
    if (normalized in record) {
      const value = record[normalized];
      if (value === '' || value === null || value === undefined) {
        continue;
      }
      return value;
    }
  }
  return null;
}

function normalizeTiming(value, key) {
  const num = parseNumber(value);
  if (num === null) {
    return null;
  }
  if (num > 0 && num < 50 && isTimeMetric(key)) {
    return num * 1000;
  }
  return num;
}

function isTimeMetric(key) {
  if (!key) {
    return false;
  }
  const lower = key.toLowerCase();
  return TIME_METRIC_KEYS.some(metric => lower.includes(metric));
}

function normalizeProject(value) {
  const text = toText(value).toUpperCase();
  if (text.startsWith('VRP')) {
    return 'VRP';
  }
  if (text.startsWith('VRS')) {
    return 'VRS';
  }
  return text;
}

function normalizeEnvironment(value) {
  const text = toText(value).toUpperCase();
  if (!text) {
    return '';
  }
  if (text.includes('PROD')) return 'PROD';
  if (text.includes('STAGE')) return 'STAGE';
  if (text.includes('TEST')) return 'TEST';
  if (text.includes('DEV')) return 'DEV';
  return text;
}

function normalizeSource(value) {
  const text = toText(value).toUpperCase();
  if (!text) {
    return '';
  }
  if (text.includes('CRUX')) return 'CRUX';
  if (text.includes('API')) return 'API';
  if (text.includes('CLI')) return 'CLI';
  return text;
}

function inferProject(environment) {
  const text = toText(environment).toUpperCase();
  if (text.startsWith('VRP')) return 'VRP';
  if (text.startsWith('VRS')) return 'VRS';
  return '';
}

function matchesProject(value, project) {
  return normalizeProject(value) === normalizeProject(project);
}

function formatMetricValue(key, value) {
  if (value === null || value === undefined) {
    return '—';
  }
  if (normalizeHeader(key) === 'cls') {
    return value.toFixed(3);
  }
  if (isTimeMetric(key)) {
    if (value >= 1000) {
      return `${(value / 1000).toFixed(2)} s`;
    }
    return `${Math.round(value)} ms`;
  }
  return value.toString();
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—';
  }
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
}

function averageNumbers(values, decimals) {
  const nums = values.map(parseNumber).filter(value => value !== null);
  if (!nums.length) {
    return '';
  }
  const avg = nums.reduce((sum, value) => sum + value, 0) / nums.length;
  return decimals > 0 ? parseFloat(avg.toFixed(decimals)) : Math.round(avg);
}

function computeStdDev(values, decimals) {
  const nums = values.map(parseNumber).filter(value => value !== null);
  if (nums.length < 2) {
    return 0;
  }
  const mean = nums.reduce((sum, value) => sum + value, 0) / nums.length;
  const variance = nums.reduce((sum, value) => sum + Math.pow(value - mean, 2), 0) / nums.length;
  const std = Math.sqrt(variance);
  return decimals > 0 ? parseFloat(std.toFixed(decimals)) : Math.round(std);
}

function computeStabilityScore(lcpStd, inpStd, clsStd) {
  const lcpPenalty = Math.min((parseNumber(lcpStd) || 0) / 100, 40);
  const inpPenalty = Math.min((parseNumber(inpStd) || 0) / 20, 30);
  const clsPenalty = Math.min((parseNumber(clsStd) || 0) * 100, 30);
  const score = 100 - lcpPenalty - inpPenalty - clsPenalty;
  return Math.max(0, Math.min(100, Math.round(score)));
}

function isHeaderRow_(record) {
  // Если значения нескольких ключевых полей буквально совпадают с названиями заголовков —
  // это строка-заголовок, попавшая в данные из-за мульти-строчной шапки
  const checks = ['run_id', 'date', 'page', 'project'];
  let headerHits = 0;
  for (const key of checks) {
    const val = record[key];
    if (val && HEADER_TOKENS_.has(normalizeHeader(val))) {
      headerHits++;
    }
  }
  return headerHits >= 2;
}

function readSheetRecords(sheet) {
  if (!sheet) {
    return [];
  }
  const values = sheet.getDataRange().getValues();
  if (values.length < 2) {
    return [];
  }
  const headers = values[0].map(normalizeHeader);
  const records = [];
  for (let i = 1; i < values.length; i++) {
    const row = values[i];
    if (!row || row.every(cell => cell === '' || cell === null || cell === undefined)) {
      continue;
    }
    const record = {};
    headers.forEach((key, columnIndex) => {
      if (key) {
        record[key] = row[columnIndex];
      }
    });
    if (isHeaderRow_(record)) {
      continue;
    }
    records.push(record);
  }
  return records;
}

function getOrCreateSheet(ss, name) {
  let sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
  }
  return sheet;
}

function writeHelperSheet(sheet, headers, rows) {
  sheet.clearContents();
  const output = [headers].concat(rows || []);
  sheet.getRange(1, 1, output.length, headers.length).setValues(output);
}

function findHeaderIndex(headers, candidates) {
  for (const candidate of candidates) {
    const index = headers.indexOf(normalizeHeader(candidate));
    if (index !== -1) {
      return index;
    }
  }
  return -1;
}

function autoSizeColumns(sheet) {
  DASHBOARD_COLUMN_WIDTHS.forEach((width, index) => sheet.setColumnWidth(index + 1, width));
  const extraCols = 5;
  for (let i = DASHBOARD_COLUMN_WIDTHS.length + 1; i <= DASHBOARD_COLUMN_WIDTHS.length + extraCols; i++) {
    sheet.setColumnWidth(i, 120);
  }
  sheet.getRange(1, 1, 1, DASHBOARD_COLUMN_WIDTHS.length).setWrap(true);
}

function uniqueNonEmptyValues_(values) {
  return Array.from(new Set(values.map(toText).map(item => item.trim()).filter(Boolean)));
}

function summarizeList_(values, limit = 6) {
  const items = uniqueNonEmptyValues_(values);
  if (!items.length) {
    return '—';
  }
  if (items.length <= limit) {
    return items.join(', ');
  }
  return `${items.slice(0, limit).join(', ')} +${items.length - limit}`;
}

function hasTagToken_(tag, token) {
  if (!tag) return false;
  return toText(tag).toLowerCase().split(/[,;\s]+/).some(t => t.trim() === token.toLowerCase());
}