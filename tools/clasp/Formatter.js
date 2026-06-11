const PerfFormatter = (() => {
  const PERF_SHEETS = [
    'VRP [PROD]', 'VRP [STAGE]', 'VRP [TEST]', 'VRP [DEV]',
    'VRS [PROD]', 'VRS [STAGE]', 'VRS [TEST]', 'VRS [DEV]'
  ];
  const CRUX_SHEET = 'CrUX';
  const FORMATTER_CONFIG_SHEET = 'Config';
  const FORMATTER_SHEET_ID_KEYS = ['GS_SHEET_ID', 'SHEET_ID'];
  const WIDTHS = [
    100, 85, 145, 90,
    50,
    60, 55, 55,
    60, 55, 55,
    60, 60, 85, 70, 70,
    115, 145
  ];
  const STATUS_COLORS = {
    GOOD: '#C8E6C9',
    NI: '#FFF9C4',
    POOR: '#FFCDD2'
  };
  const PERF_HEADERS = [
    'date', 'run_id', 'tag', 'type', 'page', 'device',
    'P', 'LCP', 'INP', 'CLS', 'LCP_p90', 'INP_p90', 'CLS_p90',
    'TBT', 'FCP', 'SI', 'TTI', 'TTFB'
  ];
  const CRUX_HEADERS = [
    'date', 'project', 'sprint', 'page', 'device',
    'LCP', 'FCP', 'INP', 'CLS',
    'LCP_good_pct', 'FCP_good_pct', 'INP_good_pct', 'CLS_good_pct',
    'TTFB', 'run_id', 'tag'
  ];
  // DEFAULT_METRIC_FALLBACKS определяется в 00_Constants.gs (единый источник истины)

  function getSpreadsheet() {
    const active = SpreadsheetApp.getActiveSpreadsheet();
    if (active) {
      return active;
    }
    const spreadsheetId = getConfiguredSpreadsheetId();
    if (!spreadsheetId) {
      throw new Error('Не удалось получить Spreadsheet для форматирования. Установите GS_SHEET_ID или SHEET_ID.');
    }
    return SpreadsheetApp.openById(spreadsheetId);
  }

  function getConfiguredSpreadsheetId() {
    const scriptProps = PropertiesService.getScriptProperties();
    for (const key of FORMATTER_SHEET_ID_KEYS) {
      const value = scriptProps.getProperty(key);
      if (value) {
        return value;
      }
    }
    const docProps = PropertiesService.getDocumentProperties();
    for (const key of FORMATTER_SHEET_ID_KEYS) {
      const value = docProps.getProperty(key);
      if (value) {
        return value;
      }
    }
    return null;
  }

  function applyVisualFormattingInternal(spreadsheet) {
    const ss = spreadsheet || getSpreadsheet();
    if (!ss) {
      return;
    }
    applyVisualStyleToSheet(ss.getSheetByName(CRUX_SHEET));
    PERF_SHEETS.forEach(name => {
      applyVisualStyleToSheet(ss.getSheetByName(name));
    });
  }

  function applyVisualStyleToSheet(sheet) {
    if (!sheet) {
      return;
    }
    const headerRow = findHeaderRow(sheet);
    const dataStartRow = Math.max(headerRow + 1, 2);
    applyColumnWidths(sheet);
    styleDataRange(sheet, dataStartRow);
    applyConditionalFormattingToSheet(sheet, headerRow, dataStartRow);
  }

  function setupPerfSheetsInternal() {
    const ss = getSpreadsheet();
    ensureSheetStructure(ss, CRUX_SHEET, CRUX_HEADERS);
    PERF_SHEETS.forEach(name => ensureSheetStructure(ss, name, PERF_HEADERS));
  }

  function formatAllPerfSheetsInternal(spreadsheet) {
    applyVisualFormattingInternal(spreadsheet);
  }

  function ensureSheetStructure(ss, sheetName, headers) {
    let sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      sheet = ss.insertSheet(sheetName);
    }
    const currentHeaders = sheet.getRange(1, 1, 1, Math.max(headers.length, 1)).getValues()[0] || [];
    const hasHeader = currentHeaders.some(cell => cell !== '' && cell !== null && cell !== undefined);
    if (!hasHeader) {
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    }
    if (sheet.getFrozenRows() < 1) {
      sheet.setFrozenRows(1);
    }
  }

  function findHeaderRow(sheet) {
    const lastRow = Math.max(sheet.getLastRow(), 1);
    const candidates = Math.min(lastRow, 5);
    for (let row = 1; row <= candidates; row++) {
      const values = sheet.getRange(row, 1, 1, Math.max(sheet.getLastColumn(), 1)).getValues()[0] || [];
      if (values.some(value => typeof value === 'string' && /(date|type|page|device)/i.test(value))) {
        return row;
      }
    }
    return 1;
  }

  function applyColumnWidths(sheet) {
    const maxCols = Math.max(sheet.getMaxColumns(), WIDTHS.length);
    WIDTHS.forEach((width, index) => sheet.setColumnWidth(index + 1, width));
    for (let col = WIDTHS.length + 1; col <= maxCols; col++) {
      sheet.setColumnWidth(col, 140);
    }
  }

  function styleDataRange(sheet, dataStartRow) {
    const lastCol = Math.max(sheet.getMaxColumns(), WIDTHS.length);
    const totalRows = Math.max(sheet.getMaxRows() - dataStartRow + 1, 1);
    if (lastCol <= 0 || totalRows <= 0) {
      return;
    }
    const dataRange = sheet.getRange(dataStartRow, 1, totalRows, lastCol);
    dataRange.setHorizontalAlignment('center');
  }

  function applyConditionalFormattingToSheet(sheet, headerRowIndex, dataStartRow) {
    if (!sheet) {
      return;
    }
    const thresholds = loadFormatterMetricThresholds();
    if (!thresholds.length) {
      return;
    }
    const lastCol = Math.max(sheet.getMaxColumns(), 1);
    const headerValues = sheet.getRange(headerRowIndex, 1, 1, lastCol).getValues()[0] || [];
    const headerMap = {};
    headerValues.forEach((cell, index) => {
      if (!cell) {
        return;
      }
      headerMap[normalizeHeader(cell)] = index + 1;
    });
    const totalRows = Math.max(sheet.getMaxRows() - dataStartRow + 1, 1);
    const metricColumns = new Set();
    thresholds.forEach(metricRule => {
      findMetricColumns(metricRule.metric, headerMap).forEach(column => metricColumns.add(column));
    });
    const rules = [];
    thresholds.forEach(metricRule => {
      const columns = findMetricColumns(metricRule.metric, headerMap);
      columns.forEach(column => {
        const range = sheet.getRange(dataStartRow, column, totalRows, 1);
        buildMetricFormatting(range, metricRule, rules);
      });
    });
    sheet.setConditionalFormatRules(rules);
  }

  function buildMetricFormatting(range, metricRule, rules) {
    const { direction, good, poor } = metricRule;
    const neutralColor = STATUS_COLORS.NI;
    if (direction === 'high_good') {
      if (poor !== null && poor !== undefined) {
        rules.push(buildRule(range, 'less', poor, null, STATUS_COLORS.POOR));
      }
      if (good !== null && good !== undefined) {
        rules.push(buildRule(range, 'greater_equal', good, null, STATUS_COLORS.GOOD));
      }
      if (good !== null && good !== undefined && poor !== null && poor !== undefined) {
        const low = Math.min(good, poor);
        const high = Math.max(good, poor);
        rules.push(buildRule(range, 'between', low, high, neutralColor));
      }
      return;
    }
    if (good !== null && good !== undefined) {
      rules.push(buildRule(range, 'less_equal', good, null, STATUS_COLORS.GOOD));
    }
    if (poor !== null && poor !== undefined) {
      rules.push(buildRule(range, 'greater', poor, null, STATUS_COLORS.POOR));
    }
    if (good !== null && good !== undefined && poor !== null && poor !== undefined) {
      const low = Math.min(good, poor);
      const high = Math.max(good, poor);
      rules.push(buildRule(range, 'between', low, high, neutralColor));
    }
  }

  function buildRule(range, type, a, b, color) {
    const builder = SpreadsheetApp.newConditionalFormatRule().setRanges([range]);
    switch (type) {
      case 'less':
        if (a !== null && a !== undefined) {
          builder.whenNumberLessThan(a);
        }
        break;
      case 'less_equal':
        if (a !== null && a !== undefined) {
          builder.whenNumberLessThanOrEqualTo(a);
        }
        break;
      case 'greater':
        if (a !== null && a !== undefined) {
          builder.whenNumberGreaterThan(a);
        }
        break;
      case 'greater_equal':
        if (a !== null && a !== undefined) {
          builder.whenNumberGreaterThanOrEqualTo(a);
        }
        break;
      case 'between':
        if (a !== null && a !== undefined && b !== null && b !== undefined) {
          builder.whenNumberBetween(a, b);
        }
        break;
    }
    return builder.setBackground(color).build();
  }

  function findMetricColumns(metric, headerMap) {
    if (!metric) {
      return [];
    }
    const normalized = normalizeHeader(metric);
    const candidates = [];

    if (normalized === 'lcp' || normalized === 'inp' || normalized === 'cls') {
      candidates.push(normalized, `${normalized}_p90`, `p90_${normalized}`, `${normalized}p90`);
    } else if (normalized.endsWith('_pct')) {
      const base = normalized.replace(/_pct$/, '');
      candidates.push(normalized, `${base}_good_pct`, `${base}_pct`, `${base}_good`);
    } else {
      candidates.push(normalized, `${normalized}_avg`, `${normalized}_value`);
    }

    const columns = [];
    candidates.forEach(candidate => {
      if (candidate && headerMap[candidate] && !columns.includes(headerMap[candidate])) {
        columns.push(headerMap[candidate]);
      }
    });
    return columns;
  }

  function loadFormatterMetricThresholds() {
    const ss = getSpreadsheet();
    if (!ss) {
      return [];
    }
    const sheet = ss.getSheetByName(FORMATTER_CONFIG_SHEET);
    if (!sheet) {
      return typeof DEFAULT_METRIC_FALLBACKS !== 'undefined' ? DEFAULT_METRIC_FALLBACKS : [];
    }
    const values = sheet.getDataRange().getValues();
    if (values.length < 2) {
      return typeof DEFAULT_METRIC_FALLBACKS !== 'undefined' ? DEFAULT_METRIC_FALLBACKS : [];
    }
    const headers = values[0].map(normalizeHeader);
    const metricIdx = headers.indexOf('metric');
    const goodIdx = findFirstIndex(headers, ['good', 'good_', 'good__', 'good_threshold', 'green', 'green_threshold', 'expected']);
    const poorIdx = findFirstIndex(headers, ['poor', 'poor_', 'poor__', 'poor_threshold', 'red', 'red_threshold', 'bad']);
    const directionIdx = findFirstIndex(headers, ['direction', 'trend', 'mode']);
    if (metricIdx === -1 || goodIdx === -1 || poorIdx === -1) {
      return typeof DEFAULT_METRIC_FALLBACKS !== 'undefined' ? DEFAULT_METRIC_FALLBACKS : [];
    }
    const thresholds = [];
    const seen = new Set();
    for (let i = 1; i < values.length; i++) {
      const row = values[i];
      const metricName = row[metricIdx];
      if (!metricName) {
        continue;
      }
      const directionValue = directionIdx === -1 ? '' : row[directionIdx];
      const direction = directionValue ? directionValue.toString().trim().toLowerCase() : 'low_good';
      thresholds.push({
        metric: metricName.toString(),
        good: toNumber(row[goodIdx]),
        poor: toNumber(row[poorIdx]),
        direction,
      });
      seen.add(normalizeHeader(metricName));
    }
    // Добавляем fallback для метрик, которых нет в Config
    if (typeof DEFAULT_METRIC_FALLBACKS !== 'undefined') {
      DEFAULT_METRIC_FALLBACKS.forEach(fallback => {
        const normalized = normalizeHeader(fallback.metric);
        if (seen.has(normalized)) {
          return;
        }
        thresholds.push({
          metric: fallback.metric,
          good: fallback.good,
          poor: fallback.poor,
          direction: fallback.direction,
        });
        seen.add(normalized);
      });
    }
    return thresholds;
  }

  function findFirstIndex(values, candidates) {
    for (let i = 0; i < candidates.length; i++) {
      const index = values.indexOf(candidates[i]);
      if (index !== -1) {
        return index;
      }
    }
    return -1;
  }

  function normalizeHeader(value) {
    if (value === null || value === undefined) {
      return '';
    }
    return value.toString().trim().toLowerCase().replace(/\s+/g, '_').replace(/[^\w_]/g, '');
  }

  function toNumber(value) {
    if (value === null || value === undefined || value === '') {
      return null;
    }
    if (typeof value === 'number') {
      return value;
    }
    const cleaned = value.toString().trim().replace(',', '.').replace(/[^\d.\-]/g, '');
    return cleaned ? parseFloat(cleaned) : null;
  }

  return {
    applyVisualFormatting: applyVisualFormattingInternal,
    setupPerfSheets: setupPerfSheetsInternal,
    formatAllPerfSheets: formatAllPerfSheetsInternal
  };
})();

function applyVisualFormatting() {
  PerfFormatter.applyVisualFormatting();
}

function applyConditionalFormatting() {
  PerfFormatter.applyVisualFormatting();
}

function setupPerfSheets() {
  PerfFormatter.setupPerfSheets();
}

function formatAllPerfSheets() {
  PerfFormatter.formatAllPerfSheets();
}
