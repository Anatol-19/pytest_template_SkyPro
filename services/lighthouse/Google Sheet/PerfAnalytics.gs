const RUNS_SHEET = 'Runs';
const ROUTES_SHEET = 'Routes';
const STABILITY_SHEET = 'Stability';
const DASHBOARD_SHEETS = ['Dashboard [VRP]', 'Dashboard [VRS]'];
const DASHBOARD_PROJECTS = ['VRP', 'VRS'];
const DASHBOARD_COLUMN_WIDTHS = [160, 140, 120, 110, 110, 120, 120, 120, 100, 100, 100, 100, 100, 100, 200];
const DASHBOARD_CONFIG_SHEET = 'Config';
const CRUX_SOURCE_SHEET = 'CrUX';
const CHART_COLUMN = 10;
const HELPER_COLUMN_PRIMARY = 20;
const HELPER_COLUMN_SECONDARY = 26;
const CROSS_ENV_BLOCK_HEIGHT = 18;
const TREND_BLOCK_HEIGHT = 36;
const WORST_PAGES_BLOCK_HEIGHT = 18;
const DEVICE_SPLIT_BLOCK_HEIGHT = 18;
const CONTROL_START_ROW = 1;
const CONTROL_RENDER_START_ROW = 15;

// Жёсткая сетка — фиксированные начала блоков (row numbers)
const LAYOUT = {
  CONTROLS:       { row: 1,   height: 14 },
  CONTEXT:        { row: 15,  height: 8  },
  ALERTS:         { row: 23,  height: 12 },
  CRUX_REF:       { row: 35,  height: 8  },
  OVERVIEW:       { row: 43,  height: 8  },
  CROSS_ENV:      { row: 51,  height: 18 },
  SPRINT_IMPACT:  { row: 51,  height: 18 },   // заменяет CROSS_ENV в Sprint mode
  TREND:          { row: 69,  height: 36 },
  WORST_PAGES:    { row: 105, height: 18 },
  DEVICE_SPLIT:   { row: 123, height: 18 },
  DIAGNOSTICS:    { row: 141, height: 12 },
  ROUTE_HEALTH:   { row: 153, height: 30 },
  EXPERIMENTS:       { row: 183, height: 20 },
  METRIC_BREAKDOWN:  { row: 203, height: 80 },
};

// Зоны графиков (фиксированные позиции)
const CHART_ZONES = {
  CROSS_ENV:    { row: 52,  col: 10 },
  TREND:        { row: 70,  col: 10 },
  STABILITY:    { row: 88,  col: 10 },
  DEVICE:       { row: 124, col: 10 },
  SPRINT:       { row: 52,  col: 10 },
};

const GENERATE_BUTTON_ANCHOR = { row: 4, column: 9, offsetX: 8, offsetY: 6, width: 220, height: 44 };
const GENERATE_BUTTON_PNG_BASE64 = 'iVBORw0KGgoAAAANSUhEUgAAANwAAAAsCAYAAAAOyNaYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAeRSURBVHhe7V3dax1FFO8/0dpE27745puPPlkj9itIaxR98lFE1BjUxtaWoH1pJVYL0ogvSaGiIKGEqAWpQhIfYj8oNpRCe6GkEhopDYaCqC8jM/feuTNnzjkzuzfZ7m7OD36Q7J4zc2bm/HZm9+7HJiUQCArDJrjBxc3lRfXN/Hn1yQ/jleREYxU2CcWtq/n8DJZnSL+VxhQbk7sf+rJg6mTx4JqaQPrJcPaaWoH2Tj1tfr8MjTisqvnZHHEi9VaFE3NT6vLt67BFFoHg/vnvX3Vs6iv12NBzavObT1eWz19Ygk1jsKTGT+T0XRhl/Pxyoc3ihdfR7VGwdfJw66Ti6mBeHQJ2hxagDYdO+/HyCTjtqzJfG/9Y/bl632uaJ7iFP26pp469ah22DD6jtg7vUr1H91aLp8+pRbdh6pL6ENpMXvIs1I3P7b4Dc44o5gbD8gm6fhZOudDGLZvaHmOKnxfXvXPqQGAzqCbutQ2W1MyNjv3MJLQFdPsaLTuMgYqzDuz5YJfaMtRnNfT4+/3qx9/nbNut4PTM9uTIK8bokaE+te34frXjs5cqyYGLd20DVWMs2G95/ooxmT1P+9+5OBz6EfTqdeCWT5VNbY8xye/stLrTNlqZVgOx/fB/aM/5wv0tJsVZI24fHVBbDzZXiXq1eOd+s/1WcO99e7IptnefVTtOvhgUUB0OqzP2ZOSuOnMW7o8zb3J4fiuu+K6oo5hNQYI72rAm6AEoLCNDH4rgWPYc3m109fLpg6btRnB6dmufs207fiBwqhbH1Kwd2k6iZyE1U4Xwy/eTasxJ2k6SUYm3FnWmAM7mlLioOAPmEByPfGNWVuqZTp+aaW3pWc4ITp+7mXO2ob7AoXp0BIckAD3w+CzEg05+k6RuMraSObBBfHnQdcaACqe1rDbwZr/EA5cILkp9HUTrS5/LGcF9+ct3ZoOe/qBx9cgnCj3w6yA4WFZjDLUJ7FjQdeLgl4TuchPOftw+SxFclL0j+4y+9M8GRnD6D71BX2WBxtUjvkRqkx54XHDorEAQ93MPAP65HSW47usE521IPzTpx8YCOfczzCG4LO2rA7Wuaiw4IComCajZMG9ykH7uss3BegpOMyo6Ii4ciL+mCC7K2gvOP3fSwJYp7kzo2+RNDtoP1hXa0L48eT8wgwFB+IKMIyxfBJfC+gsOznIpcJIlm2+iUIODAC24OBLrROq1Nt527IDUojsLYoLKIbg4mHgqyA0hOMPEJRNM1LzJEUt+WG4hggvKDq+Wkudnhv4sGVw8EcFFuXEE1yI12EHyROxxZEl+cAGlIMEFS9rGtPc/1Q9obFCcIrgoN5zghMKHSRGcUFggRXBCYYEUwQmFBVIEJxQWSBGcUFggRXBCYYEUwQmFBVIEJxQWSBGcUFggKyu4pNuD4K1HBKOPrmBEbkDWoG6pSrrtyrnfM8+tXmS5lviTCsltzthXqXFj45Tki/iVnfUWnAGfFKhwIgMZf5QlvP+vCMEZEPcwxmOmfS0z9lU3caf7Rsa3ZNwAgtMIBcCXQ9unPnXAJdC6Cg4pP5M/Izq8HLqvcHsa+dtMx1A21kJwMMEMgTBQG/AKhtlGp0zqrnn2NXNenf6RNxov8KeSj/Il44KzEiIomNx4Hdn7KiVur27iOUTUN2l8y8f6Ck4z6wOT8H9on/AyHWp/1nizCo564xYpREgvgZEZA/YN/B/ap8ZNlJPkGxvfErLegsvwEqFmGbw99NHARIcxrCu06UZwuNDj7emQtw1j4O1xn9CGOiCk+KbEUDbWXHDugMIBwQcrXi73ditkZkDiTQEluCjyvE+yRVy0mvn6KlPceVYE7PiWkxtXcMQSLC1JOdE1AWe+rMmXT3Aw6fgX4UK69Xjx5+yr9LjDMex6fEvKDSs4+mjO74PkLrdTR+wU5BNcEx1fXhCQVLup7bF98bhpkXQ7vmVlzQWHL4VSZigL7kJDQPDDchcXASjBkb7om7eo9mOkbPP3FRW3f5DC46J802IuL+stOOIKGLykzMMZSKo8j/iskhRvN4IjjvZecpMxw9nImQ3z9lUk7pjoOF/LpPEoFwPBnfrp66bgjuwJjMvE6ICA35/oI2wc+BINH2QqwaPxanYjOK+9xEHCIFxawv5Ym76Kxc33Je8btgu1KSGDbwv8fP03s8F8Gw5xKAv9I3IMTpKhSy+ExG88WepNT76wTso3CUzyRuH6rmFfoW1mRJMpZi62krHn8B6jL/39byO4v/5+YDZsfmun2v5peT/GmD4g9DIHnnP4pF96mnTUZ5IeTT7NNRIcvHiRXAYTc56+SmmzH1dnrJLiNQiXo2Wm/qKw1pf+LJwRnMb+U++YjWX+ZFXKgISD7F/UwBKTrAMmXLBUawNPgJTk615wsSM9uKhjgcXcfV8ltRnGhPhSoMssJ3tH+o2u9Oe8Nazgbi4v2q+g9h7ZW/HPDguFD5+PftSvNr+902hKn7Z5gtPQa0yztGx9DVWvPfUVFqFQmMiRfWbCai8jNY9MfmE15glO4/Lt62r36BvWWCgU5uMTh1+wM1sbgeDa0MLTM56+lCkUCtOpf2b79eZVKCmD/wGsfK39krKdlQAAAABJRU5ErkJggg==';
const SPRINT_METADATA_CELLS = {
  currentSprint: 'E5',
  nextSprint: 'E6',
  devDone: 'D9',
  testDone: 'E9',
  stageDone: 'F9',
  prodDone: 'G9',
};
const RAW_PERF_SHEETS = ['VRP [PROD]', 'VRP [STAGE]', 'VRP [TEST]', 'VRP [DEV]', 'VRS [PROD]', 'VRS [STAGE]', 'VRS [TEST]', 'VRS [DEV]', 'CrUX'];
const RUNS_HEADERS = ['date', 'project', 'environment', 'source', 'sprint', 'run_id', 'tag', 'iterations', 'pages', 'avg_score', 'p90_lcp', 'p90_inp', 'p90_cls', 'ttfb', 'tbt', 'fcp', 'tti', 'speed'];
const ROUTES_HEADERS = ['date', 'project', 'environment', 'source', 'sprint', 'run_id', 'tag', 'page', 'device', 'type', 'tests', 'avg_score', 'p90_lcp', 'p90_inp', 'p90_cls', 'ttfb'];
const STABILITY_HEADERS = ['project', 'environment', 'source', 'page', 'device', 'lcp_std', 'inp_std', 'cls_std', 'stability_score'];

const TIME_METRIC_KEYS = ['lcp', 'inp', 'ttfb', 'fcp', 'tbt', 'tti', 'si', 'speed', 'interactive'];
const PERF_SHEET_ID_KEYS = ['GS_SHEET_ID', 'SHEET_ID'];

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
  { metric: 'p', good: 90, poor: 50, direction: 'high_good' },
  { metric: 'lcp', good: 2500, poor: 4000, direction: 'low_good' },
  { metric: 'inp', good: 120, poor: 500, direction: 'low_good' },
  { metric: 'cls', good: 0.12, poor: 0.25, direction: 'low_good' },
  { metric: 'ttfb', good: 800, poor: 1800, direction: 'low_good' },
  { metric: 'fcp', good: 1800, poor: 3000, direction: 'low_good' },
  { metric: 'paint', good: 2500, poor: 4000, direction: 'low_good' },
  { metric: 'speed', good: 3400, poor: 5800, direction: 'low_good' },
  { metric: 'interactive', good: 3800, poor: 7300, direction: 'low_good' },
  { metric: 'network', good: 800, poor: 1800, direction: 'low_good' },
  { metric: 'tti', good: 3800, poor: 7300, direction: 'low_good' },
];

function updatePerfAnalytics() {
  const ss = getPerfSpreadsheet();
  ensurePerfAnalyticsTriggers(ss);
  rebuildAnalyticsHelperSheets(ss);

  const runRecords = readSheetRecords(ss.getSheetByName(RUNS_SHEET));
  const routeRecords = readSheetRecords(ss.getSheetByName(ROUTES_SHEET));
  const stabilityRecords = readSheetRecords(ss.getSheetByName(STABILITY_SHEET));
  const cruxRecords = readSheetRecords(ss.getSheetByName(CRUX_SOURCE_SHEET));

  const runs = runRecords.map(extractRunMetrics).filter(Boolean);
  const routes = routeRecords.map(parseRouteRecord).filter(Boolean);
  const stabilityRows = stabilityRecords.map(parseStabilityRecord).filter(Boolean);
  const cruxRows = cruxRecords.map(parseRouteRecord).filter(Boolean).filter(item => normalizeSource(item.source) === 'CRUX');
  const thresholds = loadMetricThresholds(ss);

  DASHBOARD_PROJECTS.forEach(project => {
    const dashboard = getOrCreateSheet(ss, `Dashboard [${project}]`);
    renderProjectDashboard(dashboard, project, runs, routes, stabilityRows, cruxRows, thresholds);
  });
}

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('QA Dashboard')
    .addItem('Generate Dashboard', 'updatePerfAnalytics')
    .addToUi();
}

function renderProjectDashboard(sheet, project, allRuns, allRoutes, allStabilityRows, allCruxRows, thresholds) {
  const projectRuns = allRuns.filter(run => matchesProject(run.project, project));
  const projectRoutes = allRoutes.filter(route => matchesProject(route.project, project));
  const projectStabilityRows = allStabilityRows.filter(item => matchesProject(item.project, project));
  const projectCruxRows = allCruxRows.filter(item => matchesProject(item.project, project));
  const sprintConfig = readSprintMetadata(sheet);
  const filters = readDashboardFilters(sheet, project, projectRuns, projectRoutes, sprintConfig);
  const mode = normalizeDashboardMode_(filters.mode);

  clearDashboardRenderArea(sheet);
  prepareDashboardControls(sheet, project, filters, projectRuns, sprintConfig);

  if (!projectRuns.length) {
    showEmptyMessage(sheet, project);
    return;
  }

  const runs = applyRunFilters(projectRuns, filters, sprintConfig);
  const routes = applyRouteFilters(projectRoutes, filters, sprintConfig);
  const stabilityRows = applyStabilityFilters(projectStabilityRows, filters);
  const effectiveRuns = runs.length ? runs : projectRuns;
  const effectiveRoutes = routes.length ? routes : projectRoutes;
  const effectiveStabilityRows = stabilityRows.length ? stabilityRows : projectStabilityRows;

  const stabilityMap = buildStabilityMap(effectiveStabilityRows);
  const latest = getLatestRunForFilters(effectiveRuns, filters, sprintConfig) || projectRuns[projectRuns.length - 1];
  const previous = effectiveRuns.length > 1 ? effectiveRuns[effectiveRuns.length - 2] : (projectRuns.length > 1 ? projectRuns[projectRuns.length - 2] : null);
  const trendRuns = effectiveRuns.slice(-10);
  const context = buildContextMetrics(project, filters, latest, effectiveRuns, effectiveRoutes, sprintConfig);

  if (mode === 'SPRINT') {
    renderContextOverviewBlock(sheet, LAYOUT.CONTEXT.row, context, thresholds);
    renderAlertsBlock(sheet, LAYOUT.ALERTS.row, context.latest, previous, effectiveRoutes, projectRoutes, effectiveStabilityRows, thresholds, 'БЛОК 2 — АЛЕРТЫ');
    renderSprintImpactBlock(sheet, LAYOUT.SPRINT_IMPACT.row, project, filters, effectiveRuns, projectRoutes, thresholds, 'БЛОК 3 — SPRINT IMPACT');
    renderTrendBlock(sheet, LAYOUT.TREND.row, trendRuns, effectiveStabilityRows, effectiveRoutes);
    renderWorstPagesBlock(sheet, LAYOUT.WORST_PAGES.row, effectiveRoutes, thresholds, 'БЛОК 4 — ХУДШИЕ СТРАНИЦЫ');
    renderDeviceSplitBlock(sheet, LAYOUT.DEVICE_SPLIT.row, effectiveRoutes, thresholds, 'БЛОК 5 — DESKTOP VS MOBILE');
    renderDiagnosticsBlock(sheet, LAYOUT.DIAGNOSTICS.row, context.latest, thresholds);
    renderRouteHealthBlock(sheet, LAYOUT.ROUTE_HEALTH.row, effectiveRoutes, projectRoutes, stabilityMap, thresholds);
    renderMetricBreakdownBlock(sheet, LAYOUT.METRIC_BREAKDOWN.row, projectRuns, projectRoutes, thresholds, sprintConfig);
    return;
  }

  renderContextOverviewBlock(sheet, LAYOUT.CONTEXT.row, context, thresholds);
  renderAlertsBlock(sheet, LAYOUT.ALERTS.row, context.latest, previous, effectiveRoutes, projectRoutes, effectiveStabilityRows, thresholds, 'БЛОК 2 — АЛЕРТЫ');
  renderCruxReferenceBlock(sheet, LAYOUT.CRUX_REF.row, context.latest, projectCruxRows);
  renderOverviewBlock(sheet, LAYOUT.OVERVIEW.row, context.latest, thresholds);
  if (shouldRenderCrossEnvBlock(filters)) {
    renderCrossEnvComparisonBlock(sheet, LAYOUT.CROSS_ENV.row, project, filters, effectiveRuns, effectiveRoutes, thresholds, 'БЛОК 3 — СРЕЗ ПО КОНТУРАМ');
  }
  renderTrendBlock(sheet, LAYOUT.TREND.row, trendRuns, effectiveStabilityRows, effectiveRoutes);
  renderWorstPagesBlock(sheet, LAYOUT.WORST_PAGES.row, effectiveRoutes, thresholds, 'БЛОК 6 — ХУДШИЕ СТРАНИЦЫ');
  renderDeviceSplitBlock(sheet, LAYOUT.DEVICE_SPLIT.row, effectiveRoutes, thresholds, 'БЛОК 7 — DESKTOP VS MOBILE');
  renderDiagnosticsBlock(sheet, LAYOUT.DIAGNOSTICS.row, context.latest, thresholds);
  renderRouteHealthBlock(sheet, LAYOUT.ROUTE_HEALTH.row, effectiveRoutes, projectRoutes, stabilityMap, thresholds);
  if (mode === 'EXPERIMENT') {
    renderExperimentsBlock(sheet, LAYOUT.EXPERIMENTS.row, effectiveRuns, thresholds);
  }
}

function readSprintMetadata(sheet) {
  const rollout = {
    DEV: safeReadCell_(sheet, SPRINT_METADATA_CELLS.devDone) === true,
    TEST: safeReadCell_(sheet, SPRINT_METADATA_CELLS.testDone) === true,
    STAGE: safeReadCell_(sheet, SPRINT_METADATA_CELLS.stageDone) === true,
    PROD: safeReadCell_(sheet, SPRINT_METADATA_CELLS.prodDone) === true,
  };
  const checkedCount = Object.values(rollout).filter(Boolean).length;
  const currentSprint = toText(safeReadCell_(sheet, SPRINT_METADATA_CELLS.currentSprint)).trim();
  const previousIncrement = toText(safeReadCell_(sheet, SPRINT_METADATA_CELLS.nextSprint)).trim();
  const hasAnyRollout = checkedCount > 0;
  return {
    currentSprint,
    previousIncrement,
    rollout,
    checkedCount,
    hasAnyRollout,
    activeSprint: currentSprint || previousIncrement,
  };
}

function normalizeDashboardMode_(value) {
  const text = toText(value).trim().toUpperCase();
  if (text === 'SPRINT VIEW') return 'SPRINT';
  if (text === 'ENVIRONMENT VIEW') return 'ENVIRONMENT';
  if (text === 'ROUTE CROSS-ENV') return 'ROUTE_CROSS_ENV';
  if (text === 'EXPERIMENT') return 'EXPERIMENT';
  return 'ENVIRONMENT';
}

function getSprintTagForEnvironment_(environment, sprintConfig) {
  if (!sprintConfig || !sprintConfig.hasAnyRollout) {
    return '';
  }
  const env = normalizeEnvironment(environment);
  return sprintConfig.rollout[env] ? 'after' : 'before';
}

function matchesSprintContext_(record, sprintConfig) {
  if (!sprintConfig || !sprintConfig.activeSprint) {
    return true;
  }
  if (toText(record.sprint).trim() !== sprintConfig.activeSprint) {
    return false;
  }
  if (!sprintConfig.hasAnyRollout) {
    return true;
  }
  // Поддержка составных тегов: "after,Regress" содержит "after"
  const expectedTag = getSprintTagForEnvironment_(record.environment, sprintConfig);
  return hasTagToken_(record.tag, expectedTag);
}

function ensurePerfAnalyticsTriggers(ss) {
  const handler = 'updatePerfAnalytics';
  const triggers = ScriptApp.getProjectTriggers();
  triggers
    .filter(trigger => trigger.getHandlerFunction() === handler && trigger.getEventType() === ScriptApp.EventType.ON_EDIT)
    .forEach(trigger => ScriptApp.deleteTrigger(trigger));
  triggers
    .filter(trigger => trigger.getHandlerFunction() === 'handleDashboardButtonEdit')
    .forEach(trigger => ScriptApp.deleteTrigger(trigger));
  triggers
    .filter(trigger => trigger.getHandlerFunction() === handler && trigger.getEventType() === ScriptApp.EventType.CLOCK)
    .forEach(trigger => ScriptApp.deleteTrigger(trigger));
}

function rebuildAnalyticsHelperSheets(ss) {
  const rawRows = collectRawPerfRows(ss);
  rebuildRunsSheet(ss, rawRows);
  rebuildRoutesSheet(ss, rawRows);
  rebuildStabilitySheet(ss, rawRows);
}

function collectRawPerfRows(ss) {
  const rows = [];
  RAW_PERF_SHEETS.forEach(sheetName => {
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      return;
    }
    const records = readSheetRecords(sheet);
    records.forEach(record => {
      const normalized = normalizeRawRecord(record, sheetName);
      if (normalized) {
        rows.push(normalized);
      }
    });
  });
  return rows;
}

function normalizeRawRecord(record, sheetName) {
  const page = toText(getRecordValue(record, ['page']));
  const device = toText(getRecordValue(record, ['device'])) || 'unknown';
  if (!page && sheetName !== 'CrUX') {
    return null;
  }
  const sheetMeta = inferMetaFromSheetName(sheetName);
  const environmentRaw = toText(getRecordValue(record, ['environment'])) || sheetMeta.environment;
  const projectRaw = toText(getRecordValue(record, ['project'])) || sheetMeta.project || inferProject(environmentRaw);
  const sourceRaw = getRecordValue(record, ['source', 'type']) || sheetMeta.source;
  return {
    date: toText(getRecordValue(record, ['date'])),
    project: normalizeProject(projectRaw),
    environment: normalizeEnvironment(environmentRaw),
    source: normalizeSource(sourceRaw),
    sprint: toText(getRecordValue(record, ['sprint'])),
    runId: toText(getRecordValue(record, ['run_id'])),
    tag: toText(getRecordValue(record, ['tag'])),
    iterations: parseNumber(getRecordValue(record, ['iterations'])) || inferIterationsFromType(getRecordValue(record, ['type'])) || (sheetName === 'CrUX' ? 1 : null),
    page,
    device,
    type: ROUTE_TYPE_MAP[page] || 'route',
    avgScore: parseNumber(getRecordValue(record, ['p', 'avg_score', 'score'])),
    lcp: normalizeTiming(getRecordValue(record, ['lcp_p90', 'p90_lcp', 'lcp']), 'lcp'),
    inp: normalizeTiming(getRecordValue(record, ['inp_p90', 'p90_inp', 'inp']), 'inp'),
    cls: parseNumber(getRecordValue(record, ['cls_p90', 'p90_cls', 'cls'])),
    ttfb: normalizeTiming(getRecordValue(record, ['ttfb', 'avg_ttfb', 'ttfb_avg']), 'ttfb'),
    tbt: normalizeTiming(getRecordValue(record, ['tbt', 'total_blocking_time']), 'tbt'),
    fcp: normalizeTiming(getRecordValue(record, ['fcp', 'first_contentful_paint']), 'fcp'),
    tti: normalizeTiming(getRecordValue(record, ['tti', 'time_to_interactive']), 'tti'),
    speed: normalizeTiming(getRecordValue(record, ['si', 'speed', 'speed_index']), 'speed'),
  };
}

function inferMetaFromSheetName(sheetName) {
  const text = toText(sheetName).toUpperCase();
  if (text === 'CRUX') {
    return { project: '', environment: 'PROD', source: 'CRUX' };
  }
  const match = text.match(/^(VRP|VRS)\s*\[(PROD|STAGE|TEST|DEV)\]$/);
  if (!match) {
    return { project: '', environment: '', source: '' };
  }
  return { project: match[1], environment: match[2], source: '' };
}

function inferIterationsFromType(typeValue) {
  const text = toText(typeValue);
  const match = text.match(/\{(\d+)\}/);
  return match ? parseInt(match[1], 10) : null;
}

function rebuildRunsSheet(ss, rows) {
  const sheet = getOrCreateSheet(ss, RUNS_SHEET);
  const grouped = {};
  rows.forEach(row => {
    const key = [row.project, row.environment, row.source, row.sprint, row.tag, row.runId].join('|');
    if (!grouped[key]) {
      grouped[key] = [];
    }
    grouped[key].push(row);
  });
  const data = Object.values(grouped).map(group => buildRunAggregateRow(group));
  writeHelperSheet(sheet, RUNS_HEADERS, data);
}

function buildRunAggregateRow(group) {
  const sample = group[group.length - 1] || {};
  const pages = new Set(group.map(item => `${item.page}|${item.device}`)).size;
  return [
    sample.date || '',
    sample.project || '',
    sample.environment || '',
    sample.source || '',
    sample.sprint || '',
    sample.runId || '',
    sample.tag || '',
    sample.iterations || '',
    pages,
    averageNumbers(group.map(item => item.avgScore), 0),
    averageNumbers(group.map(item => item.lcp), 0),
    averageNumbers(group.map(item => item.inp), 0),
    averageNumbers(group.map(item => item.cls), 3),
    averageNumbers(group.map(item => item.ttfb), 0),
    averageNumbers(group.map(item => item.tbt), 0),
    averageNumbers(group.map(item => item.fcp), 0),
    averageNumbers(group.map(item => item.tti), 0),
    averageNumbers(group.map(item => item.speed), 0),
  ];
}

function rebuildRoutesSheet(ss, rows) {
  const sheet = getOrCreateSheet(ss, ROUTES_SHEET);
  const grouped = {};
  rows.forEach(row => {
    const key = [row.project, row.environment, row.source, row.sprint, row.tag, row.runId, row.page, row.device].join('|');
    if (!grouped[key]) {
      grouped[key] = [];
    }
    grouped[key].push(row);
  });
  const data = Object.values(grouped).map(group => buildRouteAggregateRow(group));
  writeHelperSheet(sheet, ROUTES_HEADERS, data);
}

function buildRouteAggregateRow(group) {
  const sample = group[group.length - 1] || {};
  return [
    sample.date || '',
    sample.project || '',
    sample.environment || '',
    sample.source || '',
    sample.sprint || '',
    sample.runId || '',
    sample.tag || '',
    sample.page || '',
    sample.device || '',
    sample.type || 'route',
    sample.iterations || '',
    averageNumbers(group.map(item => item.avgScore), 0),
    averageNumbers(group.map(item => item.lcp), 0),
    averageNumbers(group.map(item => item.inp), 0),
    averageNumbers(group.map(item => item.cls), 3),
    averageNumbers(group.map(item => item.ttfb), 0),
  ];
}

function rebuildStabilitySheet(ss, rows) {
  const sheet = getOrCreateSheet(ss, STABILITY_SHEET);
  const grouped = {};
  rows.forEach(row => {
    const key = [row.project, row.environment, row.source, row.page, row.device].join('|');
    if (!grouped[key]) {
      grouped[key] = [];
    }
    grouped[key].push(row);
  });
  const data = Object.values(grouped).map(group => buildStabilityAggregateRow(group));
  writeHelperSheet(sheet, STABILITY_HEADERS, data);
}

function buildStabilityAggregateRow(group) {
  const sample = group[group.length - 1] || {};
  const lcpStd = computeStdDev(group.map(item => item.lcp), 0);
  const inpStd = computeStdDev(group.map(item => item.inp), 0);
  const clsStd = computeStdDev(group.map(item => item.cls), 3);
  const stabilityScore = computeStabilityScore(lcpStd, inpStd, clsStd);
  return [
    sample.project || '',
    sample.environment || '',
    sample.source || '',
    sample.page || '',
    sample.device || '',
    lcpStd,
    inpStd,
    clsStd,
    stabilityScore,
  ];
}

function writeHelperSheet(sheet, headers, rows) {
  sheet.clearContents();
  const output = [headers].concat(rows || []);
  sheet.getRange(1, 1, output.length, headers.length).setValues(output);
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

function getOrCreateSheet(ss, name) {
  let sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
  }
  return sheet;
}

function showEmptyMessage(sheet, project) {
  clearDashboardRenderArea(sheet);
  const sprintConfig = readSprintMetadata(sheet);
  prepareDashboardControls(sheet, project, buildDefaultFilters(project, [], [], sprintConfig), [], sprintConfig);
  const prefix = project ? `${project}: ` : '';
  sheet.getRange(CONTROL_RENDER_START_ROW, 1).setValue(`${prefix}данных ещё нет, запусти проверки Lighthouse и обнови дашборд.`).setFontSize(14).setFontWeight('bold');
}

function clearDashboardRenderArea(sheet) {
  sheet.getCharts().forEach(chart => sheet.removeChart(chart));
  const maxRows = Math.max(sheet.getMaxRows() - CONTROL_RENDER_START_ROW + 1, 1);
  const maxCols = Math.max(sheet.getMaxColumns(), 40);
  sheet.getRange(CONTROL_RENDER_START_ROW, 1, maxRows, maxCols).clearContent().clearFormat();
}

function clearDashboardControlArea(sheet) {
  const controlRange = sheet.getRange(1, 1, CONTROL_RENDER_START_ROW - 1, 12);
  try {
    controlRange.breakApart();
  } catch (error) {
  }
  controlRange.clearContent().clearFormat().clearDataValidations();
}

function prepareDashboardControls(sheet, project, filters, runs, sprintConfig) {
  clearDashboardControlArea(sheet);
  const latest = runs.length ? runs[runs.length - 1] : null;
  const titleRange = sheet.getRange(1, 1, 1, 8);
  titleRange.merge();
  titleRange.setValue(`Performance QA Dashboard [${project}]`);
  titleRange.setFontWeight('bold').setFontSize(16).setBackground(BLOCK_HEADER_COLOR).setFontColor(BLOCK_HEADER_FONT_COLOR).setHorizontalAlignment('center');
  const subtitle = [`Default env: PROD`];
  if (sprintConfig && sprintConfig.currentSprint) subtitle.push(`Current sprint: ${sprintConfig.currentSprint}`);
  if (sprintConfig && sprintConfig.previousIncrement) subtitle.push(`Previous increment: ${sprintConfig.previousIncrement}`);
  if (!subtitle.length && latest && latest.sprint) subtitle.push(`Latest sprint: ${latest.sprint}`);
  sheet.getRange(2, 1, 1, 8).merge();
  sheet.getRange(2, 1).setValue(subtitle.join(' | ')).setFontStyle('italic').setFontColor('#455A64');

  const labels = ['Environment', 'Device', 'Route', 'Sprint', 'Tag', 'Mode'];
  const values = [
    filters.environment || 'PROD',
    filters.device || 'ALL',
    filters.route || 'ALL',
    filters.sprint || 'ALL',
    filters.tag || 'ALL',
    filters.mode || 'Environment View',
  ];
  sheet.getRange(4, 1, labels.length, 1).setValues(labels.map(item => [item])).setFontWeight('bold').setBackground('#ECEFF1');
  sheet.getRange(4, 2, values.length, 1).setValues(values.map(item => [item])).setBackground('#FAFAFA');

  const environments = ['PROD', 'STAGE', 'TEST', 'DEV', 'ALL'];
  const devices = ['ALL', 'mobile', 'desktop'];
  const routes = ['ALL'].concat(uniqueNonEmptyValues_(runs.map(item => item.page)).sort());
  const sprints = ['ALL'].concat(uniqueNonEmptyValues_(runs.map(item => item.sprint)).sort().reverse());
  const tags = ['ALL'].concat(uniqueNonEmptyValues_(runs.map(item => item.tag)).sort());
  const modes = ['Environment View', 'Sprint View', 'Route Cross-Env', 'Experiment'];
  applyDropdown_(sheet.getRange('B4'), environments);
  applyDropdown_(sheet.getRange('B5'), devices);
  applyDropdown_(sheet.getRange('B6'), routes.length ? routes : ['ALL']);
  applyDropdown_(sheet.getRange('B7'), sprints.length ? sprints : ['ALL']);
  applyDropdown_(sheet.getRange('B8'), tags.length ? tags : ['ALL']);
  applyDropdown_(sheet.getRange('B9'), modes);

  sheet.getRange(4, 4, 1, 4).merge();
  sheet.getRange(4, 4).setValue(`Sprint Control [${project}]`).setFontWeight('bold').setBackground('#ECEFF1');
  sheet.getRange(5, 4, 2, 1).setValues([['Current Sprint'], ['Previous Increment']]).setFontWeight('bold').setBackground('#ECEFF1');
  sheet.getRange(5, 5, 2, 1).setValues([
    [sprintConfig && sprintConfig.currentSprint ? sprintConfig.currentSprint : ''],
    [sprintConfig && sprintConfig.previousIncrement ? sprintConfig.previousIncrement : ''],
  ]).setBackground('#FAFAFA');
  sheet.getRange(8, 4, 1, 4).setValues([['DEV', 'TEST', 'STAGE', 'PROD']]).setFontWeight('bold').setBackground('#ECEFF1');
  const rolloutRange = sheet.getRange(9, 4, 1, 4);
  rolloutRange.insertCheckboxes();
  rolloutRange.setValues([[
    sprintConfig && sprintConfig.rollout && sprintConfig.rollout.DEV ? true : false,
    sprintConfig && sprintConfig.rollout && sprintConfig.rollout.TEST ? true : false,
    sprintConfig && sprintConfig.rollout && sprintConfig.rollout.STAGE ? true : false,
    sprintConfig && sprintConfig.rollout && sprintConfig.rollout.PROD ? true : false,
  ]]);
  sheet.getRange(10, 4, 1, 4).merge();
  sheet.getRange(10, 4).setValue(buildSprintSummary_(sprintConfig)).setFontStyle('italic').setFontColor('#455A64');
  sheet.getRange(11, 4, 2, 4).merge();
  sheet.getRange(11, 4).setValue('Sprint View: работаем по Current Sprint. Контур с чекбоксом = after, без чекбокса = before. Previous Increment хранится как справочный прошлый инкремент.').setWrap(true).setFontColor('#607D8B');
  sheet.getRange(13, 1, 2, 12).clearContent().clearFormat().clearDataValidations();
  sheet.getRange('D13:H14').merge();
  sheet.getRange('D13:H14').setBackground('#ECEFF1').setFontColor('#455A64').setHorizontalAlignment('center').setVerticalAlignment('middle').setFontStyle('italic');
  sheet.getRange('D13:H14').setValue('Generate Dashboard: нажми кнопку справа или используй меню QA Dashboard');
  ensureGenerateDashboardButton_(sheet);
  sheet.setFrozenRows(3);
}

function ensureGenerateDashboardButton_(sheet) {
  const anchor = GENERATE_BUTTON_ANCHOR;
  sheet.getImages()
    .filter(image => {
      const cell = image.getAnchorCell();
      return cell && cell.getRow() === anchor.row && cell.getColumn() === anchor.column;
    })
    .forEach(image => image.remove());

  const image = sheet.insertImage(
    Utilities.newBlob(Utilities.base64Decode(GENERATE_BUTTON_PNG_BASE64), 'image/png', 'generate-dashboard.png'),
    anchor.column,
    anchor.row,
    anchor.offsetX,
    anchor.offsetY,
  );
  image.assignScript('updatePerfAnalytics');
  image.setWidth(anchor.width);
  image.setHeight(anchor.height);
}

function buildSprintSummary_(sprintConfig) {
  if (!sprintConfig) {
    return 'Sprint context is empty.';
  }
  if (!sprintConfig.hasAnyRollout) {
    return `Active sprint: ${sprintConfig.currentSprint || '—'} | rollout не начат`;
  }
  return `Active sprint: ${sprintConfig.currentSprint || '—'} | rollout progress: ${sprintConfig.checkedCount}/4`;
}

function applyDropdown_(range, values) {
  const rule = SpreadsheetApp.newDataValidation()
    .requireValueInList(values, true)
    .setAllowInvalid(true)
    .build();
  range.setDataValidation(rule);
}

function uniqueNonEmptyValues_(values) {
  return Array.from(new Set(values.map(toText).map(item => item.trim()).filter(Boolean)));
}

function shouldRenderCrossEnvBlock(filters) {
  const mode = normalizeDashboardMode_(filters.mode);
  const environment = toText(filters.environment).trim().toUpperCase();
  if (mode === 'ENVIRONMENT') {
    return !environment || environment === 'ALL';
  }
  return mode === 'SPRINT' || mode === 'ROUTE_CROSS_ENV' || mode === 'EXPERIMENT';
}

function getPerfSpreadsheet() {
  const active = SpreadsheetApp.getActiveSpreadsheet();
  if (active) {
    return active;
  }
  const spreadsheetId = getPerfConfiguredSpreadsheetId();
  if (!spreadsheetId) {
    throw new Error(
      'Не удалось получить Spreadsheet для дашборда. Установи GS_SHEET_ID/SHEET_ID в свойствах скрипта.'
    );
  }
  return SpreadsheetApp.openById(spreadsheetId);
}

function getPerfConfiguredSpreadsheetId() {
  const scriptProps = PropertiesService.getScriptProperties();
  for (const key of PERF_SHEET_ID_KEYS) {
    const value = scriptProps.getProperty(key);
    if (value) {
      return value;
    }
  }
  const docProps = PropertiesService.getDocumentProperties();
  for (const key of PERF_SHEET_ID_KEYS) {
    const value = docProps.getProperty(key);
    if (value) {
      return value;
    }
  }
  return null;
}

function autoSizeColumns(sheet) {
  DASHBOARD_COLUMN_WIDTHS.forEach((width, index) => sheet.setColumnWidth(index + 1, width));
  const extraCols = 5;
  for (let i = DASHBOARD_COLUMN_WIDTHS.length + 1; i <= DASHBOARD_COLUMN_WIDTHS.length + extraCols; i++) {
    sheet.setColumnWidth(i, 120);
  }
  sheet.getRange(1, 1, 1, DASHBOARD_COLUMN_WIDTHS.length).setWrap(true);
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
  const environmentRaw = toText(getRecordValue(record, ['environment']));
  const projectRaw = toText(getRecordValue(record, ['project'])) || inferProject(environmentRaw);
  const environment = normalizeEnvironment(environmentRaw);
  const source = normalizeSource(getRecordValue(record, ['source', 'type']));
  return {
    runId,
    date,
    project: normalizeProject(projectRaw),
    environment,
    source,
    sprint: toText(getRecordValue(record, ['sprint'])),
    tag: toText(getRecordValue(record, ['tag'])),
    iterations: parseNumber(getRecordValue(record, ['iterations'])),
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

function inferProject(environment) {
  const text = toText(environment).toUpperCase();
  if (text.startsWith('VRP')) return 'VRP';
  if (text.startsWith('VRS')) return 'VRS';
  return '';
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

function matchesProject(value, project) {
  return normalizeProject(value) === normalizeProject(project);
}

function parseRouteRecord(record) {
  const page = toText(getRecordValue(record, ['page']));
  if (!page) {
    return null;
  }
  const device = toText(getRecordValue(record, ['device'])) || 'unknown';
  const environmentRaw = toText(getRecordValue(record, ['environment']));
  return {
    page,
    device,
    project: normalizeProject(toText(getRecordValue(record, ['project'])) || inferProject(environmentRaw)),
    environment: normalizeEnvironment(environmentRaw),
    source: normalizeSource(getRecordValue(record, ['source', 'type'])),
    sprint: toText(getRecordValue(record, ['sprint'])),
    runId: toText(getRecordValue(record, ['run_id'])),
    tag: toText(getRecordValue(record, ['tag'])),
    iterations: parseNumber(getRecordValue(record, ['iterations'])),
    avgScore: parseNumber(getRecordValue(record, ['avg_score'])),
    lcp: normalizeTiming(getRecordValue(record, ['p90_lcp', 'lcp_p90', 'lcp']), 'lcp'),
    inp: normalizeTiming(getRecordValue(record, ['p90_inp', 'inp_p90', 'inp']), 'inp'),
    cls: parseNumber(getRecordValue(record, ['p90_cls', 'cls_p90', 'cls'])),
    ttfb: normalizeTiming(getRecordValue(record, ['ttfb', 'avg_ttfb', 'ttfb_avg']), 'ttfb'),
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
  const environmentRaw = toText(getRecordValue(record, ['environment']));
  const project = normalizeProject(toText(getRecordValue(record, ['project'])) || inferProject(environmentRaw));
  const environment = normalizeEnvironment(environmentRaw);
  const source = normalizeSource(getRecordValue(record, ['source', 'type']));
  const deviceKey = device.toLowerCase();
  return {
    page,
    device,
    project,
    environment,
    source,
    key: buildStabilityKey(project, environment, source, page, deviceKey),
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

function buildStabilityKey(project, environment, source, page, device) {
  return [normalizeProject(project), normalizeEnvironment(environment), normalizeSource(source), toText(page), toText(device).toLowerCase()].join('|');
}

function loadMetricThresholds(ss) {
  if (!ss) {
    return populateFallbackThresholds({});
  }
  const sheet = ss.getSheetByName(DASHBOARD_CONFIG_SHEET);
  const metrics = {};
  if (!sheet) {
    return populateFallbackThresholds(metrics);
  }
  const values = sheet.getDataRange().getValues();
  if (!values.length) {
    return populateFallbackThresholds(metrics);
  }
  const headers = values[0].map(normalizeHeader);
  const metricIdx = findHeaderIndex(headers, ['metric']);
  const goodIdx = findHeaderIndex(headers, ['good', 'good_', 'good__', 'good_threshold', 'green', 'green_threshold', 'expected']);
  const poorIdx = findHeaderIndex(headers, ['poor', 'poor_', 'poor__', 'poor_threshold', 'red', 'red_threshold', 'bad']);
  const directionIdx = findHeaderIndex(headers, ['direction', 'trend', 'mode']);
  if (metricIdx === -1 || goodIdx === -1 || poorIdx === -1) {
    return populateFallbackThresholds(metrics);
  }
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
      direction: directionIdx !== -1 && row[directionIdx] ? row[directionIdx].toString().trim().toLowerCase() : 'low_good',
    };
  }
  return populateFallbackThresholds(metrics);
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

function populateFallbackThresholds(base) {
  const result = Object.assign({}, base);
  const fromConfig = Object.keys(base);
  const fromFallback = [];
  DEFAULT_METRIC_FALLBACKS.forEach(fallback => {
    const key = normalizeHeader(fallback.metric);
    if (!result[key]) {
      result[key] = {
        good: fallback.good,
        poor: fallback.poor,
        direction: fallback.direction,
      };
      fromFallback.push(key);
    }
  });
  if (fromConfig.length) {
    Logger.log('[Thresholds] Из Config sheet: ' + fromConfig.join(', '));
  }
  if (fromFallback.length) {
    Logger.log('[Thresholds] Из DEFAULT_METRIC_FALLBACKS (не найдены в Config): ' + fromFallback.join(', '));
  }
  return result;
}

function colorMetricCell_(sheet, row, column, metricKey, value, thresholds) {
  const status = assessMetricStatus(metricKey, value, thresholds);
  sheet.getRange(row, column).setBackground(status.color);
  return status;
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

function renderTitleBlockLegacy(sheet, row, project, latest) {
  const range = sheet.getRange(row, 1, 1, 6);
  range.merge();
  range.setValue(`Performance QA Dashboard [${project}]`);
  range.setFontWeight('bold');
  range.setFontSize(16);
  range.setBackground(BLOCK_HEADER_COLOR);
  range.setFontColor(BLOCK_HEADER_FONT_COLOR);
  range.setHorizontalAlignment('center');
  sheet.setRowHeight(row, 32);
  const subtitle = [`Project: ${project}`];
  if (latest && latest.environment) subtitle.push(`Env: ${latest.environment}`);
  if (latest && latest.source) subtitle.push(`Source: ${latest.source}`);
  if (latest && latest.sprint) subtitle.push(`Sprint: ${latest.sprint}`);
  sheet.getRange(row + 1, 1, 1, 8).merge();
  sheet.getRange(row + 1, 1).setValue(subtitle.join(' | ')).setFontStyle('italic').setFontColor('#455A64');
  return row + 3;
}

function readDashboardFilters(sheet, project, runs, routes, sprintConfig) {
  const defaults = buildDefaultFilters(project, runs, routes, sprintConfig);
  const filterMap = [
    ['environment', 'B4'],
    ['device', 'B5'],
    ['route', 'B6'],
    ['sprint', 'B7'],
    ['tag', 'B8'],
    ['mode', 'B9'],
  ];
  const result = Object.assign({}, defaults);
  filterMap.forEach(([key, cell]) => {
    const value = safeReadCell_(sheet, cell);
    if (value) {
      result[key] = value.toString().trim();
    }
  });
  return result;
}

function buildDefaultFilters(project, runs, routes, sprintConfig) {
  const latest = runs[runs.length - 1] || {};
  return {
    project,
    environment: latest.environment || 'PROD',
    device: 'ALL',
    route: 'ALL',
    sprint: (sprintConfig && sprintConfig.activeSprint) || latest.sprint || 'ALL',
    tag: 'ALL',
    source: 'ALL',
    mode: 'Environment View',
  };
}

function safeReadCell_(sheet, a1) {
  try {
    return sheet.getRange(a1).getValue();
  } catch (error) {
    return '';
  }
}

function filterMatchesValue(actual, expected) {
  const wanted = toText(expected).trim();
  if (!wanted || wanted.toUpperCase() === 'ALL') {
    return true;
  }
  return toText(actual).trim().toUpperCase() === wanted.toUpperCase();
}

function applyRunFilters(runs, filters, sprintConfig) {
  const mode = normalizeDashboardMode_(filters.mode);
  return runs.filter(run => {
    if (!filterMatchesValue(run.source, filters.source)) {
      return false;
    }
    if (mode === 'SPRINT') {
      return matchesSprintContext_(run, sprintConfig);
    }
    if (mode === 'ENVIRONMENT') {
      return filterMatchesValue(run.environment, filters.environment);
    }
    return filterMatchesValue(run.environment, filters.environment)
      && filterMatchesValue(run.sprint, filters.sprint)
      && filterMatchesValue(run.tag, filters.tag);
  });
}

function applyRouteFilters(routes, filters, sprintConfig) {
  const mode = normalizeDashboardMode_(filters.mode);
  return routes.filter(route => {
    if (!filterMatchesValue(route.source, filters.source)) {
      return false;
    }
    if (!filterMatchesValue(route.device, filters.device)) {
      return false;
    }
    if (!filterMatchesValue(route.page, filters.route)) {
      return false;
    }
    if (mode === 'SPRINT') {
      return matchesSprintContext_(route, sprintConfig);
    }
    if (mode === 'ENVIRONMENT') {
      return filterMatchesValue(route.environment, filters.environment);
    }
    return filterMatchesValue(route.environment, filters.environment)
      && filterMatchesValue(route.sprint, filters.sprint)
      && filterMatchesValue(route.tag, filters.tag);
  });
}

function applyStabilityFilters(records, filters) {
  return records.filter(item => {
    return filterMatchesValue(item.environment, filters.environment)
      && filterMatchesValue(item.source, filters.source)
      && filterMatchesValue(item.device, filters.device)
      && filterMatchesValue(item.page, filters.route);
  });
}

function getLatestRunForFilters(runs, filters, sprintConfig) {
  if (!runs.length) {
    return null;
  }
  if (normalizeDashboardMode_(filters.mode) === 'SPRINT') {
    const scoped = runs.filter(run => matchesSprintContext_(run, sprintConfig));
    return scoped.length ? scoped[scoped.length - 1] : null;
  }
  return runs[runs.length - 1];
}

function buildContextMetrics(project, filters, latestRun, runs, routes, sprintConfig) {
  const latest = Object.assign({}, latestRun || {});
  if (routes.length) {
    const metrics = aggregateRouteMetrics(routes);
    if (metrics.lcp !== null) latest.lcp = metrics.lcp;
    if (metrics.inp !== null) latest.inp = metrics.inp;
    if (metrics.cls !== null) latest.cls = metrics.cls;
    if (metrics.ttfb !== null) latest.ttfb = metrics.ttfb;
    latest.device = filters.device;
    latest.page = filters.route;
  }
  latest.project = project;
  latest.environment = normalizeDashboardMode_(filters.mode) === 'SPRINT'
    ? 'ALL'
    : (filters.environment || latest.environment || 'ALL');
  latest.source = filters.source || latest.source || 'ALL';
  latest.sprint = normalizeDashboardMode_(filters.mode) === 'SPRINT'
    ? ((sprintConfig && sprintConfig.activeSprint) || latest.sprint || 'ALL')
    : (filters.sprint || latest.sprint || 'ALL');
  latest.tag = normalizeDashboardMode_(filters.mode) === 'SPRINT'
    ? 'rollout-based'
    : (filters.tag || latest.tag || 'ALL');
  latest.iterations = latest.iterations || 0;
  return { latest };
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

function aggregateRouteMetrics(routes) {
  if (!routes.length) {
    return { avgScore: null, lcp: null, inp: null, cls: null, ttfb: null };
  }
  const acc = routes.reduce((state, route) => {
    if (route.avgScore !== null && route.avgScore !== undefined) {
      state.avgScore += route.avgScore;
      state.avgScoreCount += 1;
    }
    if (route.lcp) {
      state.lcp += route.lcp;
      state.lcpCount += 1;
    }
    if (route.inp) {
      state.inp += route.inp;
      state.inpCount += 1;
    }
    if (route.cls !== null && route.cls !== undefined) {
      state.cls += route.cls;
      state.clsCount += 1;
    }
    if (route.ttfb) {
      state.ttfb += route.ttfb;
      state.ttfbCount += 1;
    }
    return state;
  }, { avgScore: 0, lcp: 0, inp: 0, cls: 0, ttfb: 0, avgScoreCount: 0, lcpCount: 0, inpCount: 0, clsCount: 0, ttfbCount: 0 });
  return {
    avgScore: acc.avgScoreCount ? Math.round(acc.avgScore / acc.avgScoreCount) : null,
    lcp: acc.lcpCount ? Math.round(acc.lcp / acc.lcpCount) : null,
    inp: acc.inpCount ? Math.round(acc.inp / acc.inpCount) : null,
    cls: acc.clsCount ? parseFloat((acc.cls / acc.clsCount).toFixed(3)) : null,
    ttfb: acc.ttfbCount ? Math.round(acc.ttfb / acc.ttfbCount) : null,
  };
}

function normalizeMetricForChart_(metricKey, value, thresholds) {
  const num = parseNumber(value);
  if (num === null) {
    return 0;
  }
  const config = thresholds[normalizeHeader(metricKey)];
  if (!config) {
    return num;
  }
  const good = parseNumber(config.good);
  const poor = parseNumber(config.poor);
  const direction = config.direction || 'low_good';
  if (good === null || poor === null || good === poor) {
    return num;
  }
  if (direction === 'high_good') {
    if (num >= good) return 100;
    if (num <= poor) return 0;
    return Math.round(((num - poor) / (good - poor)) * 100);
  }
  if (num <= good) return 100;
  if (num >= poor) return 0;
  return Math.round(((poor - num) / (poor - good)) * 100);
}

function renderFilterPanelLegacy(sheet, row, filters, runs, routes) {
  row = renderBlockHeader(sheet, row, 'BLOCK 1 — FILTER PANEL', 4);
  const latestSprint = filters.sprint || 'ALL';
  const rows = [
    ['Environment', filters.environment || 'ALL'],
    ['Device', filters.device || 'ALL'],
    ['Route', filters.route || 'ALL'],
    ['Sprint', latestSprint || 'ALL'],
    ['Tag', filters.tag || 'ALL'],
    ['Source', filters.source || 'ALL'],
    ['Mode', filters.mode || 'Environment View'],
  ];
  sheet.getRange(row, 1, rows.length, 2).setValues(rows);
  sheet.getRange(row, 1, rows.length, 1).setFontWeight('bold').setBackground('#ECEFF1');
  sheet.getRange(row, 2, rows.length, 1).setBackground('#FAFAFA');
  sheet.getRange('D5').setValue('Допустимо: ALL или точное значение из raw-данных').setFontStyle('italic').setFontColor('#607D8B');
  return row + rows.length + 1;
}

function renderContextOverviewBlock(sheet, row, context, thresholds) {
  const startRow = row;
  row = renderBlockHeader(sheet, row, 'BLOCK 2 — CONTEXT OVERVIEW', 4);
  const latest = context.latest || {};
  const selected = [
    latest.environment || 'ALL',
    latest.source || 'ALL',
    latest.sprint || 'ALL',
    latest.tag || 'ALL',
  ].join(' / ');
  sheet.getRange(row, 1, 1, 4).merge();
  sheet.getRange(row, 1).setValue(`Selected: ${selected}`);
  sheet.getRange(row, 1).setFontWeight('bold');
  row++;
  sheet.getRange(row, 1, 1, 3).setValues([['Metric', 'Value', 'Status']]).setFontWeight('bold').setBackground('#ECEFF1');
  row++;
  [
    { label: 'LCP p90', key: 'lcp', value: latest.lcp },
    { label: 'INP p90', key: 'inp', value: latest.inp },
    { label: 'CLS p90', key: 'cls', value: latest.cls },
    { label: 'TTFB avg', key: 'ttfb', value: latest.ttfb },
  ].forEach(item => {
    const status = assessMetricStatus(item.key, item.value, thresholds);
    sheet.getRange(row, 1, 1, 3).setValues([[item.label, formatMetricValue(item.key, item.value), status.status]]);
    sheet.getRange(row, 3).setBackground(status.color);
    row++;
  });
  return startRow + LAYOUT.CONTEXT.height;
}

function buildCrossEnvRows(project, filters, runs, routes) {
  const envOrder = ['DEV', 'TEST', 'STAGE', 'PROD'];
  const baseRoutes = routes.filter(route => {
    return filterMatchesValue(route.source, filters.source)
      && filterMatchesValue(route.device, filters.device)
      && filterMatchesValue(route.page, filters.route)
      && filterMatchesValue(route.sprint, filters.sprint)
      && filterMatchesValue(route.tag, filters.tag);
  });
  const baseRuns = runs.filter(run => {
    return filterMatchesValue(run.source, filters.source)
      && filterMatchesValue(run.sprint, filters.sprint)
      && filterMatchesValue(run.tag, filters.tag);
  });
  const rows = envOrder.map(environment => {
    const envRoutes = baseRoutes.filter(route => route.environment === environment);
    const envRuns = baseRuns.filter(run => run.environment === environment);
    const routeMetrics = aggregateRouteMetrics(envRoutes);
    const latestRun = envRuns.length ? envRuns[envRuns.length - 1] : null;
    return {
      environment,
      lcp: routeMetrics.lcp !== null ? routeMetrics.lcp : (latestRun ? latestRun.lcp : null),
      inp: routeMetrics.inp !== null ? routeMetrics.inp : (latestRun ? latestRun.inp : null),
      cls: routeMetrics.cls !== null ? routeMetrics.cls : (latestRun ? latestRun.cls : null),
      ttfb: routeMetrics.ttfb !== null ? routeMetrics.ttfb : (latestRun ? latestRun.ttfb : null),
    };
  }).filter(item => item.lcp !== null || item.inp !== null || item.cls !== null || item.ttfb !== null);

  let previousLcp = null;
  rows.forEach(row => {
    row.delta = metricDelta(row.lcp, previousLcp);
    if (row.lcp !== null) {
      previousLcp = row.lcp;
    }
  });
  return rows;
}

function buildCrossEnvDeviceRows(filters, runs, routes, sprintConfig) {
  const envOrder = ['DEV', 'TEST', 'STAGE', 'PROD'];
  const deviceOrder = ['desktop', 'mobile'];
  const scopedRoutes = routes.filter(route => {
    if (!filterMatchesValue(route.source, filters.source)) {
      return false;
    }
    if (!filterMatchesValue(route.page, filters.route)) {
      return false;
    }
    return matchesSprintContext_(route, sprintConfig);
  });
  const scopedRuns = runs.filter(run => {
    if (!filterMatchesValue(run.source, filters.source)) {
      return false;
    }
    return matchesSprintContext_(run, sprintConfig);
  });

  const rows = [];
  envOrder.forEach(environment => {
    deviceOrder.forEach(device => {
      const envDeviceRoutes = scopedRoutes.filter(route => route.environment === environment && route.device.toLowerCase() === device);
      if (!envDeviceRoutes.length) {
        return;
      }
      const metrics = aggregateRouteMetrics(envDeviceRoutes);
      const runIds = uniqueNonEmptyValues_(envDeviceRoutes.map(item => item.runId));
      const pages = uniqueNonEmptyValues_(envDeviceRoutes.map(item => item.page));
      const sources = summarizeList_(envDeviceRoutes.map(item => item.source), 3);
      rows.push({
        environment,
        device,
        incrementStatus: sprintConfig.rollout[environment] ? 'размещён' : 'не размещён',
        tag: getSprintTagForEnvironment_(environment, sprintConfig) || '—',
        score: metrics.avgScore,
        lcp: metrics.lcp,
        inp: metrics.inp,
        cls: metrics.cls,
        ttfb: metrics.ttfb,
        pagesCount: pages.length,
        runsCount: runIds.length || scopedRuns.filter(run => run.environment === environment).length,
        sources,
        note: `среднее по ${pages.length} стр. / ${runIds.length || 1} зап.`,
      });
    });
  });
  return rows;
}

function renderCrossEnvComparisonBlock(sheet, row, project, filters, allRuns, allRoutes, thresholds, title) {
  const blockTop = row;
  row = renderBlockHeader(sheet, row, title || 'БЛОК 3 — СРЕЗ ПО КОНТУРАМ', 6);
  const sprintConfig = readSprintMetadata(sheet);
  const isSprintMode = normalizeDashboardMode_(filters.mode) === 'SPRINT';
  const rows = isSprintMode
    ? buildCrossEnvDeviceRows(filters, allRuns, allRoutes, sprintConfig)
    : buildCrossEnvRows(project, filters, allRuns, allRoutes);
  if (!rows.length) {
    sheet.getRange(row, 1).setValue('Нет данных для cross-env сравнения по текущему фильтру.');
    return blockTop + LAYOUT.CROSS_ENV.height;
  }
  const headers = isSprintMode
    ? ['Контур', 'Устройство', 'Инкремент', 'Тег', 'P', 'LCP', 'INP', 'CLS', 'TTFB', 'Страниц', 'Запусков', 'Источник']
    : ['Контур', 'LCP', 'INP', 'CLS', 'TTFB', 'Δ LCP'];
  sheet.getRange(row, 1, 1, headers.length).setValues([headers]).setFontWeight('bold').setBackground('#ECEFF1');
  row++;
  const sprintBlockStartRow = row;
  rows.forEach(item => {
    if (isSprintMode) {
      sheet.getRange(row, 1, 1, 12).setValues([[
        item.environment,
        item.device,
        item.incrementStatus,
        item.tag,
        item.score !== null ? item.score : '—',
        item.lcp || '—',
        item.inp || '—',
        item.cls !== null ? item.cls : '—',
        item.ttfb || '—',
        item.pagesCount,
        item.runsCount,
        item.sources,
      ]]);
      colorMetricCell_(sheet, row, 5, 'p', item.score, thresholds);
      colorMetricCell_(sheet, row, 6, 'lcp', item.lcp, thresholds);
      colorMetricCell_(sheet, row, 7, 'inp', item.inp, thresholds);
      colorMetricCell_(sheet, row, 8, 'cls', item.cls, thresholds);
      colorMetricCell_(sheet, row, 9, 'ttfb', item.ttfb, thresholds);
    } else {
      sheet.getRange(row, 1, 1, 6).setValues([[item.environment, item.lcp || '—', item.inp || '—', item.cls !== null ? item.cls : '—', item.ttfb || '—', item.delta !== null ? formatPercent(item.delta) : '—']]);
      colorMetricCell_(sheet, row, 2, 'lcp', item.lcp, thresholds);
      colorMetricCell_(sheet, row, 3, 'inp', item.inp, thresholds);
      colorMetricCell_(sheet, row, 4, 'cls', item.cls, thresholds);
      colorMetricCell_(sheet, row, 5, 'ttfb', item.ttfb, thresholds);
    }
    row++;
  });
  if (isSprintMode) {
    const summaryText = `Комментарий: значения по строке считаются отдельно для пары "контур + устройство". В расчёт вошли только данные текущего Sprint View, число страниц и запусков указано в строке.`;
    sheet.getRange(row, 1, 1, 12).merge();
    sheet.getRange(row, 1).setValue(summaryText).setWrap(true).setFontStyle('italic').setFontColor('#546E7A');
    row++;
    const chartData = [['Срез', 'P', 'LCP', 'INP', 'CLS', 'TTFB']];
    rows.forEach(item => {
      chartData.push([
        `${item.environment}-${item.device}`,
        normalizeMetricForChart_('p', item.score, thresholds),
        normalizeMetricForChart_('lcp', item.lcp, thresholds),
        normalizeMetricForChart_('inp', item.inp, thresholds),
        normalizeMetricForChart_('cls', item.cls, thresholds),
        normalizeMetricForChart_('ttfb', item.ttfb, thresholds),
      ]);
    });
    const helperRow = blockTop;
    const helperRange = sheet.getRange(helperRow, HELPER_COLUMN_PRIMARY, chartData.length, 6);
    helperRange.setValues(chartData);
    insertGroupedBarChart(sheet, helperRange, CHART_ZONES.CROSS_ENV.row, CHART_ZONES.CROSS_ENV.col, 'Метрики по устройствам (0-100)');
  }
  if (!isSprintMode) {
    const chartData = [['Environment', 'LCP']];
    rows.forEach(item => chartData.push([item.environment, item.lcp || 0]));
    const helperRow = blockTop;
    const helperRange = sheet.getRange(helperRow, HELPER_COLUMN_PRIMARY, chartData.length, 2);
    helperRange.setValues(chartData);
    insertColumnChart(sheet, helperRange, CHART_ZONES.CROSS_ENV.row, CHART_ZONES.CROSS_ENV.col, 'Cross-env LCP');
  }
  return blockTop + LAYOUT.CROSS_ENV.height;
}

function findLatestCruxForProject(project, cruxRows) {
  const projectRows = cruxRows.filter(row => matchesProject(row.project, project) && normalizeEnvironment(row.environment) === 'PROD');
  return projectRows.length ? projectRows[projectRows.length - 1] : null;
}

function renderCruxReferenceBlock(sheet, row, latest, cruxRows) {
  const startRow = row;
  if (!latest || normalizeEnvironment(latest.environment) !== 'PROD') {
    return startRow + LAYOUT.CRUX_REF.height;
  }
  const crux = findLatestCruxForProject(latest.project, cruxRows);
  if (!crux) {
    return startRow + LAYOUT.CRUX_REF.height;
  }
  row = renderBlockHeader(sheet, row, 'БЛОК 3 — LAB VS FIELD (CrUX 28D)', 4);
  sheet.getRange(row, 1, 1, 4).setValues([['Метрика', 'LAB current', 'FIELD 28d', 'Delta']]).setFontWeight('bold').setBackground('#ECEFF1');
  row++;
  const rows = [
    ['LCP', latest.lcp, crux.lcp],
    ['INP', latest.inp, crux.inp],
    ['CLS', latest.cls, crux.cls],
    ['TTFB', latest.ttfb, crux.ttfb],
  ];
  rows.forEach(item => {
    const delta = metricDelta(item[1], item[2]);
    sheet.getRange(row, 1, 1, 4).setValues([[item[0], formatMetricValue(item[0], item[1]), formatMetricValue(item[0], item[2]), delta !== null ? formatPercent(delta) : '—']]);
    row++;
  });
  return startRow + LAYOUT.CRUX_REF.height;
}

function renderBlockHeader(sheet, row, title, span = 4) {
  const range = sheet.getRange(row, 1, 1, span);
  range.merge();
  range.setValue(title);
  range.setBackground(BLOCK_HEADER_COLOR);
  range.setFontColor(BLOCK_HEADER_FONT_COLOR);
  range.setFontWeight('bold');
  range.setHorizontalAlignment('left');
  range.setVerticalAlignment('middle');
  range.setFontSize(12);
  return row + 1;
}

function renderAlertsBlock(sheet, row, latest, previous, routes, allProjectRoutes, stabilityRows, thresholds, title) {
  const startRow = row;
  row = renderBlockHeader(sheet, row, title || 'БЛОК 2 — АЛЕРТЫ', 5);
  const alerts = buildAlerts(latest, previous, routes, allProjectRoutes, stabilityRows, thresholds);
  if (!alerts.length) {
    sheet.getRange(row, 1).setValue('Нет критичных отклонений — CWV в норме.').setFontStyle('italic');
    return startRow + LAYOUT.ALERTS.height;
  }
  sheet.getRange(row, 1, 1, 5).setValues([['Уровень', 'Контур', 'Устройство', 'Алерт', 'Причина']]).setFontWeight('bold').setBackground('#ECEFF1');
  row++;
  alerts.forEach(alert => {
    sheet.getRange(row, 1).setValue(alert.level).setBackground(ALERT_COLORS[alert.level] || '#FFF3E0');
    sheet.getRange(row, 2).setValue(alert.environment || '—');
    sheet.getRange(row, 3).setValue(alert.device || '—');
    sheet.getRange(row, 4).setValue(alert.text);
    sheet.getRange(row, 5).setValue(alert.reason);
    row++;
  });
  return startRow + LAYOUT.ALERTS.height;
}

function buildAlerts(latest, previous, routes, allProjectRoutes, stabilityRows, thresholds) {
  const alerts = [];

  // Строим lookup предыдущих run для каждой комбинации env+device
  const prevRunLookup = buildPreviousRunByEnvDevice_(allProjectRoutes);

  // Группируем routes по environment + device для Smart Alerts
  const groups = {};
  routes.forEach(route => {
    const key = `${normalizeEnvironment(route.environment)}|${route.device.toLowerCase()}`;
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(route);
  });

  // Для каждой группы env+device генерируем алерты с полным контекстом
  Object.keys(groups).forEach(groupKey => {
    const groupRoutes = groups[groupKey];
    const parts = groupKey.split('|');
    const env = parts[0];
    const device = parts[1];
    const groupMetrics = aggregateRouteMetrics(groupRoutes);
    const highestRoute = groupRoutes.slice().sort((a, b) => (b.lcp || 0) - (a.lcp || 0))[0];
    const scopeLabel = summarizeList_(groupRoutes.map(r => r.page), 3);

    // Дельты: предыдущий run для ЭТОГО env+device (не глобальный previous)
    const prevMetrics = prevRunLookup[groupKey];
    const prevLcp = prevMetrics ? prevMetrics.lcp : null;
    const prevInp = prevMetrics ? prevMetrics.inp : null;
    const prevTtfb = prevMetrics ? prevMetrics.ttfb : null;
    const deltaLcp = metricDelta(groupMetrics.lcp, prevLcp);
    const deltaInp = metricDelta(groupMetrics.inp, prevInp);
    const deltaTtfb = metricDelta(groupMetrics.ttfb, prevTtfb);
    const avgClsStd = stabilityRows.length ? stabilityRows.reduce((sum, rec) => sum + (rec.clsStd || 0), 0) / stabilityRows.length : 0;

    // LCP алерты
    if (deltaLcp !== null && deltaLcp >= 20) {
      alerts.push({
        level: 'HIGH', metric: 'LCP', environment: env, device: device,
        page: highestRoute ? highestRoute.page : '',
        text: `LCP регресс ${formatPercent(deltaLcp)} (${formatMetricValue('lcp', prevLcp)} → ${formatMetricValue('lcp', groupMetrics.lcp)})`,
        reason: `Scope: ${scopeLabel}; ${describeTtfb({ ttfb: groupMetrics.ttfb }, deltaTtfb)}`,
      });
    } else if (deltaLcp !== null && deltaLcp >= 10) {
      alerts.push({
        level: 'MEDIUM', metric: 'LCP', environment: env, device: device,
        page: highestRoute ? highestRoute.page : '',
        text: `LCP ухудшился ${formatPercent(deltaLcp)} (${formatMetricValue('lcp', prevLcp)} → ${formatMetricValue('lcp', groupMetrics.lcp)})`,
        reason: `${describeTtfb({ ttfb: groupMetrics.ttfb }, deltaTtfb)}`,
      });
    } else if (deltaLcp !== null && deltaLcp >= 5) {
      alerts.push({
        level: 'LOW', metric: 'LCP', environment: env, device: device,
        page: highestRoute ? highestRoute.page : '',
        text: `LCP растёт ${formatPercent(deltaLcp)}`,
        reason: `Следи за ${highestRoute ? highestRoute.page : 'ключевыми страницами'}.`,
      });
    }

    // INP алерты
    const inpStatus = assessMetricStatus('inp', groupMetrics.inp, thresholds).status;
    if (groupMetrics.inp && inpStatus === 'POOR') {
      alerts.push({
        level: 'HIGH', metric: 'INP', environment: env, device: device, page: '',
        text: `INP вне порога (${formatMetricValue('inp', groupMetrics.inp)})`,
        reason: `JS/тяжёлые задачи блокируют main thread.`,
      });
    } else if (groupMetrics.inp && inpStatus === 'NI') {
      alerts.push({
        level: 'MEDIUM', metric: 'INP', environment: env, device: device, page: '',
        text: `INP повышен (${formatMetricValue('inp', groupMetrics.inp)})`,
        reason: `Main thread нагружен.`,
      });
    } else if (deltaInp !== null && deltaInp >= 20) {
      alerts.push({
        level: 'LOW', metric: 'INP', environment: env, device: device, page: '',
        text: `INP растёт ${formatPercent(deltaInp)}`,
        reason: `INP drift.`,
      });
    }

    // CLS алерты
    const clsStatus = assessMetricStatus('cls', groupMetrics.cls, thresholds).status;
    if (groupMetrics.cls && clsStatus === 'POOR') {
      alerts.push({
        level: 'HIGH', metric: 'CLS', environment: env, device: device, page: '',
        text: `CLS вне порога (${groupMetrics.cls.toFixed(3)})`,
        reason: `Нестабильный layout; CLS std avg ${avgClsStd.toFixed(3)}.`,
      });
    } else if (groupMetrics.cls && (clsStatus === 'NI' || avgClsStd > 0.05)) {
      alerts.push({
        level: 'MEDIUM', metric: 'CLS', environment: env, device: device, page: '',
        text: `CLS нестабилен (${groupMetrics.cls.toFixed(3)})`,
        reason: `CLS std ${avgClsStd.toFixed(3)}; баннеры/шрифты двигаются.`,
      });
    }

    // TTFB алерты
    const ttfbStatus = assessMetricStatus('ttfb', groupMetrics.ttfb, thresholds).status;
    if (groupMetrics.ttfb && ttfbStatus === 'POOR') {
      alerts.push({
        level: 'HIGH', metric: 'TTFB', environment: env, device: device, page: '',
        text: `Backend bottleneck (${formatMetricValue('ttfb', groupMetrics.ttfb)})`,
        reason: `Сервер откликается медленно.`,
      });
    } else if (deltaTtfb !== null && deltaTtfb > 20) {
      alerts.push({
        level: 'MEDIUM', metric: 'TTFB', environment: env, device: device, page: '',
        text: `TTFB растёт ${formatPercent(deltaTtfb)}`,
        reason: 'Response time растёт — может затронуть LCP.',
      });
    }
  });

  // Сортировка: HIGH → MEDIUM → LOW
  const levelOrder = { HIGH: 0, MEDIUM: 1, LOW: 2 };
  alerts.sort((a, b) => (levelOrder[a.level] || 3) - (levelOrder[b.level] || 3));
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
  const startRow = row;
  row = renderBlockHeader(sheet, row, 'БЛОК 4 — СВОДКА ПО МЕТРИКАМ', 3);
  sheet.getRange(row, 1, 1, 3).setValues([['Метрика', 'Значение', 'Статус']]).setFontWeight('bold');
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
  return startRow + LAYOUT.OVERVIEW.height;
}

function renderTrendBlock(sheet, row, trendRuns, stabilityRows, routes) {
  const blockTop = row;
  row = renderBlockHeader(sheet, row, 'БЛОК 5 — ТРЕНД', 6);
  if (!trendRuns.length) {
    sheet.getRange(row, 1).setValue('Нет истории прогонов.');
    return blockTop + LAYOUT.TREND.height;
  }

  // Разделяем точки на before/after по тегу (теги могут быть составными)
  const hasTags = trendRuns.some(run => hasTagToken_(run.tag, 'before') || hasTagToken_(run.tag, 'after'));

  if (hasTags) {
    const columns = ['Run ID', 'LCP before', 'LCP after', 'INP before', 'INP after'];
    sheet.getRange(row, 1, 1, columns.length).setValues([columns]).setFontWeight('bold');
    row++;
    const data = trendRuns.map(run => {
      const isBefore = hasTagToken_(run.tag, 'before');
      const isAfter = hasTagToken_(run.tag, 'after');
      return [
        run.runId || '—',
        isBefore ? (run.lcp || 0) : '',
        isAfter ? (run.lcp || 0) : '',
        isBefore ? (run.inp || 0) : '',
        isAfter ? (run.inp || 0) : '',
      ];
    });
    const dataRange = sheet.getRange(row, 1, data.length, columns.length);
    dataRange.setValues(data);
    insertLineChart(sheet, sheet.getRange(row - 1, 1, data.length + 1, columns.length), CHART_ZONES.TREND.row, CHART_ZONES.TREND.col, 'Тренд CWV p90 (before/after)');
    row += data.length + 1;
  } else {
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
    insertLineChart(sheet, sheet.getRange(row - 1, 1, data.length + 1, columns.length), CHART_ZONES.TREND.row, CHART_ZONES.TREND.col, 'Тренд CWV p90');
    row += data.length + 1;
  }

  // Stability sub-block
  sheet.getRange(row, 1, 1, 4).setValues([['Стабильность — std deviation', '', '', '']]);
  sheet.getRange(row, 1, 1, 4).setFontWeight('bold');
  sheet.getRange(row, 1, 1, 4).setBackground('#263238');
  sheet.getRange(row, 1, 1, 4).setFontColor('#ffffff');
  row++;
  if (!stabilityRows.length) {
    sheet.getRange(row, 1).setValue('Stability data missing.');
    return blockTop + LAYOUT.TREND.height;
  }
  const stabilityColumns = ['Страница', 'LCP std', 'INP std', 'CLS std'];
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
  const helperRange = sheet.getRange(blockTop, HELPER_COLUMN_SECONDARY, chartData.length, 4);
  helperRange.setValues(chartData);
  insertLineChart(sheet, helperRange, CHART_ZONES.STABILITY.row, CHART_ZONES.STABILITY.col, 'Std deviation по страницам');
  return blockTop + LAYOUT.TREND.height;
}

function renderWorstPagesBlock(sheet, row, routes, thresholds, title) {
  const blockTop = row;
  row = renderBlockHeader(sheet, row, title || 'БЛОК 6 — ХУДШИЕ СТРАНИЦЫ', 5);
  if (!routes.length) {
    sheet.getRange(row, 1).setValue('Routes not collected.');
    return blockTop + LAYOUT.WORST_PAGES.height;
  }
  const metricSpecs = [
    { label: 'P', key: 'avgScore', type: 'low', formatter: value => value },
    { label: 'LCP', key: 'lcp', type: 'high', formatter: value => value },
    { label: 'INP', key: 'inp', type: 'high', formatter: value => value },
    { label: 'CLS', key: 'cls', type: 'high', formatter: value => value },
    { label: 'TTFB', key: 'ttfb', type: 'high', formatter: value => value },
  ];
  const rows = [];
  metricSpecs.forEach(spec => {
    const sorted = routes
      .filter(route => parseNumber(route[spec.key]) !== null)
      .slice()
      .sort((a, b) => spec.type === 'low' ? ((a[spec.key] || 0) - (b[spec.key] || 0)) : ((b[spec.key] || 0) - (a[spec.key] || 0)))
      .slice(0, 3);
    sorted.forEach(route => {
      rows.push({
        metric: spec.label,
        environment: route.environment,
        page: route.page,
        device: route.device,
        score: route.avgScore,
        lcp: route.lcp,
        inp: route.inp,
        cls: route.cls,
        ttfb: route.ttfb,
      });
    });
  });
  sheet.getRange(row, 1, 1, 9).setValues([['Метрика', 'Контур', 'Страница', 'Устройство', 'P', 'LCP p90', 'INP p90', 'CLS p90', 'TTFB']]).setFontWeight('bold').setBackground('#ECEFF1');
  row++;
  rows.forEach(route => {
    sheet.getRange(row, 1, 1, 9).setValues([[
      route.metric,
      route.environment,
      route.page,
      route.device,
      route.score || '—',
      route.lcp || '—',
      route.inp || '—',
      route.cls || '—',
      route.ttfb || '—',
    ]]);
    colorMetricCell_(sheet, row, 5, 'p', route.score, thresholds);
    colorMetricCell_(sheet, row, 6, 'lcp', route.lcp, thresholds);
    colorMetricCell_(sheet, row, 7, 'inp', route.inp, thresholds);
    colorMetricCell_(sheet, row, 8, 'cls', route.cls, thresholds);
    colorMetricCell_(sheet, row, 9, 'ttfb', route.ttfb, thresholds);
    row++;
  });
  return blockTop + LAYOUT.WORST_PAGES.height;
}

function renderDeviceSplitBlock(sheet, row, routes, thresholds, title) {
  const blockTop = row;
  row = renderBlockHeader(sheet, row, title || 'БЛОК 7 — DESKTOP VS MOBILE', 4);
  if (!routes.length) {
    sheet.getRange(row, 1).setValue('Нет данных по девайсам.');
    return blockTop + LAYOUT.DEVICE_SPLIT.height;
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
      environments: summarizeList_(routes.filter(route => route.device.toLowerCase() === device).map(route => route.environment), 4),
      pages: uniqueNonEmptyValues_(routes.filter(route => route.device.toLowerCase() === device).map(route => route.page)).length,
      lcp: Math.round(totals.lcp / count) || 0,
      inp: Math.round(totals.inp / count) || 0,
      cls: parseFloat((totals.cls / count).toFixed(3)) || 0,
      ttfb: Math.round(routes.filter(route => route.device.toLowerCase() === device).reduce((sum, route) => sum + (route.ttfb || 0), 0) / count) || 0,
      note: `среднее по ${count} строкам`,
    };
  });
  sheet.getRange(row, 1, 1, 8).setValues([['Устройство', 'Контуры', 'Страницы', 'LCP p90', 'INP p90', 'CLS p90', 'TTFB', 'Расчёт']]).setFontWeight('bold').setBackground('#ECEFF1');
  row++;
  rows.forEach(entry => {
    sheet.getRange(row, 1, 1, 8).setValues([[
      entry.device,
      entry.environments,
      entry.pages,
      entry.lcp,
      entry.inp,
      entry.cls,
      entry.ttfb,
      entry.note,
    ]]);
    colorMetricCell_(sheet, row, 4, 'lcp', entry.lcp, thresholds);
    colorMetricCell_(sheet, row, 5, 'inp', entry.inp, thresholds);
    colorMetricCell_(sheet, row, 6, 'cls', entry.cls, thresholds);
    colorMetricCell_(sheet, row, 7, 'ttfb', entry.ttfb, thresholds);
    row++;
  });
  const chartData = [['Device', 'LCP p90', 'INP p90', 'CLS p90']];
  rows.forEach(entry => chartData.push([entry.device, entry.lcp, entry.inp, entry.cls]));
  const helperRow = blockTop;
  const helperRange = sheet.getRange(helperRow, HELPER_COLUMN_PRIMARY, chartData.length, 4);
  helperRange.setValues(chartData);
  insertGroupedBarChart(sheet, helperRange, CHART_ZONES.DEVICE.row, CHART_ZONES.DEVICE.col, 'Mobile vs Desktop');
  return blockTop + LAYOUT.DEVICE_SPLIT.height;
}

function renderDiagnosticsBlock(sheet, row, latest, thresholds) {
  const startRow = row;
  row = renderBlockHeader(sheet, row, 'БЛОК 8 — ДИАГНОСТИКА', 3);
  const diagnostics = buildDiagnostics(latest, thresholds);
  if (!diagnostics.length) {
    sheet.getRange(row, 1).setValue('Сигналов нет, продолжай мониторинг.');
    return startRow + LAYOUT.DIAGNOSTICS.height;
  }
  sheet.getRange(row, 1, 1, 2).setValues([['Проблема', 'Причина']]).setFontWeight('bold').setBackground('#ECEFF1');
  row++;
  diagnostics.forEach(item => {
    sheet.getRange(row, 1).setValue(item.title);
    sheet.getRange(row, 2).setValue(item.detail);
    row++;
  });
  return startRow + LAYOUT.DIAGNOSTICS.height;
}

function buildDiagnostics(latest, thresholds) {
  const diagnostics = [];
  if (latest.ttfb && assessMetricStatus('ttfb', latest.ttfb, thresholds).status === 'POOR') {
    diagnostics.push({ title: 'Backend bottleneck', detail: `TTFB ${formatMetricValue('ttfb', latest.ttfb)} хуже порога из Config` });
  }
  if (latest.ttfb && latest.lcp && assessMetricStatus('ttfb', latest.ttfb, thresholds).status === 'POOR' && assessMetricStatus('lcp', latest.lcp, thresholds).status === 'POOR') {
    diagnostics.push({ title: 'SSR waterfall / chained requests', detail: `TTFB ${formatMetricValue('ttfb', latest.ttfb)} + LCP ${formatMetricValue('lcp', latest.lcp)} — серверный рендеринг блокирует отрисовку` });
  }
  if (latest.ttfb && latest.lcp && assessMetricStatus('ttfb', latest.ttfb, thresholds).status === 'GOOD' && assessMetricStatus('lcp', latest.lcp, thresholds).status === 'POOR') {
    diagnostics.push({ title: 'Frontend rendering', detail: `LCP ${formatMetricValue('lcp', latest.lcp)} хуже порога при нормальном TTFB` });
  }
  if (latest.inp && (assessMetricStatus('inp', latest.inp, thresholds).status !== 'GOOD' || (latest.tbt && latest.tbt > 300))) {
    diagnostics.push({ title: 'Main thread blocking', detail: `INP ${formatMetricValue('inp', latest.inp)} | TBT ${formatMetricValue('tbt', latest.tbt)}` });
  }
  if (latest.cls && assessMetricStatus('cls', latest.cls, thresholds).status !== 'GOOD') {
    diagnostics.push({ title: 'Layout shift', detail: `CLS ${latest.cls.toFixed(3)} вне зелёной зоны (изображения/баннеры)` });
  }
  return diagnostics;
}

function buildDeduplicatedRouteHealth(routes, allProjectRoutes, stabilityMap, thresholds) {
  // Группировка текущих данных по page + device + environment → один агрегат
  const grouped = {};
  routes.forEach(route => {
    const key = `${route.page}|${route.device.toLowerCase()}|${normalizeEnvironment(route.environment)}`;
    if (!grouped[key]) {
      grouped[key] = [];
    }
    grouped[key].push(route);
  });

  // Строим lookup предыдущих run_id из ВСЕХ routes проекта (не только отфильтрованных)
  const previousRunLookup = buildPreviousRunLookup_(allProjectRoutes);

  return Object.keys(grouped).map(key => {
    const group = grouped[key];
    const sample = group[group.length - 1];
    const metrics = aggregateRouteMetrics(group);
    const stabKey = buildStabilityKey(sample.project, sample.environment, sample.source, sample.page, sample.device.toLowerCase());
    const stability = stabilityMap[stabKey];
    const statusInfo = evaluateRouteHealth({ lcp: metrics.lcp, inp: metrics.inp, cls: metrics.cls, ttfb: metrics.ttfb }, stability, thresholds);

    // Delta: находим предыдущий run_id для того же page+device+env
    const prevMetrics = previousRunLookup[key];
    const deltaLcp = prevMetrics ? metricDelta(metrics.lcp, prevMetrics.lcp) : null;
    const deltaInp = prevMetrics ? metricDelta(metrics.inp, prevMetrics.inp) : null;

    return {
      page: sample.page,
      device: sample.device,
      environment: normalizeEnvironment(sample.environment),
      lcp: metrics.lcp,
      deltaLcp: deltaLcp,
      inp: metrics.inp,
      deltaInp: deltaInp,
      cls: metrics.cls,
      status: statusInfo.status,
      statusColor: statusInfo.color,
      reason: statusInfo.reason,
    };
  });
}

function buildPreviousRunByEnvDevice_(allRoutes) {
  // Для каждой комбинации env+device находим предпоследний run_id
  // и возвращаем его агрегированные метрики
  const byKey = {};
  allRoutes.forEach(route => {
    const key = `${normalizeEnvironment(route.environment)}|${route.device.toLowerCase()}`;
    const runId = toText(route.runId || route.run_id || '').trim();
    if (!runId) return;
    if (!byKey[key]) {
      byKey[key] = {};
    }
    if (!byKey[key][runId]) {
      byKey[key][runId] = [];
    }
    byKey[key][runId].push(route);
  });

  const result = {};
  Object.keys(byKey).forEach(key => {
    const runIds = Object.keys(byKey[key]).sort();
    if (runIds.length < 2) return;
    const prevRunId = runIds[runIds.length - 2];
    result[key] = aggregateRouteMetrics(byKey[key][prevRunId]);
  });
  return result;
}

function buildPreviousRunLookup_(allRoutes) {
  // Для каждого page+device+env находим последний и предпоследний run_id
  // и возвращаем метрики предпоследнего run_id
  const byKey = {};
  allRoutes.forEach(route => {
    const key = `${route.page}|${route.device.toLowerCase()}|${normalizeEnvironment(route.environment)}`;
    const runId = toText(route.runId || route.run_id || '').trim();
    if (!runId) return;
    if (!byKey[key]) {
      byKey[key] = {};
    }
    if (!byKey[key][runId]) {
      byKey[key][runId] = [];
    }
    byKey[key][runId].push(route);
  });

  const result = {};
  Object.keys(byKey).forEach(key => {
    const runIds = Object.keys(byKey[key]).sort();
    if (runIds.length < 2) return;
    // Предпоследний run_id
    const prevRunId = runIds[runIds.length - 2];
    const prevRoutes = byKey[key][prevRunId];
    result[key] = aggregateRouteMetrics(prevRoutes);
  });
  return result;
}

function renderRouteHealthBlock(sheet, row, routes, allProjectRoutes, stabilityMap, thresholds) {
  const startRow = row;
  row = renderBlockHeader(sheet, row, 'БЛОК 9 — ЗДОРОВЬЕ РОУТОВ', 10);
  if (!routes.length) {
    sheet.getRange(row, 1).setValue('Нет данных по маршрутам.');
    return startRow + LAYOUT.ROUTE_HEALTH.height;
  }
  const dedupRows = buildDeduplicatedRouteHealth(routes, allProjectRoutes, stabilityMap, thresholds);
  sheet.getRange(row, 1, 1, 10).setValues([['Страница', 'Устройство', 'Контур', 'LCP', 'Δ LCP', 'INP', 'Δ INP', 'CLS', 'Статус', 'Причина']]).setFontWeight('bold').setBackground('#ECEFF1');
  row++;
  dedupRows.forEach(item => {
    sheet.getRange(row, 1, 1, 10).setValues([[
      item.page,
      item.device,
      item.environment,
      item.lcp !== null ? formatMetricValue('lcp', item.lcp) : '—',
      item.deltaLcp !== null ? formatPercent(item.deltaLcp) : '—',
      item.inp !== null ? formatMetricValue('inp', item.inp) : '—',
      item.deltaInp !== null ? formatPercent(item.deltaInp) : '—',
      item.cls !== null ? item.cls.toFixed(3) : '—',
      item.status,
      item.reason,
    ]]);
    colorMetricCell_(sheet, row, 4, 'lcp', item.lcp, thresholds);
    colorMetricCell_(sheet, row, 6, 'inp', item.inp, thresholds);
    sheet.getRange(row, 9).setBackground(item.statusColor);
    row++;
  });
  return startRow + LAYOUT.ROUTE_HEALTH.height;
}

function evaluateRouteHealth(route, stability, thresholds) {
  const { lcp = 0, inp = 0, cls = 0 } = route;
  const lcpStatus = assessMetricStatus('lcp', lcp, thresholds).status;
  const inpStatus = assessMetricStatus('inp', inp, thresholds).status;
  const clsStatus = assessMetricStatus('cls', cls, thresholds).status;
  if (lcpStatus === 'POOR' || inpStatus === 'POOR' || clsStatus === 'POOR') {
    return {
      status: 'BAD',
      color: STATUS_COLORS.POOR,
      reason: `LCP ${formatMetricValue('lcp', lcp)}, INP ${formatMetricValue('inp', inp)}, CLS ${cls ? cls.toFixed(3) : 0}`,
    };
  }
  if (lcpStatus === 'NI' || inpStatus === 'NI' || clsStatus === 'NI') {
    return { status: 'MEDIUM', color: STATUS_COLORS.NI, reason: `Metrics elevated (LCP ${formatMetricValue('lcp', lcp)})` };
  }
  const stabilityHint = stability && stability.clsStd ? `CLS std ${stability.clsStd.toFixed(3)}` : '-';
  return { status: 'OK', color: STATUS_COLORS.GOOD, reason: stabilityHint };
}

function renderSprintImpactBlock(sheet, row, project, filters, allRuns, allRoutes, thresholds, title) {
  const startRow = row;
  row = renderBlockHeader(sheet, row, title || 'БЛОК — SPRINT IMPACT', 8);
  const sprintConfig = readSprintMetadata(sheet);

  // after = записи текущего спринта с тегом after
  // before = (1) записи текущего спринта с тегом before, ИЛИ
  //          (2) fallback: записи предыдущего инкремента (previousIncrement) — любой тег
  const currentSprint = (sprintConfig && sprintConfig.currentSprint) || '';
  const prevIncrement = (sprintConfig && sprintConfig.previousIncrement) || '';

  // after: ищем в текущем спринте записи с тегом after
  let afterRoutes = allRoutes.filter(r => {
    if (currentSprint && toText(r.sprint).trim() !== currentSprint) return false;
    return hasTagToken_(r.tag, 'after');
  });
  // Если нет записей текущего спринта — берём последний run_id по каждому env+device
  if (!afterRoutes.length) {
    afterRoutes = allRoutes.filter(r => hasTagToken_(r.tag, 'after'));
  }

  // before: сначала ищем записи текущего спринта с тегом before
  let beforeRoutes = allRoutes.filter(r => {
    if (currentSprint && toText(r.sprint).trim() !== currentSprint) return false;
    return hasTagToken_(r.tag, 'before');
  });
  // Fallback: если нет before в текущем спринте — берём ВСЕ записи предыдущего инкремента
  if (!beforeRoutes.length && prevIncrement) {
    beforeRoutes = allRoutes.filter(r => toText(r.sprint).trim() === prevIncrement);
  }
  // Fallback 2: если и предыдущего инкремента нет — берём предпоследний run_id по env+device
  const usePreviousRunFallback = !beforeRoutes.length;
  let previousRunMetrics = {};
  if (usePreviousRunFallback) {
    previousRunMetrics = buildPreviousRunByEnvDevice_(allRoutes);
  }

  if (!afterRoutes.length && !beforeRoutes.length && !Object.keys(previousRunMetrics).length) {
    sheet.getRange(row, 1).setValue('Нет данных для сравнения.').setFontStyle('italic');
    return startRow + LAYOUT.SPRINT_IMPACT.height;
  }

  // Группируем по environment + device
  const envDeviceKeys = new Set();
  beforeRoutes.forEach(r => envDeviceKeys.add(`${normalizeEnvironment(r.environment)}|${r.device.toLowerCase()}`));
  afterRoutes.forEach(r => envDeviceKeys.add(`${normalizeEnvironment(r.environment)}|${r.device.toLowerCase()}`));
  Object.keys(previousRunMetrics).forEach(k => envDeviceKeys.add(k));

  const impactRows = [];
  envDeviceKeys.forEach(key => {
    const parts = key.split('|');
    const env = parts[0];
    const device = parts[1];
    const aRoutes = afterRoutes.filter(r => normalizeEnvironment(r.environment) === env && r.device.toLowerCase() === device);
    const aMetrics = aggregateRouteMetrics(aRoutes);

    let bMetrics;
    if (usePreviousRunFallback) {
      bMetrics = previousRunMetrics[key] || { lcp: null, inp: null, cls: null, ttfb: null };
    } else {
      const bRoutes = beforeRoutes.filter(r => normalizeEnvironment(r.environment) === env && r.device.toLowerCase() === device);
      bMetrics = aggregateRouteMetrics(bRoutes);
    }

    const lcpDelta = metricDelta(aMetrics.lcp, bMetrics.lcp);
    const inpDelta = metricDelta(aMetrics.inp, bMetrics.inp);
    const clsDelta = metricDelta(aMetrics.cls, bMetrics.cls);
    const ttfbDelta = metricDelta(aMetrics.ttfb, bMetrics.ttfb);

    // Результат по всем Core Web Vitals (LCP, INP, CLS)
    let result = 'STABLE';
    const hasRegression = (lcpDelta !== null && lcpDelta > 10) || (inpDelta !== null && inpDelta > 10) || (clsDelta !== null && clsDelta > 10);
    const hasImprovement = (lcpDelta !== null && lcpDelta < -10) || (inpDelta !== null && inpDelta < -10) || (clsDelta !== null && clsDelta < -10);
    if (hasRegression) result = 'REGRESSION';
    else if (hasImprovement) result = 'IMPROVED';

    impactRows.push({
      env, device,
      lcpBefore: bMetrics.lcp, lcpAfter: aMetrics.lcp, lcpDelta,
      inpBefore: bMetrics.inp, inpAfter: aMetrics.inp, inpDelta,
      clsBefore: bMetrics.cls, clsAfter: aMetrics.cls, clsDelta,
      ttfbDelta,
      result,
    });
  });

  const headers = ['Контур', 'Устройство', 'LCP before', 'LCP after', 'Δ LCP', 'INP before', 'INP after', 'Δ INP', 'CLS before', 'CLS after', 'Δ CLS', 'Δ TTFB', 'Результат'];
  sheet.getRange(row, 1, 1, headers.length).setValues([headers]).setFontWeight('bold').setBackground('#ECEFF1');
  row++;
  const dataStartRow = row;
  impactRows.forEach(item => {
    const resultColor = item.result === 'IMPROVED' ? STATUS_COLORS.GOOD : (item.result === 'REGRESSION' ? STATUS_COLORS.POOR : STATUS_COLORS.NI);
    sheet.getRange(row, 1, 1, headers.length).setValues([[
      item.env,
      item.device,
      item.lcpBefore !== null ? formatMetricValue('lcp', item.lcpBefore) : '—',
      item.lcpAfter !== null ? formatMetricValue('lcp', item.lcpAfter) : '—',
      item.lcpDelta !== null ? formatPercent(item.lcpDelta) : '—',
      item.inpBefore !== null ? formatMetricValue('inp', item.inpBefore) : '—',
      item.inpAfter !== null ? formatMetricValue('inp', item.inpAfter) : '—',
      item.inpDelta !== null ? formatPercent(item.inpDelta) : '—',
      item.clsBefore !== null ? (item.clsBefore).toFixed(3) : '—',
      item.clsAfter !== null ? (item.clsAfter).toFixed(3) : '—',
      item.clsDelta !== null ? formatPercent(item.clsDelta) : '—',
      item.ttfbDelta !== null ? formatPercent(item.ttfbDelta) : '—',
      item.result,
    ]]);
    colorMetricCell_(sheet, row, 3, 'lcp', item.lcpBefore, thresholds);
    colorMetricCell_(sheet, row, 4, 'lcp', item.lcpAfter, thresholds);
    colorMetricCell_(sheet, row, 6, 'inp', item.inpBefore, thresholds);
    colorMetricCell_(sheet, row, 7, 'inp', item.inpAfter, thresholds);
    colorMetricCell_(sheet, row, 9, 'cls', item.clsBefore, thresholds);
    colorMetricCell_(sheet, row, 10, 'cls', item.clsAfter, thresholds);
    sheet.getRange(row, headers.length).setBackground(resultColor);
    row++;
  });

  // Sprint Impact Chart — grouped bar: LCP before vs LCP after
  if (impactRows.length) {
    const chartData = [['Срез', 'LCP before', 'LCP after']];
    impactRows.forEach(item => {
      chartData.push([`${item.env}-${item.device}`, item.lcpBefore || 0, item.lcpAfter || 0]);
    });
    const helperRange = sheet.getRange(startRow, HELPER_COLUMN_SECONDARY, chartData.length, 3);
    helperRange.setValues(chartData);
    insertGroupedBarChart(sheet, helperRange, CHART_ZONES.SPRINT.row, CHART_ZONES.SPRINT.col, 'Sprint Impact: LCP before vs after');
  }

  return startRow + LAYOUT.SPRINT_IMPACT.height;
}

function hasTagToken_(tag, token) {
  if (!tag) return false;
  return toText(tag).toLowerCase().split(/[,;\s]+/).some(t => t.trim() === token.toLowerCase());
}

// ─── Metric Breakdown ───────────────────────────────────────────────────────

const METRIC_BREAKDOWN_DEFS = {
  route: [
    { key: 'lcp',  label: 'LCP (Largest Contentful Paint)',    unit: 'ms' },
    { key: 'inp',  label: 'INP (Interaction to Next Paint)',   unit: 'ms' },
    { key: 'cls',  label: 'CLS (Cumulative Layout Shift)',     unit: ''   },
    { key: 'ttfb', label: 'TTFB (Time to First Byte)',         unit: 'ms' },
  ],
  run: [
    { key: 'tbt',   label: 'TBT (Total Blocking Time)',       unit: 'ms' },
    { key: 'fcp',   label: 'FCP (First Contentful Paint)',     unit: 'ms' },
    { key: 'speed', label: 'SI (Speed Index)',                 unit: 'ms' },
    { key: 'tti',   label: 'TTI (Time to Interactive)',        unit: 'ms' },
  ],
};

/**
 * Агрегирует массив runs по одной числовой метрике, возвращая среднее.
 */
function aggregateRunMetric_(runs, metricKey) {
  let sum = 0;
  let count = 0;
  runs.forEach(run => {
    const v = run[metricKey];
    if (v !== null && v !== undefined) {
      sum += v;
      count++;
    }
  });
  if (!count) return null;
  if (metricKey === 'cls') return parseFloat((sum / count).toFixed(3));
  return Math.round(sum / count);
}

/**
 * Строит before/after routes по той же логике что и Sprint Impact.
 * Возвращает { afterRoutes, beforeRoutes, usePreviousRunFallback, previousRunLookup }
 */
function resolveBeforeAfterRoutes_(allRoutes, sprintConfig) {
  const currentSprint = (sprintConfig && sprintConfig.currentSprint) || '';
  const prevIncrement = (sprintConfig && sprintConfig.previousIncrement) || '';

  let afterRoutes = allRoutes.filter(r => {
    if (currentSprint && toText(r.sprint).trim() !== currentSprint) return false;
    return hasTagToken_(r.tag, 'after');
  });
  if (!afterRoutes.length) {
    afterRoutes = allRoutes.filter(r => hasTagToken_(r.tag, 'after'));
  }

  let beforeRoutes = allRoutes.filter(r => {
    if (currentSprint && toText(r.sprint).trim() !== currentSprint) return false;
    return hasTagToken_(r.tag, 'before');
  });
  if (!beforeRoutes.length && prevIncrement) {
    beforeRoutes = allRoutes.filter(r => toText(r.sprint).trim() === prevIncrement);
  }

  const usePreviousRunFallback = !beforeRoutes.length;
  let previousRunLookup = {};
  if (usePreviousRunFallback) {
    previousRunLookup = buildPreviousRunLookup_(allRoutes);
  }

  return { afterRoutes, beforeRoutes, usePreviousRunFallback, previousRunLookup };
}

/**
 * Строит before/after runs по той же логике что и Sprint Impact.
 */
function resolveBeforeAfterRuns_(allRuns, sprintConfig) {
  const currentSprint = (sprintConfig && sprintConfig.currentSprint) || '';
  const prevIncrement = (sprintConfig && sprintConfig.previousIncrement) || '';

  let afterRuns = allRuns.filter(r => {
    if (currentSprint && toText(r.sprint).trim() !== currentSprint) return false;
    return hasTagToken_(r.tag, 'after');
  });
  if (!afterRuns.length) {
    afterRuns = allRuns.filter(r => hasTagToken_(r.tag, 'after'));
  }

  let beforeRuns = allRuns.filter(r => {
    if (currentSprint && toText(r.sprint).trim() !== currentSprint) return false;
    return hasTagToken_(r.tag, 'before');
  });
  if (!beforeRuns.length && prevIncrement) {
    beforeRuns = allRuns.filter(r => toText(r.sprint).trim() === prevIncrement);
  }

  const usePreviousRunFallback = !beforeRuns.length;
  let previousRunByEnvDevice = {};
  if (usePreviousRunFallback) {
    previousRunByEnvDevice = buildPreviousRunByEnvDeviceRuns_(allRuns);
  }

  return { afterRuns, beforeRuns, usePreviousRunFallback, previousRunByEnvDevice };
}

/**
 * Для каждого env+device находим предпоследний run_id из Runs и агрегируем метрики.
 */
function buildPreviousRunByEnvDeviceRuns_(allRuns) {
  const byKey = {};
  allRuns.forEach(run => {
    const env = normalizeEnvironment(run.environment);
    // Runs не имеют device напрямую — определяем из runId или считаем 'all'
    const device = 'all';
    const key = env + '|' + device;
    const runId = toText(run.runId).trim();
    if (!runId) return;
    if (!byKey[key]) byKey[key] = {};
    if (!byKey[key][runId]) byKey[key][runId] = [];
    byKey[key][runId].push(run);
  });

  const result = {};
  Object.keys(byKey).forEach(key => {
    const runIds = Object.keys(byKey[key]).sort();
    if (runIds.length < 2) return;
    const prevRunId = runIds[runIds.length - 2];
    result[key] = byKey[key][prevRunId];
  });
  return result;
}

function renderMetricBreakdownBlock(sheet, row, projectRuns, projectRoutes, thresholds, sprintConfig) {
  const startRow = row;
  row = renderBlockHeader(sheet, row, 'БЛОК — METRIC BREAKDOWN', 7);

  // ═══ Route-level метрики (LCP, INP, CLS, TTFB) — per page+device ═══
  const resolved = resolveBeforeAfterRoutes_(projectRoutes, sprintConfig);

  METRIC_BREAKDOWN_DEFS.route.forEach(def => {
    // Подзаголовок метрики
    const subRange = sheet.getRange(row, 1, 1, 7);
    subRange.merge();
    subRange.setValue('━━ ' + def.label + ' ━━');
    subRange.setFontWeight('bold').setBackground('#37474F').setFontColor('#FFFFFF');
    row++;

    // Заголовок таблицы
    sheet.getRange(row, 1, 1, 6).setValues([['Страница', 'Устройство', 'Before', 'After', 'Δ', 'Статус']])
      .setFontWeight('bold').setBackground('#ECEFF1');
    row++;

    // Собираем все уникальные page+device из after и before
    const pageDeviceKeys = new Set();
    resolved.afterRoutes.forEach(r => pageDeviceKeys.add(r.page + '|' + r.device.toLowerCase()));
    resolved.beforeRoutes.forEach(r => pageDeviceKeys.add(r.page + '|' + r.device.toLowerCase()));
    if (resolved.usePreviousRunFallback) {
      Object.keys(resolved.previousRunLookup).forEach(k => {
        // key формат: page|device|env — берём page|device
        const parts = k.split('|');
        pageDeviceKeys.add(parts[0] + '|' + parts[1]);
      });
    }

    let hasData = false;
    Array.from(pageDeviceKeys).sort().forEach(key => {
      const parts = key.split('|');
      const page = parts[0];
      const device = parts[1];

      // After: все routes этой page+device, усреднение
      const aRoutes = resolved.afterRoutes.filter(r => r.page === page && r.device.toLowerCase() === device);
      const afterAgg = aggregateRouteMetrics(aRoutes);
      const afterVal = afterAgg[def.key];

      // Before
      let beforeVal = null;
      if (resolved.usePreviousRunFallback) {
        // previousRunLookup ключи: page|device|env — нужны ВСЕ envs
        Object.keys(resolved.previousRunLookup).forEach(lk => {
          const lParts = lk.split('|');
          if (lParts[0] === page && lParts[1] === device) {
            const v = resolved.previousRunLookup[lk][def.key];
            if (v !== null && v !== undefined && beforeVal === null) {
              beforeVal = v;
            }
          }
        });
      } else {
        const bRoutes = resolved.beforeRoutes.filter(r => r.page === page && r.device.toLowerCase() === device);
        const beforeAgg = aggregateRouteMetrics(bRoutes);
        beforeVal = beforeAgg[def.key];
      }

      if (afterVal === null && beforeVal === null) return;
      hasData = true;

      const delta = metricDelta(afterVal, beforeVal);
      const status = assessMetricStatus(def.key, afterVal, thresholds);
      const statusLabel = status.status === 'GOOD' ? '✓ GOOD' : (status.status === 'POOR' ? '✗ POOR' : '⚠ NI');

      sheet.getRange(row, 1, 1, 6).setValues([[
        page,
        device,
        formatMetricValue(def.key, beforeVal),
        formatMetricValue(def.key, afterVal),
        delta !== null ? formatPercent(delta) : '—',
        statusLabel,
      ]]);
      colorMetricCell_(sheet, row, 3, def.key, beforeVal, thresholds);
      colorMetricCell_(sheet, row, 4, def.key, afterVal, thresholds);
      sheet.getRange(row, 6).setBackground(status.color);
      row++;
    });

    if (!hasData) {
      sheet.getRange(row, 1).setValue('Нет данных').setFontStyle('italic');
      row++;
    }
    row++; // пустая строка между метриками
  });

  // ═══ Run-level метрики (TBT, FCP, SI, TTI) — per env+device ═══
  const resolvedRuns = resolveBeforeAfterRuns_(projectRuns, sprintConfig);

  METRIC_BREAKDOWN_DEFS.run.forEach(def => {
    const subRange = sheet.getRange(row, 1, 1, 7);
    subRange.merge();
    subRange.setValue('━━ ' + def.label + ' — данные из Runs ━━');
    subRange.setFontWeight('bold').setBackground('#37474F').setFontColor('#FFFFFF');
    row++;

    sheet.getRange(row, 1, 1, 6).setValues([['Контур', 'Устройство', 'Before', 'After', 'Δ', 'Статус']])
      .setFontWeight('bold').setBackground('#ECEFF1');
    row++;

    // Группируем runs по env (device='all' для runs)
    const envKeys = new Set();
    resolvedRuns.afterRuns.forEach(r => envKeys.add(normalizeEnvironment(r.environment)));
    resolvedRuns.beforeRuns.forEach(r => envKeys.add(normalizeEnvironment(r.environment)));
    if (resolvedRuns.usePreviousRunFallback) {
      Object.keys(resolvedRuns.previousRunByEnvDevice).forEach(k => envKeys.add(k.split('|')[0]));
    }

    let hasData = false;
    Array.from(envKeys).sort().forEach(env => {
      const device = 'all';
      const key = env + '|' + device;

      // After: усреднение всех runs этого env
      const aRuns = resolvedRuns.afterRuns.filter(r => normalizeEnvironment(r.environment) === env);
      const afterVal = aggregateRunMetric_(aRuns, def.key);

      // Before
      let beforeVal = null;
      if (resolvedRuns.usePreviousRunFallback) {
        const prevRuns = resolvedRuns.previousRunByEnvDevice[key];
        if (prevRuns) {
          beforeVal = aggregateRunMetric_(prevRuns, def.key);
        }
      } else {
        const bRuns = resolvedRuns.beforeRuns.filter(r => normalizeEnvironment(r.environment) === env);
        beforeVal = aggregateRunMetric_(bRuns, def.key);
      }

      if (afterVal === null && beforeVal === null) return;
      hasData = true;

      const delta = metricDelta(afterVal, beforeVal);
      const status = assessMetricStatus(def.key, afterVal, thresholds);
      const statusLabel = status.status === 'GOOD' ? '✓ GOOD' : (status.status === 'POOR' ? '✗ POOR' : '⚠ NI');

      sheet.getRange(row, 1, 1, 6).setValues([[
        env,
        device,
        formatMetricValue(def.key, beforeVal),
        formatMetricValue(def.key, afterVal),
        delta !== null ? formatPercent(delta) : '—',
        statusLabel,
      ]]);
      colorMetricCell_(sheet, row, 3, def.key, beforeVal, thresholds);
      colorMetricCell_(sheet, row, 4, def.key, afterVal, thresholds);
      sheet.getRange(row, 6).setBackground(status.color);
      row++;
    });

    if (!hasData) {
      sheet.getRange(row, 1).setValue('Нет данных').setFontStyle('italic');
      row++;
    }
    row++;
  });

  return startRow + LAYOUT.METRIC_BREAKDOWN.height;
}

function renderExperimentsBlock(sheet, row, runs, thresholds) {
  row = renderBlockHeader(sheet, row, 'БЛОК 10 — ЭКСПЕРИМЕНТЫ', 7);
  sheet.getRange(row, 1, 1, 7).setValues([['Тег', 'Run ID', 'LCP p90', 'Δ LCP', 'INP p90', 'CLS p90', 'Результат']]).setFontWeight('bold').setBackground('#ECEFF1');
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
    colorMetricCell_(sheet, row, 3, 'lcp', run.lcp, thresholds);
    colorMetricCell_(sheet, row, 5, 'inp', run.inp, thresholds);
    colorMetricCell_(sheet, row, 6, 'cls', run.cls, thresholds);
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