const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  console.log("=== TEST A: Unauthenticated Visit ===");
  await page.goto('http://localhost:3000'); 
  
  await Promise.all([
    page.waitForNavigation(),
    page.click('a[href="/dashboard"]') // "Access Vault"
  ]);

  let url = page.url();
  console.log("Expected /login?next=/dashboard. Got:", url);

  console.log("=== TEST B: Login ===");
  await page.type('input[type="email"]', 'demo@example.com');
  await page.type('input[type="password"]', 'demo1234');
  
  await Promise.all([
    page.waitForNavigation(),
    page.click('button[type="submit"]')
  ]);
  
  url = page.url();
  console.log("Expected /dashboard. Got:", url);
  
  // Refresh page
  await page.reload();
  url = page.url();
  console.log("After refresh, Expected /dashboard. Got:", url);

  console.log("=== TEST C: Navigate back to / and click Access Vault ===");
  await page.goto('http://localhost:3000');
  await Promise.all([
    page.waitForNavigation(),
    page.click('a[href="/dashboard"]')
  ]);
  url = page.url();
  console.log("Expected /dashboard. Got:", url);

  await browser.close();
})();
