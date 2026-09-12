// Optional browser checks using existing tools; never installs dependencies.
const assert = require('node:assert/strict');
const { mkdirSync, readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const { chromium } = require(process.env.YTMD_PLAYWRIGHT_MODULE || 'playwright-core');
const root = resolve(__dirname, '..');
const base = process.argv[2] || 'http://127.0.0.1:8000/';
const videos = JSON.parse(readFileSync(root + '/examples/videos.json', 'utf8')).videos;
mkdirSync(root + '/.impeccable/review', { recursive: true });
function contrast(a,b) {
  const luminance=hex=>{
    const rgb=hex.slice(1).match(/../g).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
    return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722;
  };
  const x=luminance(a), y=luminance(b);
  return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);
}
async function checkContrast(page) {
  const colors=await page.evaluate(()=>{
    const css=getComputedStyle(document.documentElement);
    return Object.fromEntries(['paper','ink','muted','green','green-hover','selected','on-green','overlay','on-overlay'].map(k=>[k,css.getPropertyValue('--'+k).trim()]));
  });
  for(const [fg,bg] of [['ink','paper'],['muted','paper'],['green','paper'],['green','selected'],['on-green','green'],['on-green','green-hover'],['on-overlay','overlay']]) {
    assert.ok(contrast(colors[fg],colors[bg])>=4.5, `${fg}/${bg} contrast below AA`);
  }
}
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.YTMD_CHROMIUM || undefined, headless: true });
  try {
    for (const [name, width, height] of [['desktop',1440,1000], ['mobile',390,844], ['small-mobile',320,740], ['zoom-equivalent',720,500]]) {
      const context = await browser.newContext({viewport:{width,height}, deviceScaleFactor:name === 'zoom-equivalent' ? 2 : 1, colorScheme:'light', permissions:['clipboard-read','clipboard-write']});
      const page = await context.newPage(); const errors=[], external=[];
      page.on('pageerror',e=>errors.push(e.message));
      page.on('request',r=>{if(new URL(r.url()).origin!==new URL(base).origin) external.push(r.url());});
      await page.goto(base,{waitUntil:'networkidle'});
      await page.evaluate(()=>document.fonts.ready);
      assert.equal(await page.locator('h1').innerText(),'Put YouTube videos\nto work');
      const words=await page.evaluate(()=>document.body.innerText.trim().split(/\s+/).length);
      assert.ok(words<=400, 'Default copy grew beyond the six-video brief: '+words);
      assert.equal(await page.locator('[role="tab"], iframe, input').count(),0);
      assert.equal(await page.locator('button:visible').count(),2);
      assert.equal(await page.locator('[data-copy]:visible').count(),1);
      await checkContrast(page);
      assert.equal(await page.locator('.thumbnail').count(),6);
      assert.equal(await page.locator('details[open]').count(),0);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      // Load lazy images before capturing; all images must be real, local, and unbroken.
      for (const img of await page.locator('.thumbnail img').all()) {
        await img.scrollIntoViewIfNeeded();
        await img.evaluate(el=>el.decode());
        assert.ok(await img.evaluate(el=>el.naturalWidth>=320));
      }
      await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
      if (name==='desktop'||name==='mobile') {
        assert.ok((await page.locator('.thumbnail').first().boundingBox()).y < height, 'First thumbnail should appear in the initial viewport');
        await page.screenshot({path:root+'/.impeccable/review/'+name+'.png',fullPage:true});
      }
      await page.locator('#theme-toggle').focus(); await page.keyboard.press('Enter');
      assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
      assert.equal(await page.locator('#theme-toggle').getAttribute('aria-label'),'Switch to light mode');
      assert.equal(await page.locator('meta[name="theme-color"]').getAttribute('content'),'#0a0a0a');
      assert.equal(await page.evaluate(()=>localStorage.getItem('ytmd-theme')),'dark');
      assert.equal(await page.locator('.thumbnail img').first().evaluate(el=>getComputedStyle(el).filter),'none');
      await checkContrast(page);
      if (name==='desktop'||name==='mobile') await page.screenshot({path:root+'/.impeccable/review/'+name+'-dark.png',fullPage:true});
      await page.reload({waitUntil:'networkidle'});
      assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
      await page.locator('#theme-toggle').click();
      await page.reload({waitUntil:'networkidle'});
      assert.equal(await page.locator('html').getAttribute('data-theme'),'light');
      await page.emulateMedia({reducedMotion:'reduce'});
      assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).scrollBehavior),'auto');
      for (const video of videos) {
        const plan=page.locator('#plan-'+video.id);
        await plan.locator('summary').focus(); await page.keyboard.press('Enter');
        assert.equal(await plan.evaluate(el=>el.open),true);
        assert.equal(await page.locator('#evidence-'+video.id).isVisible(),true);
        assert.equal(await plan.locator('li').count(),3);
        for (const [i, excerpt] of video.evidence.entries()) {
          assert.equal(await plan.locator('.citation').nth(i).getAttribute('href'),
            `https://www.youtube.com/watch?v=${video.id}&t=${Math.floor(excerpt.start)}s`);
        }
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
        await plan.locator('summary').focus(); await page.keyboard.press('Space');
        assert.equal(await plan.evaluate(el=>el.open),false);
      }
      await page.locator('[data-copy]').click();
      assert.match(await page.evaluate(()=>navigator.clipboard.readText()), /^Install ytmd using/);
      assert.equal(await page.locator('#install').evaluate(el=>el.open),false);
      await page.locator('#install summary').click();
      assert.equal(await page.locator('#agent-prompt').isVisible(),true);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      await page.goto(base+'#evidence-MZ14rrkHVbg',{waitUntil:'networkidle'});
      assert.equal(await page.locator('#plan-MZ14rrkHVbg').evaluate(el=>el.open),true);
      assert.equal(await page.locator('#evidence-MZ14rrkHVbg').evaluate(el=>document.activeElement===el),true);
      assert.deepEqual(errors,[]); assert.deepEqual(external,[]);
      console.log(name+': '+words+' default words; six images/plans, light/dark AA contrast and persistence, timestamps, keyboard, copy, deep links, local requests, layout passed');
      await context.close();
    }
    const system=await browser.newContext({colorScheme:'dark'});
    const automatic=await system.newPage(); await automatic.goto(base,{waitUntil:'networkidle'});
    assert.equal(await automatic.locator('html').getAttribute('data-theme'),'dark');
    assert.equal(await automatic.evaluate(()=>localStorage.getItem('ytmd-theme')),null);
    await automatic.emulateMedia({colorScheme:'light'});
    await automatic.waitForFunction(()=>document.documentElement.dataset.theme==='light');
    await automatic.locator('#theme-toggle').click();
    await automatic.emulateMedia({colorScheme:'dark'});
    await automatic.emulateMedia({colorScheme:'light'});
    assert.equal(await automatic.locator('html').getAttribute('data-theme'),'dark');
    console.log('System theme: automatic until explicitly overridden');
    await system.close();
    const nojs=await browser.newContext({viewport:{width:390,height:844},javaScriptEnabled:false,colorScheme:'dark'});
    const plain=await nojs.newPage(); await plain.goto(base,{waitUntil:'networkidle'});
    assert.equal(await plain.locator('button:visible').count(),0);
    assert.equal(await plain.locator('body').evaluate(el=>getComputedStyle(el).backgroundColor),'rgb(10, 10, 10)');
    await plain.locator('#install summary').click();
    assert.equal(await plain.locator('#agent-prompt').isVisible(),true);
    for (const video of videos) {
      await plain.locator('#plan-'+video.id+' summary').click();
      assert.equal(await plain.locator('#evidence-'+video.id).isVisible(),true);
    }
    assert.equal(await plain.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    console.log('No JavaScript: all six plans/sources and setup accessible');
    await nojs.close();
    const fallback=await browser.newContext({colorScheme:'dark'});
    await fallback.addInitScript(()=>{
      Object.defineProperty(navigator,'clipboard',{value:{writeText:async()=>{throw new Error('denied');}}});
      Object.defineProperty(window,'localStorage',{get(){throw new Error('storage denied');}});
    });
    const denied=await fallback.newPage(); await denied.goto(base,{waitUntil:'networkidle'});
    assert.equal(await denied.locator('html').getAttribute('data-theme'),'dark');
    await denied.locator('#theme-toggle').click();
    assert.equal(await denied.locator('html').getAttribute('data-theme'),'light');
    await denied.locator('[data-copy]').click();
    assert.equal(await denied.locator('#install').evaluate(el=>el.open),true);
    assert.match(await denied.evaluate(()=>getSelection().toString()),/^Install ytmd/);
    assert.match(await denied.locator('#copy-status').textContent(),/Text selected/);
    assert.equal(await denied.locator('[data-copy]').isEnabled(),true);
    console.log('Storage/clipboard denial: theme works in-session; setup revealed and selected');
    await fallback.close();
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
