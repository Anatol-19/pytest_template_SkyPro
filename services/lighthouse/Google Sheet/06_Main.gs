/**
 * @file 06_Main.gs.js
 * @description Точки входа: меню, триггеры, резолв spreadsheet.
 *
 * Содержит:
 *  - updatePerfAnalytics — главная точка входа (меню + кнопка)
 *  - onOpen — создание меню QA Dashboard
 *  - ensurePerfAnalyticsTriggers — управление триггерами
 *  - getPerfSpreadsheet — резолв активного spreadsheet
 */



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