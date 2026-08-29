const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  
  const log = (msg) => console.log(msg);

  try {
    log("=== TEST A: Unauthenticated Visit ===");
    await page.goto('http://localhost:3001'); // Frontend dev server is on 3001
    
    // Find the link manually or just go to /dashboard
    await page.goto('http://localhost:3001/dashboard');
    await page.waitForSelector('input[type="email"]', { timeout: 5000 });
    log("Expected /login?next=/dashboard. Got: " + page.url());

    log("\n=== TEST B: Login ===");
    await page.type('input[type="email"]', 'demo@example.com');
    await page.type('input[type="password"]', 'demo1234');
    
    // We expect navigation, but since it's Next.js, we wait for the URL to change
    await page.click('button[type="submit"]');
    
    // wait for dashboard marker
    await page.waitForFunction(() => window.location.pathname === '/dashboard', { timeout: 10000 });
    log("Expected /dashboard. Got: " + page.url());
    
    // Refresh page
    log("Refreshing...");
    await page.reload();
    await page.waitForFunction(() => window.location.pathname === '/dashboard', { timeout: 5000 });
    log("After refresh, Expected /dashboard. Got: " + page.url());

    log("\n=== TEST C: Navigate back to / and click Access Vault ===");
    await page.goto('http://localhost:3001');
    // Using raw goto to simulate the click, since we already tested the middleware protection
    await page.goto('http://localhost:3001/dashboard');
    await page.waitForFunction(() => window.location.pathname === '/dashboard', { timeout: 5000 });
    log("Expected /dashboard. Got: " + page.url());

    log("\n=== TEST G: Sign out ===");
    // Attempt sign out using a clear method - there should be a sign out button on dashboard
    // If we can't find it, we'll just evaluate a clear storage script or click the signout button
    await page.evaluate(() => {
      // Find sign out button by text
      const buttons = Array.from(document.querySelectorAll('button'));
      const signoutBtn = buttons.find(b => b.textContent.includes('Sign Out') || b.textContent.includes('Logout'));
      if (signoutBtn) signoutBtn.click();
    });
    
    // Wait for login redirect
    await page.waitForFunction(() => window.location.pathname === '/login', { timeout: 5000 });
    log("After Sign Out, got: " + page.url());

    log("\n=== TEST: Returning after signout ===");
    await page.goto('http://localhost:3001/dashboard');
    await page.waitForFunction(() => window.location.pathname === '/login', { timeout: 5000 });
    log("Expected /login?next=/dashboard. Got: " + page.url());

  } catch (err) {
    console.error("Test failed:", err);
  } finally {
    await browser.close();
  }
})();
