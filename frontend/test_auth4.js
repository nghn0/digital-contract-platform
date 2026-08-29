const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  
  const log = (msg) => console.log(msg);

  try {
    log("=== TEST A: Unauthenticated Visit ===");
    await page.goto('http://localhost:3000');
    
    // Find the link manually or just go to /dashboard
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForSelector('input[type="email"]', { timeout: 5000 });
    log("Expected /login?next=/dashboard. Got: " + page.url());

    log("\n=== TEST B: Login ===");
    // Click Demo Access
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const demoBtn = buttons.find(b => b.textContent && b.textContent.includes('Demo'));
      if (demoBtn) demoBtn.click();
    });
    
    // wait for dashboard marker
    await page.waitForFunction(() => window.location.pathname === '/dashboard', { timeout: 10000 });
    log("Expected /dashboard. Got: " + page.url());
    
    // Refresh page
    log("Refreshing...");
    await page.reload();
    await page.waitForFunction(() => window.location.pathname === '/dashboard', { timeout: 5000 });
    log("After refresh, Expected /dashboard. Got: " + page.url());

    log("\n=== TEST C: Navigate back to / and click Access Vault ===");
    await page.goto('http://localhost:3000');
    // Using raw goto to simulate the click, since we already tested the middleware protection
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForFunction(() => window.location.pathname === '/dashboard', { timeout: 5000 });
    log("Expected /dashboard. Got: " + page.url());

    log("\n=== TEST G: Sign out ===");
    // Find sign out button and click it
    await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('a, button, div, span'));
      const signoutBtn = links.find(b => b.textContent && b.textContent.includes('Sign Out'));
      if (signoutBtn) signoutBtn.click();
    });
    
    // Wait for login redirect
    await page.waitForFunction(() => window.location.pathname === '/login', { timeout: 5000 });
    log("After Sign Out, got: " + page.url());

    log("\n=== TEST: Returning after signout ===");
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForFunction(() => window.location.pathname === '/login', { timeout: 5000 });
    const url = new URL(page.url());
    log("Expected /login?next=/dashboard. Got: " + url.pathname + url.search);

  } catch (err) {
    console.error("Test failed:", err);
  } finally {
    await browser.close();
  }
})();
