// ======================================
// PERF QA FORMATTER v6 (base layout)
// ======================================

const PERF_SHEETS = [
  'VRP [PROD]','VRP [STAGE]','VRP [TEST]','VRP [DEV]',
  'VRS [PROD]','VRS [STAGE]','VRS [TEST]','VRS [DEV]'
]

const CRUX_SHEET = 'CrUX'
const FORMATTER_CONFIG_SHEET = 'Config'

const TECH_HEADERS = [
  'date','type','page','device',
  'P',
  'LCP','INP','CLS',
  'LCP_p90','INP_p90','CLS_p90',
  'TBT','FCP','SI','TTI','TTFB',
  'run_id','tag'
]

const UI_HEADERS = [
  'Date','Type','Page','Device',
  'Score',
  'LCP','INP','CLS',
  'LCP p90','INP p90','CLS p90',
  'TBT','FCP','Speed Index','TTI','TTFB',
  'run_id','tag'
]

const WIDTHS = [
  100,85,145,90,
  50,
  60,55,55,
  60,55,55,
  60,60,85,70,70,
  115,145
]

const CRUX_HEADERS = [
  'date','project','sprint','page','device',
  'LCP','FCP','INP','CLS',
  'LCP_good_pct','FCP_good_pct','INP_good_pct','CLS_good_pct',
  'TTFB','run_id','tag'
]

const CRUX_UI_HEADERS = [
  'Date','Project','Sprint','Page','Device',
  'LCP','FCP','INP','CLS',
  'LCP good %','FCP good %','INP good %','CLS good %',
  'TTFB','run_id','tag'
]

const CRUX_WIDTHS = [
  100,100,100,145,70,
  65,65,65,65,
  65,65,65,65,
  75,115,145
]

const DEFAULT_METRIC_FALLBACKS = [
  { metric: 'paint', good: 2500, poor: 4000, direction: 'low_good' },
  { metric: 'speed', good: 3400, poor: 5800, direction: 'low_good' },
  { metric: 'interactive', good: 3800, poor: 7300, direction: 'low_good' },
  { metric: 'network', good: 800, poor: 1800, direction: 'low_good' },
];

function setupPerfSheets(){
  const ss = SpreadsheetApp.getActiveSpreadsheet()
  PERF_SHEETS.forEach(name=>{
    let sheet = ss.getSheetByName(name)
    if(!sheet){ sheet = ss.insertSheet(name) }
    buildLayout(sheet)
  })
  setupCruxSheet(ss)
}

function buildLayout(sheet){
  sheet.clear()
  sheet.getRange(1,1,1,TECH_HEADERS.length).setValues([TECH_HEADERS])
  sheet.hideRows(1)

  sheet.getRange('E2').setValue('Perf')
  sheet.getRange('F2:H2').merge().setValue('Core Web Vitals')
  sheet.getRange('I2:K2').merge().setValue('Core Web Vitals p90')
  sheet.getRange('L2').setValue('Blocking')
  sheet.getRange('M2').setValue('Paint')
  sheet.getRange('N2').setValue('Speed')
  sheet.getRange('O2').setValue('Interactive')
  sheet.getRange('P2').setValue('Network')

  sheet.getRange(3,1,1,UI_HEADERS.length).setValues([UI_HEADERS])

  sheet.getRange('A2:R3')
    .setBackground('#263238')
    .setFontColor('white')
    .setFontWeight('bold')
    .setHorizontalAlignment('center')
    .setVerticalAlignment('middle')

  sheet.getRange('F3:H3').setBackground('#A5D6A7')
  sheet.getRange('I3:K3').setBackground('#90CAF9')

  sheet.setFrozenRows(3)
  WIDTHS.forEach((w,i)=> sheet.setColumnWidth(i+1,w))

  sheet.getRange('A4:R2000')
    .applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY,false,false)
    .setHorizontalAlignment('center')

  sheet.getRange('C4:C2000').setFontColor('#1565C0')
  applyConditionalFormatting(sheet)
}

function applyConditionalFormatting(sheet){
  if (!sheet) {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    sheet = ss ? ss.getActiveSheet() : null;
  }
  if (!sheet) {
    return;
  }
  const thresholds = loadMetricThresholds();
  if (!thresholds.length) {
    sheet.setConditionalFormatRules([]);
    return;
  }
  const headerRow = sheet.getRange(1,1,1,sheet.getMaxColumns()).getValues()[0] || [];
  const headerMap = {};
  headerRow.forEach((cell, index)=>{
    if (!cell) return;
    headerMap[normalizeHeader(cell)] = index + 1;
  });
  const dataHeight = Math.max(sheet.getMaxRows() - 3, 1);
  const rules = [];
  thresholds.forEach(metricRule=>{
    const column = findMetricColumn(metricRule.metric, headerMap);
    if (!column) return;
    const range = sheet.getRange(4, column, dataHeight);
    buildMetricFormatting(range, sheet, metricRule, rules);
  });
  sheet.setConditionalFormatRules(rules);
}

function setupCruxSheet(ss){
  let sheet = ss.getSheetByName(CRUX_SHEET)
  if(!sheet){ sheet = ss.insertSheet(CRUX_SHEET) }
  buildCruxLayout(sheet)
}

function buildCruxLayout(sheet){
  sheet.clear()
  sheet.getRange(1,1,1,CRUX_HEADERS.length).setValues([CRUX_HEADERS])
  sheet.hideRows(1)

  sheet.getRange('F2:I2').merge().setValue('CWV p75')
  sheet.getRange('J2:M2').merge().setValue('CWV good %')
  sheet.getRange('N2').setValue('Network')

  sheet.getRange(3,1,1,CRUX_UI_HEADERS.length).setValues([CRUX_UI_HEADERS])

  sheet.getRange(`A2:${colLetter(CRUX_HEADERS.length)}3`)
    .setBackground('#1B1F24')
    .setFontColor('white')
    .setFontWeight('bold')
    .setHorizontalAlignment('center')
    .setVerticalAlignment('middle')

  sheet.setFrozenRows(3)
  CRUX_WIDTHS.forEach((w,i)=> sheet.setColumnWidth(i+1,w))

  sheet.getRange(`A4:${colLetter(CRUX_HEADERS.length)}2000`)
    .applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY,false,false)
    .setHorizontalAlignment('center')

  sheet.getRange('D4:D2000').setFontColor('#1565C0')
  applyCruxFormatting(sheet)
}

function applyCruxFormatting(sheet){
  let rules=[]
  rules.push(colorRule(sheet,'F4:F2000',2500,null,'#C8E6C9','less'))
  rules.push(colorRule(sheet,'F4:F2000',4000,null,'#FFCDD2','greater'))
  rules.push(colorRule(sheet,'F4:F2000',2500,4000,'#FFF9C4','between'))

  rules.push(colorRule(sheet,'G4:G2000',1800,null,'#C8E6C9','less'))
  rules.push(colorRule(sheet,'G4:G2000',3000,null,'#FFCDD2','greater'))

  rules.push(colorRule(sheet,'H4:H2000',200,null,'#C8E6C9','less'))
  rules.push(colorRule(sheet,'H4:H2000',500,null,'#FFCDD2','greater'))

  rules.push(colorRule(sheet,'I4:I2000',0.1,null,'#C8E6C9','less'))
  rules.push(colorRule(sheet,'I4:I2000',0.25,null,'#FFCDD2','greater'))

  rules.push(colorRule(sheet,'J4:M2000',75,null,'#C8E6C9','greater'))
  rules.push(colorRule(sheet,'J4:M2000',50,null,'#FFCDD2','less'))

  rules.push(colorRule(sheet,'N4:N2000',800,null,'#C8E6C9','less'))
  rules.push(colorRule(sheet,'N4:N2000',1800,null,'#FFCDD2','greater'))

  sheet.setConditionalFormatRules(rules)
}

function colorRule(sheet,range,a,b,color,type){
  const target = typeof range === 'string' ? sheet.getRange(range) : range;
  const builder = SpreadsheetApp.newConditionalFormatRule().setRanges([target]);
  switch(type){
    case 'less':
    case 'less_equal':
      if (a !== null && a !== undefined) builder.whenNumberLessThanOrEqualTo(a);
      break;
    case 'greater':
      if (b !== null && b !== undefined) builder.whenNumberGreaterThan(b);
      break;
    case 'greater_equal':
      if (a !== null && a !== undefined) builder.whenNumberGreaterThanOrEqualTo(a);
      break;
    case 'between':
      if (a !== null && b !== null) builder.whenNumberBetween(a,b);
      break;
  }
  return builder.setBackground(color).build();
}

function loadMetricThresholds(){
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(FORMATTER_CONFIG_SHEET);
  if (!sheet) return [];
  const values = sheet.getDataRange().getValues();
  if (values.length < 2) return [];
  const headers = values[0].map(normalizeHeader);
  const metricIdx = headers.indexOf('metric');
  const goodIdx = headers.indexOf('good');
  const poorIdx = headers.indexOf('poor');
  const directionIdx = headers.indexOf('direction');
  const entries = [];
  const seen = new Set();
  for (let i=1; i<values.length; i++){
    const row = values[i];
    const metric = row[metricIdx];
    if (!metric) continue;
    const good = toNumber(row[goodIdx]);
    const poor = toNumber(row[poorIdx]);
    const direction = row[directionIdx] ? row[directionIdx].toString().trim().toLowerCase() : 'low_good';
    seen.add(normalizeHeader(metric.toString()));
    entries.push({ metric: metric.toString(), good, poor, direction });
  }
  DEFAULT_METRIC_FALLBACKS.forEach(fallback => {
    const normalized = normalizeHeader(fallback.metric);
    if (seen.has(normalized)) {
      return;
    }
    entries.push({
      metric: fallback.metric,
      good: fallback.good,
      poor: fallback.poor,
      direction: fallback.direction,
    });
    seen.add(normalized);
  });
  return entries;
}

function buildMetricFormatting(range,sheet,metricRule,rules){
  const direction = metricRule.direction || 'low_good';
  const good = metricRule.good;
  const poor = metricRule.poor;
  if (direction === 'high_good'){
    if (good !== null) rules.push(colorRule(sheet,range,good,null,'#C8E6C9','greater_equal'));
    if (poor !== null) rules.push(colorRule(sheet,range,null,poor,'#FFCDD2','less'));
    if (good !== null && poor !== null){
      const low = Math.min(good,poor);
      const high = Math.max(good,poor);
      rules.push(colorRule(sheet,range,low,high,'#FFF9C4','between'));
    }
  } else {
    if (good !== null) rules.push(colorRule(sheet,range,good,null,'#C8E6C9','less_equal'));
    if (poor !== null) rules.push(colorRule(sheet,range,null,poor,'#FFCDD2','greater'));
    if (good !== null && poor !== null) rules.push(colorRule(sheet,range,good,poor,'#FFF9C4','between'));
  }
}

function findMetricColumn(metric, headerMap) {
  const normalized = normalizeHeader(metric);
  const candidates = new Set();
  if (normalized) {
    candidates.add(normalized);
    candidates.add(`${normalized}_p90`);
    candidates.add(`p90_${normalized}`);
    candidates.add(`${normalized}p90`);
  }
  for (const candidate of candidates) {
    if (candidate && headerMap[candidate]) {
      return headerMap[candidate];
    }
  }
  return null;
}

function normalizeHeader(value){
  if (value === null || value === undefined) return '';
  return value.toString().trim().toLowerCase().replace(/\s+/g,'_').replace(/[^\w_]/g,'');
}

function toNumber(value) {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  if (typeof value === 'number') {
    return value;
  }
  const cleaned = value.toString().trim().replace(',', '.').replace(/[^\d.\-]/g, '');
  return cleaned ? parseFloat(cleaned) : null;
}

function colLetter(n){
  let s='';
  while(n){ let m=(n-1)%26; s=String.fromCharCode(65+m)+s; n=Math.floor((n-1)/26); }
  return s;
}
