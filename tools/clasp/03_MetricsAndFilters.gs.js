/**
 * @file 03_MetricsAndFilters.gs.js
 * @description Аналитическое ядро: оценка метрик, фильтрация, контекст.
 *
 * Содержит:
 *  - Оценка метрик (assessMetricStatus, colorMetricCell_, metricDelta)
 *  - Агрегация (aggregateRouteMetrics, aggregateRunMetric_)
 *  - Sprint metadata и фильтры (readSprintMetadata, applyRunFilters, applyRouteFilters)
 *  - Контекст и алерты (buildContextMetrics, buildAlerts, buildDiagnostics)
 *  - Здоровье роутов (evaluateRouteHealth, buildDeduplicatedRouteHealth)
 */



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

function shouldRenderCrossEnvBlock(filters) {
  const mode = normalizeDashboardMode_(filters.mode);
  const environment = toText(filters.environment).trim().toUpperCase();
  if (mode === 'ENVIRONMENT') {
    return !environment || environment === 'ALL';
  }
  return mode === 'SPRINT' || mode === 'ROUTE_CROSS_ENV' || mode === 'EXPERIMENT';
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