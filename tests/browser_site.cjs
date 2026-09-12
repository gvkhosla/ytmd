// Optional browser checks. Uses existing tools; never installs dependencies.
const assert = require('node:assert/strict');
const { mkdirSync } = require('node:fs');
const { resolve } = require('node:path');
const { chromium } = require(process.env.YTMD_PLAYWRIGHT_MODULE || 'playwright-core');
const root = resolve(__dirname, '..');
const base = process.argv[2] || 'http://127.0.0.1:8000/';
mkdirSync(root + '/.impeccable/review', { recursive: true });
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.YTMD_CHROMIUM || undefined, headless: true });
  try {
    for (const [name, width, height] of [['desktop', 1440, 1000], ['mobile', 390, 844], ['narrow-desktop', 1280, 900], ['small-mobile', 320, 740], ['zoom-equivalent', 720, 500]]) {
      const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: name === 'zoom-equivalent' ? 2 : 1, permissions: ['clipboard-read', 'clipboard-write'] });
      const page = await context.newPage(); const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      await page.goto(base, { waitUntil: 'networkidle' });
      await page.evaluate(() => document.fonts.ready);
      assert.equal(await page.locator('#answer-apply').isVisible(), true);
      assert.equal(await page.locator('.answer:visible').count(), 1);
      assert.equal(await page.locator('#source-count').textContent(), '4 of 8 passages');
      assert.equal(await page.locator('.source-help').isVisible(), true);
      assert.equal(await page.locator('.review-grid').evaluate(el => el.firstElementChild.className), width <= 800 ? 'answer-column' : 'source-column');
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, name + ' overflow');
      if (name === 'desktop' || name === 'mobile') await page.screenshot({ path: root + '/.impeccable/review/' + name + '.png', fullPage: true });
      await page.emulateMedia({ reducedMotion: 'reduce' });
      assert.equal(await page.locator('#answer-apply').evaluate(el => getComputedStyle(el).animationName), 'none');
      for (const mode of ['understand', 'learn', 'apply']) {
        await page.locator('#tab-' + mode).click();
        assert.equal(await page.locator('.answer:visible').count(), 1);
        assert.equal(await page.locator('#answer-' + mode).isVisible(), true);
        const links = page.locator('#answer-' + mode + ' .citation');
        for (let n = 0; n < await links.count(); n++) {
          const link = links.nth(n), target = await link.getAttribute('href');
          await link.click();
          assert.equal(await page.locator(target).isVisible(), true);
          assert.equal(await page.locator(target).evaluate(el => document.activeElement === el), true);
          assert.equal(await page.locator('.source-passage.is-selected').count(), 1);
          assert.equal(await page.locator(target).evaluate(el => {
            const r=el.getBoundingClientRect(), p=el.parentElement.getBoundingClientRect();
            return r.top < p.bottom && r.bottom > p.top;
          }), true, 'citation is outside its source scroller');
        }
      }
      await page.locator('#tab-apply').focus(); await page.keyboard.press('Home');
      assert.equal(await page.locator('#tab-understand').getAttribute('aria-selected'), 'true');
      await page.keyboard.press('ArrowRight');
      assert.equal(await page.locator('#tab-learn').getAttribute('aria-selected'), 'true');
      await page.keyboard.press('End');
      assert.equal(await page.locator('#tab-apply').getAttribute('aria-selected'), 'true');
      await page.keyboard.press('ArrowRight');
      assert.equal(await page.locator('#tab-understand').getAttribute('aria-selected'), 'true');
      await page.keyboard.press('ArrowLeft');
      assert.equal(await page.locator('#tab-apply').getAttribute('aria-selected'), 'true');
      await page.locator('[data-copy="agent-prompt"]').click();
      assert.match(await page.evaluate(() => navigator.clipboard.readText()), /^Install ytmd using/);
      await page.locator('.terminal-install > summary').click();
      await page.locator('[data-copy="install-code"]').click();
      assert.match(await page.evaluate(() => navigator.clipboard.readText()), /v0\.5\.0\/install\.sh/);
      await page.locator('[data-copy="linux-code"]').click();
      assert.match(await page.evaluate(() => navigator.clipboard.readText()), /^pipx install yt-dlp/);
      await page.locator('.setup-disclosure').nth(1).locator('summary').click();
      await page.locator('[data-copy="use-prompt"]').click();
      assert.match(await page.evaluate(() => navigator.clipboard.readText()), /accomplish \[my task\]/);
      await page.locator('.cli-reference > summary').click();
      for (const id of ['get-command', 'info-command', 'search-command', 'show-command']) {
        await page.locator('[data-copy="'+id+'"]').click();
        assert.equal(await page.evaluate(() => navigator.clipboard.readText()), await page.locator('#'+id).textContent());
      }
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, 'open disclosures overflow');
      await page.goto(base + '#source-420', { waitUntil: 'networkidle' });
      assert.equal(await page.locator('#answer-learn').isVisible(), true);
      assert.equal(await page.locator('#source-420').evaluate(el => document.activeElement === el), true);
      await page.setViewportSize({width: width > 800 ? 390 : 1440, height});
      await page.waitForFunction(() => document.querySelector('.review-grid').firstElementChild.className === (innerWidth <= 800 ? 'answer-column' : 'source-column'));
      assert.equal(await page.locator('#source-420').evaluate(el => document.activeElement === el), true);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      assert.deepEqual(errors, []);
      console.log(name + ': layout, modes, citations, keyboard, clipboard, disclosures, deep link, reduced motion passed');
      await context.close();
    }
    const nojs = await browser.newContext({ viewport: { width: 390, height: 844 }, javaScriptEnabled: false });
    const plain = await nojs.newPage(); await plain.goto(base, {waitUntil:'networkidle'});
    assert.equal(await plain.locator('.answer:visible').count(), 3);
    assert.equal(await plain.locator('#demo-controls').isVisible(), false);
    assert.equal(await plain.locator('[data-copy]:visible').count(), 0);
    await plain.locator('.terminal-install > summary').click();
    assert.equal(await plain.locator('#install-code').isVisible(), true);
    assert.equal(await plain.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    console.log('No JavaScript: all answers, passages, and install commands accessible');
    await nojs.close();
    const fallback = await browser.newContext();
    await fallback.addInitScript(() => Object.defineProperty(navigator, 'clipboard', { value: { writeText: async () => { throw new Error('denied'); } } }));
    const denied = await fallback.newPage(); await denied.goto(base, {waitUntil:'networkidle'});
    await denied.locator('[data-copy="agent-prompt"]').click();
    assert.match(await denied.locator('#copy-status').textContent(), /Text selected/);
    assert.match(await denied.evaluate(() => getSelection().toString()), /^Install ytmd/);
    assert.equal(await denied.locator('[data-copy="agent-prompt"]').isEnabled(), true);
    console.log('Clipboard denial: selectable fallback and restored button passed');
    await fallback.close();
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });
