// Optional browser checks using existing tools; never installs dependencies.
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
    for (const [name, width, height] of [['desktop',1440,1000], ['mobile',390,844], ['small-mobile',320,740], ['zoom-equivalent',720,500]]) {
      const context = await browser.newContext({viewport:{width,height}, deviceScaleFactor:name === 'zoom-equivalent' ? 2 : 1, permissions:['clipboard-read','clipboard-write']});
      const page = await context.newPage(); const errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      await page.goto(base,{waitUntil:'networkidle'});
      await page.evaluate(()=>document.fonts.ready);
      const words=await page.evaluate(()=>document.body.innerText.trim().split(/\s+/).length);
      assert.ok(words<=230, 'Default copy grew beyond the single-use-case brief: '+words);
      assert.equal(await page.locator('[role="tab"]').count(),0);
      assert.equal(await page.locator('button:visible').count(),1);
      assert.equal(await page.locator('#sources').evaluate(el=>el.open),false);
      assert.equal(await page.locator('#install').evaluate(el=>el.open),false);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      if (name==='desktop'||name==='mobile') await page.screenshot({path:root+'/.impeccable/review/'+name+'.png',fullPage:true});
      await page.emulateMedia({reducedMotion:'reduce'});
      assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).scrollBehavior),'auto');
      for (const id of ['source-60','source-120','source-240']) {
        await page.locator('#sources').evaluate(el=>el.open=false);
        await page.locator('.citation[href="#'+id+'"]').click();
        assert.equal(await page.locator('#sources').evaluate(el=>el.open),true);
        assert.equal(await page.locator('#'+id).evaluate(el=>document.activeElement===el),true);
      }
      await page.locator('.citation').first().focus(); await page.keyboard.press('Enter');
      assert.equal(await page.locator('#source-60').evaluate(el=>document.activeElement===el),true);
      await page.locator('[data-copy]').click();
      assert.match(await page.evaluate(()=>navigator.clipboard.readText()), /^Install ytmd using/);
      // Copying the setup prompt must not add a screenful of instructions to the page.
      assert.equal(await page.locator('#install').evaluate(el=>el.open),false);
      await page.locator('#install summary').click();
      assert.equal(await page.locator('#agent-prompt').isVisible(),true);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      await page.goto(base+'#source-240',{waitUntil:'networkidle'});
      assert.equal(await page.locator('#sources').evaluate(el=>el.open),true);
      assert.equal(await page.locator('#source-240').evaluate(el=>document.activeElement===el),true);
      assert.deepEqual(errors,[]);
      console.log(name+': '+words+' default words; citations, keyboard, copy, disclosures, deep links, layout passed');
      await context.close();
    }
    const nojs=await browser.newContext({viewport:{width:390,height:844},javaScriptEnabled:false});
    const plain=await nojs.newPage(); await plain.goto(base,{waitUntil:'networkidle'});
    assert.equal(await plain.locator('button:visible').count(),0);
    await plain.locator('#install summary').click();
    assert.equal(await plain.locator('#agent-prompt').isVisible(),true);
    await plain.locator('.citation').first().click();
    assert.equal(await plain.locator('#source-60').isVisible(),true);
    assert.equal(await plain.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    console.log('No JavaScript: setup and native source navigation passed');
    await nojs.close();
    const fallback=await browser.newContext();
    await fallback.addInitScript(()=>Object.defineProperty(navigator,'clipboard',{value:{writeText:async()=>{throw new Error('denied');}}}));
    const denied=await fallback.newPage(); await denied.goto(base,{waitUntil:'networkidle'});
    await denied.locator('[data-copy]').click();
    assert.equal(await denied.locator('#install').evaluate(el=>el.open),true);
    assert.match(await denied.evaluate(()=>getSelection().toString()),/^Install ytmd/);
    assert.match(await denied.locator('#copy-status').textContent(),/Text selected/);
    assert.equal(await denied.locator('[data-copy]').isEnabled(),true);
    console.log('Clipboard denial: instructions revealed, selected, and recoverable');
    await fallback.close();
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
