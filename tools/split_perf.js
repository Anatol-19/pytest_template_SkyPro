const fs = require('fs');
const src = fs.readFileSync('C:/Study/pytest_template_SkyPro/services/lighthouse/Google Sheet/PerfAnalytics.gs', 'utf8');
const lines = src.split('\n');

function extract(from, to) {
  return lines.slice(from - 1, to).join('\n');
}

function findFuncEnd(startLine) {
  let depth = 0; let started = false;
  for (let i = startLine - 1; i < lines.length; i++) {
    const line = lines[i];
    for (const ch of line) {
      if (ch === '{') { depth++; started = true; }
      if (ch === '}') { depth--; }
    }
    if (started && depth === 0) return i + 1;
  }
  return lines.length;
}

function func(startLine) {
  const end = findFuncEnd(startLine);
  return extract(startLine, end);
}

function constBlock(startLine) {
  let depth = 0; let started = false;
  for (let i = startLine - 1; i < lines.length; i++) {
    const line = lines[i];
    for (const ch of line) {
      if (ch === '{' || ch === '[') { depth++; started = true; }
      if (ch === '}' || ch === ']') { depth--; }
    }
    if (!started && line.includes(';')) return extract(startLine, i + 1);
    if (started && depth === 0) return extract(startLine, i + 1);
  }
  return extract(startLine, startLine);
}

// ========== FILE 0: Constants ==========
const file0_header = `/**
 * @file 00_Constants.gs.js
 * @description Все shared-константы и конфигурационные значения.
 *
 * Загружается ПЕРВЫМ (алфавитный порядок) — все const доступны остальным файлам.
 *
 * Содержит:
 *  - Имена листов (RUNS_SHEET, ROUTES_SHEET, etc.)
 *  - Сетка дашборда (LAYOUT, CHART_ZONES)
 *  - Цвета статусов и блоков (STATUS_COLORS, ALERT_COLORS)
 *  - Дефолтные пороги метрик (DEFAULT_METRIC_FALLBACKS)
 *  - Определения метрик для Breakdown (METRIC_BREAKDOWN_DEFS)
 *  - UI-элементы (GENERATE_BUTTON_*, SPRINT_METADATA_CELLS)
 */`;
const file0 = [file0_header, '', extract(1, 104), '', constBlock(673), '', constBlock(2307)].join('\n');

// ========== FILE 1: Utilities ==========
const file1_lines = [815, 729, 722, 744, 796, 807, 822, 833, 852, 845, 863,
  1048, 1064, 453, 462, 473, 679, 693, 481, 447, 970, 664, 619, 1229, 2300];

const file1_header = `/**
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
 */`;
const file1 = [file1_header, '', ...file1_lines.map(l => func(l))].join('\n\n');

// ========== FILE 2: Data Collection ==========
const file2_lines = [262, 269, 287, 321, 333, 339, 353, 378, 392, 414, 428,
  761, 867, 894, 919, 929, 933, 980];

const file2_header = `/**
 * @file 02_DataCollection.gs.js
 * @description ETL-слой: чтение сырых данных, агрегация, helper-sheets.
 *
 * Содержит:
 *  - Сбор сырых данных (collectRawPerfRows, normalizeRawRecord)
 *  - Ребилд Runs/Routes/Stability sheets
 *  - Парсинг записей (extractRunMetrics, parseRouteRecord, parseStabilityRecord)
 *  - Загрузка порогов из Config (loadMetricThresholds, populateFallbackThresholds)
 */`;
const file2 = [file2_header, '', ...file2_lines.map(l => func(l))].join('\n\n');

// ========== FILE 3: Metrics And Filters ==========
const file3_lines = [1004, 1010, 1041, 1276, 1240, 2325,
  195, 216, 225, 233, 1091, 1111, 1125, 1133,
  1141, 1159, 1183, 1192, 1203, 623,
  1583, 1704, 1717, 1971, 2150, 1991];

const file3_header = `/**
 * @file 03_MetricsAndFilters.gs.js
 * @description Аналитическое ядро: оценка метрик, фильтрация, контекст.
 *
 * Содержит:
 *  - Оценка метрик (assessMetricStatus, colorMetricCell_, metricDelta)
 *  - Агрегация (aggregateRouteMetrics, aggregateRunMetric_)
 *  - Sprint metadata и фильтры (readSprintMetadata, applyRunFilters, applyRouteFilters)
 *  - Контекст и алерты (buildContextMetrics, buildAlerts, buildDiagnostics)
 *  - Здоровье роутов (evaluateRouteHealth, buildDeduplicatedRouteHealth)
 */`;
const file3 = [file3_header, '', ...file3_lines.map(l => func(l))].join('\n\n');

// ========== FILE 4: Sprint Analysis ==========
const file4_lines = [1350, 1388, 2344, 2378, 2064, 2091, 2411, 2038, 2046, 2057, 2631];

const file4_header = `/**
 * @file 04_SprintAnalysis.gs.js
 * @description Sprint-сравнения: before/after, temporal lookups.
 *
 * Содержит:
 *  - Cross-env данные (buildCrossEnvRows, buildCrossEnvDeviceRows)
 *  - Resolve before/after (resolveBeforeAfterRoutes_, resolveBeforeAfterRuns_)
 *  - Previous run lookups (buildPreviousRunByEnvDevice_, buildPreviousRunLookup_)
 *  - Временная сортировка (sortRunIdsByDate_, toDate_)
 *  - Baseline (findBaselineRun)
 */`;
const file4 = [file4_header, '', ...file4_lines.map(l => func(l))].join('\n\n');

// ========== FILE 5: Dashboard Renderer ==========
const file5_lines = [135, 513, 497, 504, 580, 601, 611, 489,
  1549, 1072, 1301, 1320, 1562, 1523, 1727,
  1438, 1748, 1829, 1888, 1953, 2119, 2169, 2435, 2600,
  1518, 2640, 2653, 2665];

const file5_header = `/**
 * @file 05_DashboardRenderer.gs.js
 * @description Presentation layer — все render-блоки дашборда.
 *
 * Содержит:
 *  - Оркестратор (renderProjectDashboard)
 *  - Управление UI (prepareDashboardControls, clearDashboard*, showEmptyMessage)
 *  - Блоки: Context, Alerts, CrUX Ref, Overview, Cross-Env, Trend,
 *    Worst Pages, Device Split, Diagnostics, Route Health,
 *    Sprint Impact, Metric Breakdown, Experiments
 *  - Графики (insertLineChart, insertColumnChart, insertGroupedBarChart)
 */`;
const file5 = [file5_header, '', ...file5_lines.map(l => func(l))].join('\n\n');

// ========== FILE 6: Main ==========
const file6_header = `/**
 * @file 06_Main.gs.js
 * @description Точки входа: меню, триггеры, резолв spreadsheet.
 *
 * Содержит:
 *  - updatePerfAnalytics — главная точка входа (меню + кнопка)
 *  - onOpen — создание меню QA Dashboard
 *  - ensurePerfAnalyticsTriggers — управление триггерами
 *  - getPerfSpreadsheet — резолв активного spreadsheet
 */`;
const file6 = [file6_header, '', func(106), func(128), func(248), func(632), func(646)].join('\n\n');

// Write files
const dir = 'C:/Study/pytest_template_SkyPro/tools/clasp';
const files = {
  '00_Constants.gs.js': file0,
  '01_Utilities.gs.js': file1,
  '02_DataCollection.gs.js': file2,
  '03_MetricsAndFilters.gs.js': file3,
  '04_SprintAnalysis.gs.js': file4,
  '05_DashboardRenderer.gs.js': file5,
  '06_Main.gs.js': file6,
};

Object.entries(files).forEach(([name, content]) => {
  fs.writeFileSync(`${dir}/${name}`, content);
});

console.log('Files created!');

// Verify
const srcFuncCount = (src.match(/^function /gm) || []).length;
let outFuncCount = 0;
Object.keys(files).forEach(name => {
  const content = fs.readFileSync(`${dir}/${name}`, 'utf8');
  const count = (content.match(/^function /gm) || []).length;
  outFuncCount += count;
  console.log(`  ${name}: ${count} functions, ${content.split('\n').length} lines`);
});
console.log(`Source: ${srcFuncCount} functions, Output: ${outFuncCount} functions`);
if (srcFuncCount !== outFuncCount) {
  console.log('WARNING: function count mismatch!');
}