const RUNS_SHEET = 'Runs';
const ROUTES_SHEET = 'Routes';
const STABILITY_SHEET = 'Stability';
const DASHBOARD_SHEET = 'Dashboard';
const CONFIG_SHEET = 'Config';

const TIME_METRIC_KEYS = ['lcp', 'inp', 'ttfb', 'fcp', 'tbt', 'tti', 'si', 'speed', 'interactive'];

const ROUTE_TYPE_MAP = {
  main: 'home',
  s_video: 'video',
  models: 'model',
  s_model: 'model',
  categories: 'category',
  s_category: 'category',
  s_studio: 'studio',
  dreams: 'content',
  s_dream: 'content',
};

const ALERT_COLORS = {
  HIGH: '#FFCDD2',
  MEDIUM: '#FFF8E1',
  LOW: '#E8F5E9',
};

const STATUS_COLORS = {
  GOOD: '#C8E6C9',
  NI: '#FFF9C4',
  POOR: '#FFCDD2',
  DEFAULT: '#CFD8DC',
};

const BLOCK_HEADER_COLOR = '#1B1F24';
const BLOCK_HEADER_FONT_COLOR = '#FFFFFF';

const DEFAULT_METRIC_FALLBACKS = [
  { metric: 'paint', good: 2500, poor: 4000, direction: 'low_good' },
  { metric: 'speed', good: 3400, poor: 5800, direction: 'low_good' },
  { metric: 'interactive', good: 3800, poor: 7300, direction: 'low_good' },
  { metric: 'network', good: 800, poor: 1800, direction: 'low_good' },
];

function updatePerfAnalytics() {
  const ss = SpreadsheetApp.getActive();
  ensurePerfAnalyticsTriggers(ss);
  const dashboard = getOrCreateSheet(ss, DASHBOARD_SHEET);
  dashboard.clear();
  dashboard.getCharts().forEach(chart => dashboard.removeChart(chart));

  const runRecords = readSheetRecords(ss.getSheetByName(RUNS_SHEET));
  if (!runRecords.length) {
    showEmptyMessage(dashboard);
    return;
  }
  const runs = runRecords.map(extractRunMetrics).filter(Boolean);
  if (!runs.length) {
    showEmptyMessage(dashboard);
    return;
  }

  const routes = readSheetRecords(ss.getSheetByName(ROUTES_SHEET)).map(parseRouteRecord).filter(Boolean);
  const stabilityRows = readSheetRecords(ss.getSheetByName(STABILITY_SHEET)).map(parseStabilityRecord).filter(Boolean);
  const stabilityMap = buildStabilityMap(stabilityRows);
  const thresholds = loadMetricThresholds(ss);

  const latest = runs[runs.length - 1];
  const previous = runs.length > 1 ? runs[runs.length - 2] : null;
  const trendRuns = runs.slice(-10);

  let cursor = renderTitleBlock(dashboard, 1);
  cursor = renderAlertsBlock(dashboard, cursor, latest, previous, routes, stabilityRows);
  cursor = renderOverviewBlock(dashboard, cursor, latest, thresholds);
  cursor = renderTrendBlock(dashboard, cursor, trendRuns, stabilityRows);
  cursor = renderWorstPagesBlock(dashboard, cursor, routes);
  cursor = renderDeviceSplitBlock(dashboard, cursor, routes);
  cursor = renderDiagnosticsBlock(dashboard, cursor, latest);
  cursor = renderRouteHealthBlock(dashboard, cursor, routes, stabilityMap);
  cursor = renderExperimentsBlock(dashboard, cursor, runs);
  autoSizeColumns(dashboard);
}

function ensurePerfAnalyticsTriggers(ss) {
  const handler = 'updatePerfAnalytics';
  const triggers = ScriptApp.getProjectTriggers();
  const hasEdit = triggers.some(trigger => trigger.getHandlerFunction() === handler && trigger.getEventType() === ScriptApp.EventType.ON_EDIT);
  if (!hasEdit) {
    ScriptApp.newTrigger(handler).forSpreadsheet(ss).onEdit().create();
  }
  const hasClock = triggers.some(trigger => trigger.getHandlerFunction() === handler && trigger.getEventType() === ScriptApp.EventType.CLOCK);
  if (!hasClock) {
    ScriptApp.newTrigger(handler).timeBased().everyHours(2).create();
  }
}

function getOrCreateSheet(ss, name) {
  let sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
  }
  return sheet;
}

function showEmptyMessage(sheet) {
  sheet.getRange('A1').setValue('Данных ещё нет, запусти проверки Lighthouse и обнови дашборд.').setFontSize(14).setFontWeight('bold');
}

function autoSizeColumns(sheet) {
  for (let i = 1; i <= 10; i++) {
    sheet.setColumnWidth(i, 130);
  }
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
    records.push(record);
  }
  return records;
}

function normalizeHeader(value) {
  if (value === null || value === undefined) {
    return '';
  }
  return value.toString().trim().toLowerCase().replace(/\s+/g, '_').replace(/[^\w_]/g, '');
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

function extractRunMetrics(record) {
  if (!record) {
    return null;
  }
  const runId = toText(getRecordValue(record, ['run_id']));
  const date = toText(getRecordValue(record, ['date']));
  if (!runId && !date) {
    return null;
  }
  return {
    runId,
    date,
    tag: toText(getRecordValue(record, ['tag'])),
    pages: parseNumber(getRecordValue(record, ['pages'])),
    avgScore: parseNumber(getRecordValue(record, ['avg_score', 'score'])),
    lcp: normalizeTiming(getRecordValue(record, ['p90_lcp', 'lcp_p90', 'lcp']), 'lcp'),
    inp: normalizeTiming(getRecordValue(record, ['p90_inp', 'inp_p90', 'inp']), 'inp'),
    cls: parseNumber(getRecordValue(record, ['p90_cls', 'cls_p90', 'cls'])),
    ttfb: normalizeTiming(getRecordValue(record, ['ttfb', 'avg_ttfb', 'ttfb_avg']), 'ttfb'),
    tbt: normalizeTiming(getRecordValue(record, ['tbt', 'total_blocking_time']), 'tbt'),
    fcp: normalizeTiming(getRecordValue(record, ['fcp', 'first_contentful_paint']), 'fcp'),
    tti: normalizeTiming(getRecordValue(record, ['tti', 'time_to_interactive']), 'tti'),
    speed: normalizeTiming(getRecordValue(record, ['speed', 'speed_index']), 'speed'),
  };
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

function toText(value) {
  if (value === null || value === undefined) {
    return '';
  }
  return value.toString();
}

function parseRouteRecord(record) {
  const page = toText(getRecordValue(record, ['page']));
  if (!page) {
    return null;
  }
  const device = toText(getRecordValue(record, ['device'])) || 'unknown';
  return {
    page,
    device,
    avgScore: parseNumber(getRecordValue(record, ['avg_score'])),
    lcp: normalizeTiming(getRecordValue(record, ['p90_lcp', 'lcp_p90', 'lcp']), 'lcp'),
    inp: normalizeTiming(getRecordValue(record, ['p90_inp', 'inp_p90', 'inp']), 'inp'),
    cls: parseNumber(getRecordValue(record, ['p90_cls', 'cls_p90', 'cls'])),
    tests: parseNumber(getRecordValue(record, ['tests'])),
    type: ROUTE_TYPE_MAP[page] || 'route',
  };
}

function parseStabilityRecord(record) {
  const page = toText(getRecordValue(record, ['page']));
  const device = toText(getRecordValue(record, ['device']));
  if (!page || !device) {
    return null;
  }
  const deviceKey = device.toLowerCase();
  return {
    key: `${page}|${deviceKey}`,
    lcpStd: parseNumber(getRecordValue(record, ['lcp_std'])),
    inpStd: parseNumber(getRecordValue(record, ['inp_std'])),
    clsStd: parseNumber(getRecordValue(record, ['cls_std'])),
    stabilityScore: parseNumber(getRecordValue(record, ['stability_score'])),
  };
}

function buildStabilityMap(records) {
  const map = {};
  records.forEach(record => {
    if (record && record.key) {
      map[record.key] = record;
    }
  });
  return map;
}

function loadMetricThresholds(ss) {
  const sheet = ss.getSheetByName(CONFIG_SHEET);
  const metrics = {};
  if (!sheet) {
    return populateFallbackThresholds(metrics);
  }
  const values = sheet.getDataRange().getValues();
  if (!values.length) {
    return populateFallbackThresholds(metrics);
  }
  const headers = values[0].map(normalizeHeader);
  const metricIdx = headers.indexOf('metric');
  const goodIdx = headers.indexOf('good');
  const poorIdx = headers.indexOf('poor');
  const directionIdx = headers.indexOf('direction');
  for (let i = 1; i < values.length; i++) {
    const row = values[i];
    const metricName = row[metricIdx];
    if (!metricName) {
      continue;
    }
    const key = normalizeHeader(metricName);
    metrics[key] = {
      good: parseNumber(row[goodIdx]),
      poor: parseNumber(row[poorIdx]),
      direction: row[directionIdx] ? row[directionIdx].toString().trim().toLowerCase() : 'low_good',
    };
  }
  return populateFallbackThresholds(metrics);
}

function populateFallbackThresholds(base) {
  const result = Object.assign({}, base);
  DEFAULT_METRIC_FALLBACKS.forEach(fallback => {
    const key = normalizeHeader(fallback.metric);
    if (!result[key]) {
      result[key] = {
        good: fallback.good,
        poor: fallback.poor,
        direction: fallback.direction,
      };
    }
  });
  return result;
}

function assessMetricStatus(metricKey, value, thresholds) {
  if (value === null || value === undefined) {
    return { status: 'NI', color: STATUS_COLORS.DEFAULT };
  }
  const key = normalizeHeader(metricKey);
  const config = thresholds[key];
  if (!config) {
    return { status: 'NI', color: STATUS_COLORS.DEFAULT };
  }
  const { good, poor, direction } = config;
  if (direction === 'high_good') {
    if (poor !== null && poor !== undefined && value < poor) {
      return { status: 'POOR', color: STATUS_COLORS.POOR };
    }
    if (good !== null && good !== undefined && value >= good) {
      return { status: 'GOOD', color: STATUS_COLORS.GOOD };
    }
    return { status: 'NI', color: STATUS_COLORS.NI };
  }
  if (direction === 'low_good') {
    if (good !== null && good !== undefined && value <= good) {
      return { status: 'GOOD', color: STATUS_COLORS.GOOD };
    }
    if (poor !== null && poor !== undefined && value > poor) {
      return { status: 'POOR', color: STATUS_COLORS.POOR };
    }
    return { status: 'NI', color: STATUS_COLORS.NI };
  }
  return { status: 'NI', color: STATUS_COLORS.NI };
}

function metricDelta(current, previous) {
  if (current === null || previous === null || previous === 0) {
    return null;
  }
  return ((current - previous) / previous) * 100;
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

function renderTitleBlock(sheet, row) {
  const range = sheet.getRange(row, 1, 1, 6);
  range.merge();
  range.setValue('Performance QA Dashboard');
  range.setFontWeight('bold');
  range.setFontSize(16);
  range.setBackground(BLOCK_HEADER_COLOR);
  range.setFontColor(BLOCK_HEADER_FONT_COLOR);
  range.setHorizontalAlignment('center');
  return row + 2;
}

function renderAlertsBlock(sheet, row, latest, previous, routes, stabilityRows) {
  const header = sheet.getRange(row, 1, 1, 3);
  header.setValues([['BLOCK 0 — ALERTS (AUTO QA)', '', '']]);
  header.setBackground(BLOCK_HEADER_COLOR);
  header.setFontColor(BLOCK_HEADER_FONT_COLOR);
  header.setFontWeight('bold');
  row++;
  const alerts = buildAlerts(latest, previous, routes, stabilityRows);
  if (!alerts.length) {
    sheet.getRange(row, 1).setValue('Нет критичных отклонений — CWV в норме.').setFontStyle('italic');
    return row + 2;
  }
  sheet.getRange(row, 1, 1, 3).setValues([['Level', 'Alert', 'Reason']]).setFontWeight('bold');
  row++;
  alerts.forEach(alert => {
    sheet.getRange(row, 1).setValue(alert.level).setBackground(ALERT_COLORS[alert.level] || '#FFF3E0');
    sheet.getRange(row, 2).setValue(alert.text);
    sheet.getRange(row, 3).setValue(alert.reason);
    row++;
  });
  return row + 1;
}

function buildAlerts(latest, previous, routes, stabilityRows) {
  const alerts = [];
  const deltaLcp = metricDelta(latest.lcp, previous ? previous.lcp : null);
  const deltaInp = metricDelta(latest.inp, previous ? previous.inp : null);
  const deltaTtfb = metricDelta(latest.ttfb, previous ? previous.ttfb : null);
  const avgClsStd = stabilityRows.length ? stabilityRows.reduce((sum, rec) => sum + (rec.clsStd || 0), 0) / stabilityRows.length : 0;
  const highestRoute = routes.slice().sort((a, b) => (b.lcp || 0) - (a.lcp || 0))[0];

  if (deltaLcp !== null && deltaLcp >= 20) {
    alerts.push({
      level: 'HIGH',
      text: `[HIGH] LCP regression (${formatPercent(deltaLcp)})`,
      reason: `Reason: ${describeTtfb(latest, deltaTtfb)}${highestRoute ? `; worst page ${highestRoute.page} (${highestRoute.device})` : ''}`,
    });
  } else if (deltaLcp !== null && deltaLcp >= 10) {
    alerts.push({
      level: 'MEDIUM',
      text: `[MEDIUM] LCP degraded (${formatPercent(deltaLcp)})`,
      reason: `Reason: ${describeTtfb(latest, deltaTtfb)}`,
    });
  } else if (deltaLcp !== null && deltaLcp >= 5) {
    alerts.push({
      level: 'LOW',
      text: `[LOW] LCP trend ↑ (${formatPercent(deltaLcp)})`,
      reason: `Reason: следи за ${highestRoute ? highestRoute.page : 'ключевыми страницами'}.`,
    });
  }

  if (latest.inp && latest.inp >= 1000) {
    alerts.push({
      level: 'HIGH',
      text: '[HIGH] INP critical (>1000ms)',
      reason: `Reason: ${describeMainThread(latest)}; дёргается JS/тяжёлые задачи.`,
    });
  } else if (latest.inp && latest.inp >= 200) {
    alerts.push({
      level: 'MEDIUM',
      text: '[MEDIUM] INP elevated (>200ms)',
      reason: `Reason: ${describeMainThread(latest)}.`,
    });
  } else if (deltaInp !== null && deltaInp >= 20) {
    alerts.push({
      level: 'LOW',
      text: '[LOW] INP growth',
      reason: `Reason: INP ${formatPercent(deltaInp)} drift.`,
    });
  }

  if (latest.cls && latest.cls >= 0.25) {
    alerts.push({
      level: 'HIGH',
      text: '[HIGH] CLS critical (>0.25)',
      reason: `Reason: unstable layout; CLS std avg ${avgClsStd.toFixed(3)}.`,
    });
  } else if (latest.cls && (latest.cls >= 0.1 || avgClsStd > 0.05)) {
    alerts.push({
      level: 'MEDIUM',
      text: '[MEDIUM] CLS unstable (>0.1)',
      reason: `Reason: CLS std ${avgClsStd.toFixed(3)}; баннеры/шрифты двигаются.`,
    });
  }

  if (latest.ttfb && latest.ttfb > 800) {
    alerts.push({
      level: 'HIGH',
      text: '[HIGH] Backend bottleneck (TTFB > 800ms)',
      reason: `Reason: ${formatMetricValue('ttfb', latest.ttfb)} — сервер откликается медленно.`,
    });
  } else if (deltaTtfb !== null && deltaTtfb > 20) {
    alerts.push({
      level: 'MEDIUM',
      text: `[MEDIUM] TTFB growth (${formatPercent(deltaTtfb)})`,
      reason: 'Reason: response time растёт — может затронуть LCP.',
    });
  }

  return alerts;
}

function describeTtfb(latest, delta) {
  if (!latest.ttfb) {
    return 'TTFB missing';
  }
  if (latest.ttfb > 800) {
    return 'TTFB > 800 ms (backend slow)';
  }
  if (delta !== null && delta > 5) {
    return `TTFB +${delta.toFixed(1)}%`;
  }
  return 'TTFB stable';
}

function describeMainThread(latest) {
  if (!latest.tbt) {
    return 'TBT not available';
  }
  if (latest.tbt > 300) {
    return 'TBT > 300 ms (main thread busy)';
  }
  return 'TBT < 300 ms';
}

function renderOverviewBlock(sheet, row, latest, thresholds) {
  const header = sheet.getRange(row, 1, 1, 3);
  header.setValues([['BLOCK 1 — OVERVIEW', '', '']]);
  header.setBackground(BLOCK_HEADER_COLOR);
  header.setFontColor(BLOCK_HEADER_FONT_COLOR);
  header.setFontWeight('bold');
  row++;
  sheet.getRange(row, 1, 1, 3).setValues([['Metric', 'Value', 'Status']]).setFontWeight('bold');
  row++;
  [
    { label: 'LCP p90', key: 'lcp', value: latest.lcp },
    { label: 'INP p90', key: 'inp', value: latest.inp },
    { label: 'CLS p90', key: 'cls', value: latest.cls },
    { label: 'TTFB avg', key: 'ttfb', value: latest.ttfb },
  ].forEach(metric => {
    const status = assessMetricStatus(metric.key, metric.value, thresholds);
    sheet.getRange(row, 1).setValue(metric.label);
    sheet.getRange(row, 2).setValue(formatMetricValue(metric.key, metric.value));
    sheet.getRange(row, 3).setValue(status.status);
    sheet.getRange(row, 3).setBackground(status.color);
    row++;
  });
  return row + 1;
}

function renderTrendBlock(sheet, row, trendRuns, stabilityRows) {
  const header = sheet.getRange(row, 1, 1, 4);
  header.setValues([['BLOCK 2 — TREND', '', '', '']]);
  header.setBackground(BLOCK_HEADER_COLOR);
  header.setFontColor(BLOCK_HEADER_FONT_COLOR);
  header.setFontWeight('bold');
  row++;
  if (!trendRuns.length) {
    sheet.getRange(row, 1).setValue('Нет истории прогонов.');
    return row + 2;
  }
  const columns = ['Run ID', 'LCP p90', 'INP p90', 'CLS p90'];
  sheet.getRange(row, 1, 1, columns.length).setValues([columns]).setFontWeight('bold');
  row++;
  const data = trendRuns.map(run => [
    run.runId || '—',
    run.lcp || 0,
    run.inp || 0,
    run.cls || 0,
  ]);
  const dataRange = sheet.getRange(row, 1, data.length, columns.length);
  dataRange.setValues(data);
  sheet.getRange(row, 2, data.length, 1).setNumberFormat('0');
  sheet.getRange(row, 3, data.length, 1).setNumberFormat('0');
  sheet.getRange(row, 4, data.length, 1).setNumberFormat('0.000');
  insertLineChart(sheet, sheet.getRange(row - 1, 1, data.length + 1, columns.length), row - 1, 6, 'CWV p90 trend');
  row += data.length;
  row += 1;
  sheet.getRange(row, 1, 1, 4).setValues([['Stability — std deviation', '', '', '']]);
  sheet.getRange(row, 1, 1, 4).setFontWeight('bold');
  sheet.getRange(row, 1, 1, 4).setBackground('#263238');
  sheet.getRange(row, 1, 1, 4).setFontColor('#ffffff');
  row++;
  if (!stabilityRows.length) {
    sheet.getRange(row, 1).setValue('Stability data missing.');
    return row + 2;
  }
  const stabilityColumns = ['Page', 'LCP std', 'INP std', 'CLS std'];
  sheet.getRange(row, 1, 1, stabilityColumns.length).setValues([stabilityColumns]).setFontWeight('bold');
  row++;
  const stabilityData = stabilityRows
    .slice()
    .sort((a, b) => (b.lcpStd || 0) - (a.lcpStd || 0))
    .slice(0, 8);
  stabilityData.forEach(item => {
    sheet.getRange(row, 1).setValue(item.page);
    sheet.getRange(row, 2).setValue(item.lcpStd || 0);
    sheet.getRange(row, 3).setValue(item.inpStd || 0);
    sheet.getRange(row, 4).setValue(item.clsStd || 0);
    row++;
  });
  const chartData = [['Page', 'LCP std', 'INP std', 'CLS std']];
  stabilityData.forEach(item => chartData.push([item.page, item.lcpStd || 0, item.inpStd || 0, item.clsStd || 0]));
  const helperRow = row;
  const helperRange = sheet.getRange(helperRow, 7, chartData.length, 4);
  helperRange.setValues(chartData);
  insertLineChart(sheet, helperRange, helperRow, 6, 'Std deviation per page');
  row += chartData.length;
  return row + 2;
}

function renderWorstPagesBlock(sheet, row, routes) {
  const header = sheet.getRange(row, 1, 1, 5);
  header.setValues([['BLOCK 3 — WORST PAGES', '', '', '', '']]);
  header.setBackground(BLOCK_HEADER_COLOR);
  header.setFontColor(BLOCK_HEADER_FONT_COLOR);
  header.setFontWeight('bold');
  row++;
  if (!routes.length) {
    sheet.getRange(row, 1).setValue('Routes not collected.');
    return row + 2;
  }
  const sorted = routes.slice().sort((a, b) => (b.lcp || 0) - (a.lcp || 0));
  const rows = sorted.slice(0, 10);
  sheet.getRange(row, 1, 1, 5).setValues([['Page', 'Device', 'LCP p90', 'INP p90', 'CLS p90']]).setFontWeight('bold');
  row++;
  rows.forEach(route => {
    sheet.getRange(row, 1).setValue(route.page);
    sheet.getRange(row, 2).setValue(route.device);
    sheet.getRange(row, 3).setValue(route.lcp || 0);
    sheet.getRange(row, 4).setValue(route.inp || 0);
    sheet.getRange(row, 5).setValue(route.cls || 0);
    row++;
  });
  const helperData = [['Page', 'LCP p90']];
  rows.forEach(route => helperData.push([route.page, route.lcp || 0]));
  const helperRow = row;
  const helperRange = sheet.getRange(helperRow, 7, helperData.length, 2);
  helperRange.setValues(helperData);
  insertColumnChart(sheet, helperRange, helperRow, 6, 'Top 10 LCP');
  row += helperData.length + 1;
  return row;
}

function renderDeviceSplitBlock(sheet, row, routes) {
  const header = sheet.getRange(row, 1, 1, 4);
  header.setValues([['BLOCK 4 — DEVICE SPLIT', '', '', '']]);
  header.setBackground(BLOCK_HEADER_COLOR);
  header.setFontColor(BLOCK_HEADER_FONT_COLOR);
  header.setFontWeight('bold');
  row++;
  if (!routes.length) {
    sheet.getRange(row, 1).setValue('Нет данных по девайсам.');
    return row + 2;
  }
  const buckets = routes.reduce((acc, route) => {
    const device = route.device.toLowerCase();
    if (!acc[device]) {
      acc[device] = { count: 0, lcp: 0, inp: 0, cls: 0 };
    }
    if (route.lcp) {
      acc[device].lcp += route.lcp;
    }
    if (route.inp) {
      acc[device].inp += route.inp;
    }
    if (route.cls) {
      acc[device].cls += route.cls;
    }
    acc[device].count++;
    return acc;
  }, {});
  const rows = Object.entries(buckets).map(([device, totals]) => {
    const count = totals.count || 1;
    return {
      device,
      lcp: Math.round(totals.lcp / count) || 0,
      inp: Math.round(totals.inp / count) || 0,
      cls: parseFloat((totals.cls / count).toFixed(3)) || 0,
    };
  });
  sheet.getRange(row, 1, 1, 4).setValues([['Device', 'LCP p90', 'INP p90', 'CLS p90']]).setFontWeight('bold');
  row++;
  rows.forEach(entry => {
    sheet.getRange(row, 1).setValue(entry.device);
    sheet.getRange(row, 2).setValue(entry.lcp);
    sheet.getRange(row, 3).setValue(entry.inp);
    sheet.getRange(row, 4).setValue(entry.cls);
    row++;
  });
  const chartData = [['Device', 'LCP p90', 'INP p90', 'CLS p90']];
  rows.forEach(entry => chartData.push([entry.device, entry.lcp, entry.inp, entry.cls]));
  const helperRow = row;
  const helperRange = sheet.getRange(helperRow, 7, chartData.length, 4);
  helperRange.setValues(chartData);
  insertGroupedBarChart(sheet, helperRange, helperRow, 6, 'Mobile vs Desktop');
  row += chartData.length + 1;
  return row;
}

function renderDiagnosticsBlock(sheet, row, latest) {
  const header = sheet.getRange(row, 1, 1, 2);
  header.setValues([['BLOCK 5 — DIAGNOSTICS', '']]);
  header.setBackground(BLOCK_HEADER_COLOR);
  header.setFontColor(BLOCK_HEADER_FONT_COLOR);
  header.setFontWeight('bold');
  row++;
  const diagnostics = buildDiagnostics(latest);
  if (!diagnostics.length) {
    sheet.getRange(row, 1).setValue('Сигналов нет, продолжай мониторинг.');
    return row + 2;
  }
  sheet.getRange(row, 1, 1, 2).setValues([['Issue', 'Reason']]).setFontWeight('bold');
  row++;
  diagnostics.forEach(item => {
    sheet.getRange(row, 1).setValue(item.title);
    sheet.getRange(row, 2).setValue(item.detail);
    row++;
  });
  return row + 1;
}

function buildDiagnostics(latest) {
  const diagnostics = [];
  if (latest.ttfb && latest.ttfb > 800) {
    diagnostics.push({ title: 'Backend bottleneck', detail: `TTFB ${formatMetricValue('ttfb', latest.ttfb)} > 800ms` });
  }
  if (latest.ttfb && latest.lcp && latest.ttfb <= 800 && latest.lcp > 4000) {
    diagnostics.push({ title: 'Frontend rendering', detail: `LCP ${formatMetricValue('lcp', latest.lcp)} > 4000ms при нормальном TTFB` });
  }
  if (latest.inp && (latest.inp > 200 || (latest.tbt && latest.tbt > 300))) {
    diagnostics.push({ title: 'Main thread blocking', detail: `INP ${formatMetricValue('inp', latest.inp)} | TBT ${formatMetricValue('tbt', latest.tbt)}` });
  }
  if (latest.cls && latest.cls > 0.1) {
    diagnostics.push({ title: 'Layout shift', detail: `CLS ${latest.cls.toFixed(3)} > 0.1 (изображения/баннеры)` });
  }
  return diagnostics;
}

function renderRouteHealthBlock(sheet, row, routes, stabilityMap) {
  const header = sheet.getRange(row, 1, 1, 5);
  header.setValues([['BLOCK 6 — ROUTE HEALTH', '', '', '', '']]);
  header.setBackground(BLOCK_HEADER_COLOR);
  header.setFontColor(BLOCK_HEADER_FONT_COLOR);
  header.setFontWeight('bold');
  row++;
  if (!routes.length) {
    sheet.getRange(row, 1).setValue('Нет данных по маршрутам.');
    return row + 2;
  }
  sheet.getRange(row, 1, 1, 5).setValues([['Page', 'Type', 'Device', 'Status', 'Reason']]).setFontWeight('bold');
  row++;
  routes.forEach(route => {
    const key = `${route.page}|${route.device.toLowerCase()}`;
    const stability = stabilityMap[key];
    const statusInfo = evaluateRouteHealth(route, stability);
    sheet.getRange(row, 1).setValue(route.page);
    sheet.getRange(row, 2).setValue(route.type);
    sheet.getRange(row, 3).setValue(route.device);
    sheet.getRange(row, 4).setValue(statusInfo.status);
    sheet.getRange(row, 5).setValue(statusInfo.reason);
    row++;
  });
  return row + 1;
}

function evaluateRouteHealth(route, stability) {
  const { lcp = 0, inp = 0, cls = 0 } = route;
  if (lcp > 10000 || inp > 1000 || cls > 0.25) {
    return { status: 'BAD', reason: `LCP ${formatMetricValue('lcp', lcp)}, INP ${formatMetricValue('inp', inp)}, CLS ${cls ? cls.toFixed(3) : 0}` };
  }
  if (lcp > 4000 || inp > 500 || cls > 0.1) {
    return { status: 'MEDIUM', reason: `Metrics elevated (LCP ${formatMetricValue('lcp', lcp)})` };
  }
  const stabilityHint = stability && stability.clsStd ? `CLS std ${stability.clsStd.toFixed(3)}` : '-';
  return { status: 'OK', reason: stabilityHint };
}

function renderExperimentsBlock(sheet, row, runs) {
  const header = sheet.getRange(row, 1, 1, 7);
  header.setValues([['BLOCK 7 — EXPERIMENTS', '', '', '', '', '', '']]);
  header.setBackground(BLOCK_HEADER_COLOR);
  header.setFontColor(BLOCK_HEADER_FONT_COLOR);
  header.setFontWeight('bold');
  row++;
  sheet.getRange(row, 1, 1, 7).setValues([['Tag', 'Run ID', 'LCP p90', 'Δ LCP', 'INP p90', 'CLS p90', 'Result']]).setFontWeight('bold');
  row++;
  let hasTag = false;
  runs.forEach((run, index) => {
    if (!run.tag) {
      return;
    }
    hasTag = true;
    const baseline = findBaselineRun(runs, index);
    const delta = metricDelta(run.lcp, baseline ? baseline.lcp : null);
    sheet.getRange(row, 1).setValue(run.tag);
    sheet.getRange(row, 2).setValue(run.runId);
    sheet.getRange(row, 3).setValue(formatMetricValue('lcp', run.lcp));
    sheet.getRange(row, 4).setValue(delta !== null ? formatPercent(delta) : '—');
    sheet.getRange(row, 5).setValue(formatMetricValue('inp', run.inp));
    sheet.getRange(row, 6).setValue(run.cls ? run.cls.toFixed(3) : '—');
    sheet.getRange(row, 7).setValue(delta !== null && delta <= 0 ? 'OK' : 'REGRESS');
    row++;
  });
  if (!hasTag) {
    sheet.getRange(row, 1).setValue('Tagged runs not found.');
    row++;
  }
  return row + 1;
}

function findBaselineRun(runs, index) {
  for (let i = index - 1; i >= 0; i--) {
    if (!runs[i].tag) {
      return runs[i];
    }
  }
  return null;
}

function insertLineChart(sheet, range, row, column, title) {
  const chart = sheet.newChart()
    .asLineChart()
    .addRange(range)
    .setPosition(row, column, 0, 0)
    .setOption('title', title)
    .setOption('legend', { position: 'bottom' })
    .setOption('curveType', 'function')
    .setNumHeaders(1)
    .build();
  sheet.insertChart(chart);
}

function insertColumnChart(sheet, range, row, column, title) {
  const chart = sheet.newChart()
    .asColumnChart()
    .addRange(range)
    .setPosition(row, column, 0, 0)
    .setOption('title', title)
    .setOption('legend', { position: 'bottom' })
    .setNumHeaders(1)
    .build();
  sheet.insertChart(chart);
}

function insertGroupedBarChart(sheet, range, row, column, title) {
  const chart = sheet.newChart()
    .asBarChart()
    .addRange(range)
    .setPosition(row, column, 0, 0)
    .setOption('title', title)
    .setOption('legend', { position: 'bottom' })
    .setNumHeaders(1)
    .build();
  sheet.insertChart(chart);
}
