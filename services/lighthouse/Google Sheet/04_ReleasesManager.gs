/**
 * @file 04_ReleasesManager.gs.js
 * @description Управление списком релизов/спринтов.
 *
 * Содержит:
 *  - Чтение списка релизов (readReleasesList)
 *  - Поиск текущего/предыдущего спринта (findCurrentSprint, findPreviousSprint)
 *  - Построение baseline для сравнения (findBaselineForSprint)
 *  - История трендов (buildSprintTrendData)
 */

const RELEASES_SHEET = 'Releases';
const RELEASE_STATUS = {
  DONE: '✅ Done',
  IN_PROGRESS: '🟡 In Progress',
  PLANNED: '⬜ Planned',
};

/**
 * Читает список релизов из листа Releases.
 * @returns {Array} Массив объектов {name, startDate, endDate, status, rollout}
 */
function readReleasesList(ss) {
  const sheet = ss.getSheetByName(RELEASES_SHEET);
  if (!sheet) {
    Logger.log('[Releases] Лист Releases не найден');
    return [];
  }
  
  const records = readSheetRecords(sheet);
  const releases = records.map(r => {
    const name = toText(getRecordValue(r, ['Release', 'release', 'name'])).trim();
    const startDate = parseDate(getRecordValue(r, ['Start Date', 'start_date', 'start']));
    const endDate = parseDate(getRecordValue(r, ['End Date', 'end_date', 'end']));
    const status = toText(getRecordValue(r, ['Status', 'status'])).trim();
    
    return {
      name,
      startDate,
      endDate,
      status,
      rollout: {
        DEV: getRecordValue(r, ['DEV', 'dev']) === true,
        TEST: getRecordValue(r, ['TEST', 'test']) === true,
        STAGE: getRecordValue(r, ['STAGE', 'stage']) === true,
        PROD: getRecordValue(r, ['PROD', 'prod']) === true,
      },
    };
  }).filter(r => r.name); // Фильтруем пустые строки
  
  // Сортировка по дате начала (новые сверху)
  return releases.sort((a, b) => {
    if (!a.startDate && !b.startDate) return 0;
    if (!a.startDate) return 1;
    if (!b.startDate) return -1;
    return b.startDate - a.startDate;
  });
}

/**
 * Находит текущий спринт (In Progress).
 * @param {Array} releases - Отсортированный список релизов
 * @returns {Object|null} Объект спринта или null
 */
function findCurrentSprint(releases) {
  return releases.find(r => r.status.includes('In Progress')) || null;
}

/**
 * Находит предыдущий спринт (первый Done после текущего).
 * @param {Array} releases - Отсортированный список релизов
 * @param {Object} currentSprint - Текущий спринт
 * @returns {Object|null} Объект спринта или null
 */
function findPreviousSprint(releases, currentSprint) {
  if (!currentSprint) return null;
  
  const currentIndex = releases.findIndex(r => r.name === currentSprint.name);
  if (currentIndex === -1) return null;
  
  // Ищем первый Done после текущего
  for (let i = currentIndex + 1; i < releases.length; i++) {
    if (releases[i].status.includes('Done')) {
      return releases[i];
    }
  }
  
  return null;
}

/**
 * Находит N предыдущих спринтов для анализа.
 * @param {Array} releases - Отсортированный список релизов
 * @param {Object} currentSprint - Текущий спринт
 * @param {number} count - Количество спринтов
 * @returns {Array} Массив спринтов
 */
function findPreviousSprints(releases, currentSprint, count = 3) {
  if (!currentSprint) return [];
  
  const currentIndex = releases.findIndex(r => r.name === currentSprint.name);
  if (currentIndex === -1) return [];
  
  const result = [];
  for (let i = currentIndex + 1; i < releases.length && result.length < count; i++) {
    result.push(releases[i]);
  }
  
  return result;
}

/**
 * Строит baseline для сравнения текущего спринта.
 * @param {Object} currentSprint - Текущий спринт
 * @param {Array} releases - Список релизов
 * @param {Array} allRuns - Все запуски (Runs sheet)
 * @param {Array} allRoutes - Все роуты (Routes sheet)
 * @returns {Object} {source, runs, label}
 */
function findBaselineForSprint(currentSprint, releases, allRuns, allRoutes) {
  const currentSprintName = currentSprint.name;
  
  // ПРИОРИТЕТ 1: before текущего спринта
  const currentBefore = allRoutes.filter(r => 
      toText(r.sprint).trim() === currentSprintName && hasTagToken_(r.tag, 'before')
  );
  if (currentBefore.length) {
      Logger.log(`[Baseline] Найдено ${currentBefore.length} before замеров для ${currentSprintName}`);
      return { 
          source: 'current_sprint_before', 
          runs: currentBefore,
          label: `Before текущего спринта (${currentSprintName})`
      };
  }
  
  // ПРИОРИТЕТ 2: after предыдущего спринта (из Releases)
  const previousSprint = findPreviousSprint(releases, currentSprint);
  if (previousSprint) {
      const previousAfter = allRoutes.filter(r => 
          toText(r.sprint).trim() === previousSprint.name && hasTagToken_(r.tag, 'after')
      );
      if (previousAfter.length) {
          Logger.log(`[Baseline] Найдено ${previousAfter.length} after замеров для ${previousSprint.name}`);
          return { 
              source: 'previous_sprint_after', 
              runs: previousAfter,
              label: `After предыдущего спринта (${previousSprint.name})`
          };
      }
  }
  
  // ПРИОРИТЕТ 3: последний after из N предыдущих спринтов
  const previousSprints = findPreviousSprints(releases, currentSprint, 3);
  for (const sprint of previousSprints) {
      const sprintAfter = allRoutes.filter(r => 
          toText(r.sprint).trim() === sprint.name && hasTagToken_(r.tag, 'after')
      );
      if (sprintAfter.length) {
          // Берём последний замер этого спринта
          const sorted = sortRunIdsByDate_(groupRunsByRunId_(sprintAfter));
          if (sorted.length) {
              const latestRunId = sorted[sorted.length - 1];
              const latestRuns = sprintAfter.filter(r => toText(r.runId).trim() === latestRunId);
              Logger.log(`[Baseline] Найдено ${latestRuns.length} замеров для ${sprint.name} (latest run)`);
              return { 
                  source: `release_${sprint.name}_after`, 
                  runs: latestRuns,
                  label: `Последний after ${sprint.name}`
              };
          }
      }
  }
  
  // ПРИОРИТЕТ 4: previous run fallback (temporal)
  Logger.log(`[Baseline] Fallback на previous run`);
  return { 
      source: 'previous_run_fallback', 
      runs: buildPreviousRunByEnvDevice_(allRoutes),
      label: 'Предыдущий замер (fallback)'
  };
}

/**
 * Группирует запуски по run_id.
 * @param {Array} runs - Массив запусков
 * @returns {Object} Объект {run_id: [runs]}
 */
function groupRunsByRunId_(runs) {
  const byId = {};
  runs.forEach(run => {
    const runId = toText(run.runId || run.run_id || '').trim();
    if (!runId) return;
    if (!byId[runId]) byId[runId] = [];
    byId[runId].push(run);
  });
  return byId;
}

/**
 * Строит данные для графика тренда метрик по спринтам.
 * @param {Array} releases - Список релизов
 * @param {Array} allRoutes - Все роуты
 * @param {string} metric - Метрика ('lcp', 'inp', 'cls')
 * @returns {Array} Данные для графика [['Release', 'Value', ...], ...]
 */
function buildSprintTrendData(releases, allRoutes, metric = 'lcp') {
  const trendData = [['Release', 'LCP', 'INP', 'CLS', 'TTFB']];
  
  // Проходим в обратном порядке (старые → новые)
  for (let i = releases.length - 1; i >= 0; i--) {
    const release = releases[i];
    if (!release.status.includes('Done') && !release.status.includes('In Progress')) {
      continue;
    }
    
    const afterRoutes = allRoutes.filter(r => 
        toText(r.sprint).trim() === release.name && hasTagToken_(r.tag, 'after')
    );
    
    if (afterRoutes.length) {
      const metrics = aggregateRouteMetrics(afterRoutes);
      trendData.push([
        release.name,
        metrics.lcp || 0,
        metrics.inp || 0,
        metrics.cls || 0,
        metrics.ttfb || 0,
      ]);
    }
  }
  
  return trendData;
}

/**
 * Создаёт или обновляет лист Releases с шапкой.
 * @param {Spreadsheet} ss - Активный spreadsheet
 */
function ensureReleasesSheet(ss) {
  let sheet = ss.getSheetByName(RELEASES_SHEET);
  
  if (!sheet) {
    sheet = ss.insertSheet(RELEASES_SHEET);
    const headers = [
      'Release', 'Start Date', 'End Date', 'Status',
      'DEV', 'TEST', 'STAGE', 'PROD'
    ];
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold').setBackground('#ECEFF1');
    sheet.setFrozenRows(1);
    
    // Добавляем пример данных
    const exampleData = [
      ['Release 18-03', '=DATEVALUE("18-03-2026")', '=B2+13', '✅ Done', TRUE, TRUE, TRUE, TRUE],
      ['Release 01-04', '=DATEVALUE("01-04-2026")', '=B3+13', '🟡 In Progress', TRUE, TRUE, FALSE, FALSE],
      ['Release 15-04', '=DATEVALUE("15-04-2026")', '=B4+13', '⬜ Planned', '', '', '', ''],
    ];
    sheet.getRange(2, 1, exampleData.length, exampleData[0].length).setValues(exampleData);
    
    // Добавляем формулу для Status
    sheet.getRange('D2').setFormula(
      '=IF(COUNTIF(E2:H2, TRUE)=4, "✅ Done", IF(COUNTIF(E2:H2, TRUE)>0, "🟡 In Progress", "⬜ Planned"))'
    );
    
    // Auto-resize columns
    sheet.autoResizeColumns(1, 8);
    
    Logger.log('[Releases] Лист Releases создан с примером данных');
  }
  
  return sheet;
}

/**
 * Парсит дату из значения ячейки.
 * @param {*} value - Значение
 * @returns {Date|null} Дата или null
 */
function parseDate(value) {
  if (!value) return null;
  if (value instanceof Date) return value;
  
  // Попытка парсинга строки
  const parsed = new Date(value);
  if (!isNaN(parsed.getTime())) {
    return parsed;
  }
  
  return null;
}
