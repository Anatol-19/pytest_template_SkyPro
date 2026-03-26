/**
 * @file 04_SprintAnalysis.gs.js
 * @description Sprint-сравнения: before/after, temporal lookups.
 *
 * Содержит:
 *  - Cross-env данные (buildCrossEnvRows, buildCrossEnvDeviceRows)
 *  - Resolve before/after (resolveBeforeAfterRoutes_, resolveBeforeAfterRuns_)
 *  - Previous run lookups (buildPreviousRunByEnvDevice_, buildPreviousRunLookup_)
 *  - Временная сортировка (sortRunIdsByDate_, toDate_)
 *  - Baseline (findBaselineRun)
 */



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

function resolveBeforeAfterRoutes_(filteredRoutes, allRoutes, sprintConfig) {
  // after — из отфильтрованных (UI filters), before — fallback из полного набора
  if (!allRoutes) { allRoutes = filteredRoutes; }
  const currentSprint = (sprintConfig && sprintConfig.currentSprint) || '';
  const prevIncrement = (sprintConfig && sprintConfig.previousIncrement) || '';

  let afterRoutes = filteredRoutes.filter(r => {
    if (currentSprint && toText(r.sprint).trim() !== currentSprint) return false;
    return hasTagToken_(r.tag, 'after');
  });
  if (!afterRoutes.length) {
    afterRoutes = filteredRoutes.filter(r => hasTagToken_(r.tag, 'after'));
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

function resolveBeforeAfterRuns_(filteredRuns, allRuns, sprintConfig) {
  if (!allRuns) { allRuns = filteredRuns; }
  const currentSprint = (sprintConfig && sprintConfig.currentSprint) || '';
  const prevIncrement = (sprintConfig && sprintConfig.previousIncrement) || '';

  let afterRuns = filteredRuns.filter(r => {
    if (currentSprint && toText(r.sprint).trim() !== currentSprint) return false;
    return hasTagToken_(r.tag, 'after');
  });
  if (!afterRuns.length) {
    afterRuns = filteredRuns.filter(r => hasTagToken_(r.tag, 'after'));
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
    const runIds = sortRunIdsByDate_(byKey[key]);
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
    const runIds = sortRunIdsByDate_(byKey[key]);
    if (runIds.length < 2) return;
    const prevRunId = runIds[runIds.length - 2];
    const prevRoutes = byKey[key][prevRunId];
    result[key] = aggregateRouteMetrics(prevRoutes);
  });
  return result;
}

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
    const runIds = sortRunIdsByDate_(byKey[key]);
    if (runIds.length < 2) return;
    const prevRunId = runIds[runIds.length - 2];
    result[key] = byKey[key][prevRunId];
  });
  return result;
}

function sortRunIdsByDate_(runGroups) {
  return Object.keys(runGroups).sort((a, b) => {
    const dateA = getEarliestDate_(runGroups[a]);
    const dateB = getEarliestDate_(runGroups[b]);
    return dateA - dateB;
  });
}

function getEarliestDate_(records) {
  let earliest = Infinity;
  records.forEach(r => {
    const d = toDate_(r.date);
    if (d && d.getTime() < earliest) {
      earliest = d.getTime();
    }
  });
  return earliest === Infinity ? 0 : earliest;
}

function toDate_(value) {
  if (!value) return null;
  if (value instanceof Date) return value;
  const parsed = new Date(value);
  return isNaN(parsed.getTime()) ? null : parsed;
}

function findBaselineRun(runs, index) {
  for (let i = index - 1; i >= 0; i--) {
    if (!runs[i].tag) {
      return runs[i];
    }
  }
  return null;
}