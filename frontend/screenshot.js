const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  
  // Desktop
  const contextDesktop = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await contextDesktop.addInitScript(() => {
    localStorage.setItem('equityiq_access_token', 'mock_token');
  });
  const pageDesktop = await contextDesktop.newPage();
  await pageDesktop.goto('http://localhost:3000/dashboard', { waitUntil: 'networkidle' });
  await pageDesktop.waitForSelector('h1', { timeout: 10000 });
  await pageDesktop.screenshot({ path: 'C:/Users/Shrey/.gemini/antigravity/brain/17660775-13f4-4d97-bffb-d9fe7ff861d0/dashboard_desktop.png' });
  
  // Tablet
  const contextTablet = await browser.newContext({ viewport: { width: 768, height: 1024 } });
  await contextTablet.addInitScript(() => {
    localStorage.setItem('equityiq_access_token', 'mock_token');
  });
  const pageTablet = await contextTablet.newPage();
  await pageTablet.goto('http://localhost:3000/dashboard', { waitUntil: 'networkidle' });
  await pageTablet.waitForSelector('h1', { timeout: 10000 });
  await pageTablet.screenshot({ path: 'C:/Users/Shrey/.gemini/antigravity/brain/17660775-13f4-4d97-bffb-d9fe7ff861d0/dashboard_tablet.png' });
  
  // Mobile
  const contextMobile = await browser.newContext({ viewport: { width: 375, height: 812 } });
  await contextMobile.addInitScript(() => {
    localStorage.setItem('equityiq_access_token', 'mock_token');
  });
  const pageMobile = await contextMobile.newPage();
  await pageMobile.goto('http://localhost:3000/dashboard', { waitUntil: 'networkidle' });
  await pageMobile.waitForSelector('h1', { timeout: 10000 });
  await pageMobile.screenshot({ path: 'C:/Users/Shrey/.gemini/antigravity/brain/17660775-13f4-4d97-bffb-d9fe7ff861d0/dashboard_mobile.png' });

  // Open mobile sidebar
  await pageMobile.click('button:has(svg)'); // Click hamburger menu
  await pageMobile.waitForTimeout(1000); // Wait for animation
  await pageMobile.screenshot({ path: 'C:/Users/Shrey/.gemini/antigravity/brain/17660775-13f4-4d97-bffb-d9fe7ff861d0/dashboard_mobile_sidebar.png' });
  
  await browser.close();
  console.log('Screenshots captured successfully.');
})();
