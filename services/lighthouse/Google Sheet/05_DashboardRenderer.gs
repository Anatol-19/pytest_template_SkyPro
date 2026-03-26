/**
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
 */



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
    renderMetricBreakdownBlock(sheet, LAYOUT.METRIC_BREAKDOWN.row, effectiveRuns, effectiveRoutes, projectRuns, projectRoutes, thresholds, sprintConfig);
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

function showEmptyMessage(sheet, project) {
  clearDashboardRenderArea(sheet);
  const sprintConfig = readSprintMetadata(sheet);
  prepareDashboardControls(sheet, project, buildDefaultFilters(project, [], [], sprintConfig), [], sprintConfig);
  const prefix = project ? `${project}: ` : '';
  sheet.getRange(CONTROL_RENDER_START_ROW, 1).setValue(`${prefix}данных ещё нет, запусти проверки Lighthouse и обнови дашборд.`).setFontSize(14).setFontWeight('bold');
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

function renderMetricBreakdownBlock(sheet, row, effectiveRuns, effectiveRoutes, allRuns, allRoutes, thresholds, sprintConfig) {
  const startRow = row;
  row = renderBlockHeader(sheet, row, 'БЛОК — METRIC BREAKDOWN', 7);

  // ═══ Route-level метрики (LCP, INP, CLS, TTFB) — per page+device ═══
  // after из отфильтрованных effectiveRoutes, before fallback из allRoutes
  const resolved = resolveBeforeAfterRoutes_(effectiveRoutes, allRoutes, sprintConfig);

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
  const resolvedRuns = resolveBeforeAfterRuns_(effectiveRuns, allRuns, sprintConfig);

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

function findLatestCruxForProject(project, cruxRows) {
  const projectRows = cruxRows.filter(row => matchesProject(row.project, project) && normalizeEnvironment(row.environment) === 'PROD');
  return projectRows.length ? projectRows[projectRows.length - 1] : null;
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