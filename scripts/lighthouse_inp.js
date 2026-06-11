/**
 * Универсальный скрипт для измерения INP через Lighthouse timespan
 * 
 * Ищет первый интерактивный элемент и кликает по нему.
 * Использование:
 *   node scripts/lighthouse_inp.js <url> [device]
 */

const puppeteer = require('puppeteer');
const lighthouse = require('lighthouse').default;
const {writeFileSync} = require('fs');

// Селекторы для поиска интерактивных элементов (приоритет)
const INTERACTIVE_SELECTORS = [
  'button:not([disabled])',
  'a[href]:not([disabled])',
  'input[type="submit"]:not([disabled])',
  'input[type="button"]:not([disabled])',
  '[role="button"]:not([disabled])',
  '[onclick]:not([disabled])',
  '[tabindex]:not([tabindex="-1"]):not([disabled])'
];

async function findInteractiveElement(page) {
  for (const selector of INTERACTIVE_SELECTORS) {
    try {
      const elements = await page.$$(selector);
      if (elements.length > 0) {
        // Пропускаем скрытые элементы
        for (const el of elements) {
          const isVisible = await el.isIntersectingViewport();
          if (isVisible) {
            return el;
          }
        }
      }
    } catch (e) {
      // Селектор не найден, пробуем следующий
    }
  }
  return null;
}

async function runINPTest(url, device = 'desktop') {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Настройка устройства
  if (device === 'mobile') {
    await page.emulate(puppeteer.devices['Pixel 5']);
  } else {
    await page.setViewport({width: 1920, height: 1080});
  }
  
  // Запуск Lighthouse flow
  const flow = await lighthouse.startFlow(page, {
    name: 'INP Test',
    configContext: {
      settingsOverrides: {
        onlyCategories: ['performance'],
        skipAudits: ['uses-http2']  // Ускоряем тест
      }
    }
  });
  
  // 1. Navigation - загрузка страницы
  console.log(`[INFO] Navigation: ${url}`);
  await flow.navigate(url, {
    waitUntil: ['load', 'networkidle0']
  });
  
  // 2. Timespan - поиск и клик по интерактивному элементу
  console.log(`[INFO] Timespan: Looking for interactive element...`);
  const interactiveEl = await findInteractiveElement(page);
  
  if (interactiveEl) {
    await flow.startTimespan();
    
    try {
      // Скролл к элементу
      await interactiveEl.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
      
      // Клик
      console.log(`[INFO] Clicking on interactive element...`);
      await interactiveEl.click();
      await page.waitForTimeout(1000);
      
      await flow.endTimespan();
      console.log(`[INFO] Timespan completed`);
    } catch (e) {
      console.log(`[WARN] Click failed: ${e.message}`);
      await flow.endTimespan();
    }
  } else {
    console.log(`[WARN] No interactive element found, skipping timespan`);
  }
  
  await browser.close();
  
  // Генерация отчета
  const report = await flow.generateReport();
  const jsonReport = JSON.stringify(flow.getArtifacts(), null, 2);
  
  // Возвращаем результаты
  const results = {
    url: url,
    device: device,
    timestamp: new Date().toISOString(),
    inp: null
  };
  
  // Извлекаем INP из отчета
  const lhr = flow.getArtifacts()?.LighthouseResult;
  if (lhr?.audits?.['interaction-to-next-paint']) {
    results.inp = lhr.audits['interaction-to-next-paint'].numericValue;
  } else if (lhr?.audits?.['experimental-interaction-to-next-paint']) {
    results.inp = lhr.audits['experimental-interaction-to-next-paint'].numericValue;
  }
  
  return {results, report, jsonReport};
}

// CLI entry point
if (require.main === module) {
  const url = process.argv[2];
  const device = process.argv[3] || 'desktop';
  const outputDir = process.argv[4] || './temp_reports';
  
  if (!url) {
    console.error('Usage: node lighthouse_inp.js <url> [device] [outputDir]');
    process.exit(1);
  }
  
  runINPTest(url, device)
    .then(({results, report, jsonReport}) => {
      const fs = require('fs');
      const path = require('path');
      
      // Сохраняем JSON
      const outputPath = path.join(outputDir, `inp_${Date.now()}.json`);
      fs.mkdirSync(outputDir, {recursive: true});
      fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
      
      console.log(`[INFO] Results saved to: ${outputPath}`);
      console.log(`[INFO] INP: ${results.inp || 'N/A'} ms`);
      
      // Выводим JSON для парсинга
      console.log(JSON.stringify(results));
    })
    .catch(err => {
      console.error(`[ERROR] ${err.message}`);
      process.exit(1);
    });
}

module.exports = {runINPTest, findInteractiveElement};