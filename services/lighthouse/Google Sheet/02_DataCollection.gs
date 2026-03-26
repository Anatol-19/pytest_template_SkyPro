/**
 * @file 02_DataCollection.gs.js
 * @description ETL-слой: чтение сырых данных, агрегация, helper-sheets.
 *
 * Содержит:
 *  - Сбор сырых данных (collectRawPerfRows, normalizeRawRecord)
 *  - Ребилд Runs/Routes/Stability sheets
 *  - Парсинг записей (extractRunMetrics, parseRouteRecord, parseStabilityRecord)
 *  - Загрузка порогов из Config (loadMetricThresholds, populateFallbackThresholds)
 */



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