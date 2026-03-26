/**
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
 */

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
const GENERATE_BUTTON_PNG_BASE64 = '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';
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

const HEADER_TOKENS_ = new Set([
  'date', 'project', 'environment', 'source', 'sprint', 'run_id', 'tag',
  'iterations', 'pages', 'avg_score', 'p90_lcp', 'p90_inp', 'p90_cls',
  'ttfb', 'tbt', 'fcp', 'tti', 'speed', 'page', 'device', 'type', 'tests',
]);

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