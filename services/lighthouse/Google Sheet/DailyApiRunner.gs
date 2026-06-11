const API_MONITOR_ENVIRONMENTS = {
  VRS_DEV: 'https://dev.vrsmash.com',
  VRS_TEST: 'https://test.vrsmash.com',
  VRS_STAGE: 'https://stage.vrsmash.com',
  VRS_PROD: 'https://www.vrsmash.com',
  VRP_DEV: 'https://d.vrporn.com',
  VRP_TEST: 'https://t.vrporn.com',
  VRP_STAGE: 'https://sg.vrporn.com',
  VRP_PROD: 'https://vrporn.com',
};

const API_MONITOR_ROUTES = {
  main: '/',
  s_video: '/pretty-petite-vr-pmv/',
  models: '/pornstars/?sort=latest',
  s_model: '/pornstars/samy-sun/',
  categories: '/categories/',
  s_category: '/tag/anal/',
  s_studio: '/studio/vrbangers/',
  dreams: '/camgirls/',
  s_dream: '/camgirls/model-vrporn/',
};

const API_MONITOR_DEVICES = ['desktop', 'mobile'];
const API_MONITOR_HEADERS = [
  'date', 'project', 'environment', 'source', 'sprint', 'run_id', 'tag', 'type', 'page', 'device', 'iterations',
  'P', 'LCP', 'INP', 'CLS', 'LCP_p90', 'INP_p90', 'CLS_p90', 'TBT', 'FCP', 'SI', 'TTI', 'TTFB'
];

function runDailyApiMonitoring() {
  const sprint = getCurrentSprintForApiMonitoring_();
  const tag = getDefaultApiMonitoringTag_();
  const environments = Object.keys(API_MONITOR_ENVIRONMENTS);
  return runApiMonitoringBatch_(environments, Object.keys(API_MONITOR_ROUTES), API_MONITOR_DEVICES, sprint, tag);
}

function runDailyApiMonitoringForVRP() {
  const sprint = getCurrentSprintForApiMonitoring_();
  const tag = getDefaultApiMonitoringTag_();
  const environments = Object.keys(API_MONITOR_ENVIRONMENTS).filter(env => env.startsWith('VRP_'));
  return runApiMonitoringBatch_(environments, Object.keys(API_MONITOR_ROUTES), API_MONITOR_DEVICES, sprint, tag);
}

function runDailyApiMonitoringForVRS() {
  const sprint = getCurrentSprintForApiMonitoring_();
  const tag = getDefaultApiMonitoringTag_();
  const environments = Object.keys(API_MONITOR_ENVIRONMENTS).filter(env => env.startsWith('VRS_'));
  return runApiMonitoringBatch_(environments, Object.keys(API_MONITOR_ROUTES), API_MONITOR_DEVICES, sprint, tag);
}

function runApiMonitoringForEnvironment(environment, sprint, tag) {
  return runApiMonitoringBatch_([
    environment
  ], Object.keys(API_MONITOR_ROUTES), API_MONITOR_DEVICES, sprint || getCurrentSprintForApiMonitoring_(), tag || getDefaultApiMonitoringTag_());
}

function setupDailyApiMonitoringTrigger() {
  const handler = 'runDailyApiMonitoring';
  const triggers = ScriptApp.getProjectTriggers();
  const exists = triggers.some(trigger => trigger.getHandlerFunction() === handler && trigger.getEventType() === ScriptApp.EventType.CLOCK);
  if (!exists) {
    ScriptApp.newTrigger(handler).timeBased().everyDays(1).atHour(8).create();
  }
}

function clearDailyApiMonitoringTriggers() {
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === 'runDailyApiMonitoring') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
}

function runApiMonitoringBatch_(environments, routeKeys, devices, sprint, tag) {
  const spreadsheet = getPerfSpreadsheet();
  const apiKey = getApiKeyForMonitoring_();
  const runId = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy.MM.dd-HHmmss');
  const dateValue = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy.MM.dd');
  const results = [];

  environments.forEach(environment => {
    const baseUrl = API_MONITOR_ENVIRONMENTS[environment];
    if (!baseUrl) {
      results.push(`skip ${environment}: base_url not configured`);
      return;
    }

    const targetSheet = resolveApiMonitoringSheetName_(environment);
    const sheet = getOrCreateSheet(spreadsheet, targetSheet);
    ensureApiMonitoringHeaders_(sheet);

    routeKeys.forEach(routeKey => {
      const routePath = API_MONITOR_ROUTES[routeKey];
      if (!routePath) {
        results.push(`skip ${environment}/${routeKey}: route not configured`);
        return;
      }
      const fullUrl = buildApiMonitoringUrl_(baseUrl, routePath);
      devices.forEach(device => {
        try {
          const row = fetchAndBuildApiMonitoringRow_(apiKey, environment, routeKey, fullUrl, device, sprint, tag, runId, dateValue);
          appendApiMonitoringRow_(sheet, row);
          results.push(`ok ${environment} ${device} ${routeKey}`);
        } catch (error) {
          results.push(`error ${environment} ${device} ${routeKey}: ${error}`);
        }
      });
    });
  });

  return results.join('\n');
}

function fetchAndBuildApiMonitoringRow_(apiKey, environment, routeKey, fullUrl, device, sprint, tag, runId, dateValue) {
  const endpoint = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed';
  const params = [
    `url=${encodeURIComponent(fullUrl)}`,
    `strategy=${encodeURIComponent(device)}`,
    'category=performance',
    'category=accessibility',
    'category=best-practices',
    'category=seo',
    `key=${encodeURIComponent(apiKey)}`,
  ].join('&');
  const response = UrlFetchApp.fetch(`${endpoint}?${params}`, { muteHttpExceptions: true });
  const code = response.getResponseCode();
  if (code < 200 || code >= 300) {
    throw new Error(`HTTP ${code}: ${response.getContentText().slice(0, 200)}`);
  }
  const payload = JSON.parse(response.getContentText());
  const lighthouse = payload.lighthouseResult || {};
  const audits = lighthouse.audits || {};
  const categories = lighthouse.categories || {};
  const project = environment.split('_')[0];
  const env = environment.split('_')[1] || environment;

  const lcp = normalizeTimeMetric_(audits['largest-contentful-paint'] && audits['largest-contentful-paint'].numericValue, 'lcp');
  const inpRaw = (audits['experimental-interaction-to-next-paint'] && audits['experimental-interaction-to-next-paint'].numericValue) ||
    (audits['max-potential-fid'] && audits['max-potential-fid'].numericValue) || null;
  const inp = normalizeTimeMetric_(inpRaw, 'inp');
  const cls = normalizeClsMetric_(audits['cumulative-layout-shift'] && audits['cumulative-layout-shift'].numericValue);
  const row = {
    date: dateValue,
    project,
    environment: env,
    source: 'API',
    sprint: sprint || '',
    run_id: runId,
    tag: tag || 'daily_api_1iter',
    type: 'API{1}',
    page: `=HYPERLINK("${fullUrl}"; "${routeKey}")`,
    device,
    iterations: 1,
    P: normalizeScore_(categories.performance && categories.performance.score),
    LCP: lcp,
    INP: inp,
    CLS: cls,
    LCP_p90: lcp,
    INP_p90: inp,
    CLS_p90: cls,
    TBT: normalizeTimeMetric_(audits['total-blocking-time'] && audits['total-blocking-time'].numericValue, 'tbt'),
    FCP: normalizeTimeMetric_(audits['first-contentful-paint'] && audits['first-contentful-paint'].numericValue, 'fcp'),
    SI: normalizeTimeMetric_(audits['speed-index'] && audits['speed-index'].numericValue, 'si'),
    TTI: normalizeTimeMetric_(audits['interactive'] && audits['interactive'].numericValue, 'tti'),
    TTFB: normalizeTimeMetric_(audits['server-response-time'] && audits['server-response-time'].numericValue, 'ttfb'),
  };
  return row;
}

function appendApiMonitoringRow_(sheet, row) {
  const headers = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), API_MONITOR_HEADERS.length)).getValues()[0];
  const normalizedHeaders = headers.map(value => value || '').filter(Boolean);
  const finalHeaders = normalizedHeaders.length ? normalizedHeaders : API_MONITOR_HEADERS.slice();
  const rowValues = finalHeaders.map(header => row[header] !== undefined ? row[header] : '');
  const startRow = Math.max(sheet.getLastRow() + 1, 4);
  sheet.getRange(startRow, 1, 1, rowValues.length).setValues([rowValues]);
}

function ensureApiMonitoringHeaders_(sheet) {
  const firstRow = sheet.getRange(1, 1, 1, API_MONITOR_HEADERS.length).getValues()[0];
  const hasHeader = firstRow.some(Boolean);
  if (!hasHeader) {
    sheet.getRange(1, 1, 1, API_MONITOR_HEADERS.length).setValues([API_MONITOR_HEADERS]);
  }
}

function resolveApiMonitoringSheetName_(environment) {
  const parts = String(environment || '').toUpperCase().split('_');
  const project = parts[0] || 'PROJECT';
  const env = parts[1] || 'PROD';
  return `${project} [${env}]`;
}

function buildApiMonitoringUrl_(baseUrl, routePath) {
  const origin = String(baseUrl || '').replace(/\/$/, '');
  const path = String(routePath || '').startsWith('/') ? routePath : `/${routePath}`;
  return `${origin}${path}`;
}

function normalizeTimeMetric_(value, key) {
  const num = parseNumber(value);
  if (num === null) {
    return '';
  }
  if (num > 0 && num < 50) {
    return Math.round(num * 1000);
  }
  return Math.round(num);
}

function normalizeClsMetric_(value) {
  const num = parseNumber(value);
  if (num === null) {
    return '';
  }
  return parseFloat(num.toFixed(4));
}

function normalizeScore_(value) {
  const num = parseNumber(value);
  if (num === null) {
    return '';
  }
  return Math.round(num * 100);
}

function getApiKeyForMonitoring_() {
  const scriptProps = PropertiesService.getScriptProperties();
  return scriptProps.getProperty('API_KEY') || scriptProps.getProperty('PAGESPEED_API_KEY') || '';
}

function getCurrentSprintForApiMonitoring_() {
  const scriptProps = PropertiesService.getScriptProperties();
  return scriptProps.getProperty('CURRENT_SPRINT') || '';
}

function getDefaultApiMonitoringTag_() {
  const scriptProps = PropertiesService.getScriptProperties();
  return scriptProps.getProperty('DAILY_API_TAG') || 'daily_api_1iter';
}
