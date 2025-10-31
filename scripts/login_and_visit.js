// 使用 Playwright 在 headless 模式下登录 GitHub 并访问目标 Streamlit 应用
// 依赖：playwright（在 workflow 中已安装）
const { chromium } = require('playwright');

(async () => {
  const username = process.env.GH_LOGIN;
  const password = process.env.GH_PASS;
  const target = process.env.TARGET_URL || 'https://nacvnejvddvitifldre34r.streamlit.app/';
  const saveScreenshot = (process.env.SAVE_SCREENSHOT || 'true') === 'true';

  if (!username || !password) {
    console.error('GH_LOGIN or GH_PASS not set in env. Aborting.');
    process.exit(2);
  }

  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36',
    // 你可以指定 viewport/session cookie 等
  });
  const page = await context.newPage();

  try {
    console.log('Navigating to GitHub login page...');
    await page.goto('https://github.com/login', { waitUntil: 'domcontentloaded', timeout: 60000 });

    // 填写并提交登录表单
    await page.fill('input[name="login"]', username);
    await page.fill('input[name="password"]', password);
    await Promise.all([
      page.click('input[name="commit"]'),
      page.waitForNavigation({ waitUntil: 'networkidle', timeout: 60000 }).catch(e => {
        console.warn('Navigation after login may have been blocked or took too long:', e.message);
      })
    ]);

    // 检测是否进入了 2FA 或危险页面
    const urlAfter = page.url();
    console.log('URL after attempted login:', urlAfter);

    // 若检测到 2FA 页面特征（例如 /sessions/verified-device）
    if (await page.$('input[name="otp"]') || urlAfter.includes('/sessions/verified-device') || await page.$('text=Two-factor authentication')) {
      console.error('Two-factor authentication (2FA) detected. Automated login cannot proceed.');
      if (saveScreenshot) await page.screenshot({ path: 'login_2fa_detected.png', fullPage: true });
      await browser.close();
      process.exit(3);
    }

    // 检查是否登录成功（页面含有用户头像或 profile link）
    const signedIn = await page.$('summary[aria-label="View profile and more"]') || (await page.$('a[href="/' + username + '"]'));
    if (!signedIn) {
      console.warn('Login may have failed or GitHub presented additional checks (captcha/challenge). URL:', urlAfter);
      if (saveScreenshot) await page.screenshot({ path: 'login_failed.png', fullPage: true });
      // 仍然尝试访问目标（有时登录已成功但未能检测）
    } else {
      console.log('Login appears successful.');
      if (saveScreenshot) await page.screenshot({ path: 'github_logged_in.png', fullPage: true });
    }

    // 访问目标 Streamlit 应用
    console.log('Navigating to target Streamlit app:', target);
    await page.goto(target, { waitUntil: 'networkidle', timeout: 90000 });

    // 等待页面主要元素出现（依据 Streamlit 页面常见元素）
    try {
      await page.waitForSelector('iframe, [data-testid], .stApp, body', { timeout: 30000 });
    } catch (e) {
      console.warn('Main selector did not appear quickly:', e.message);
    }

    const finalUrl = page.url();
    console.log('Visited final URL:', finalUrl);

    // 获取页面内容摘要与 HTTP 状态（Playwright 没有直接 status for navigation if same-origin blocked; we can fetch via fetch API）
    const pageTitle = await page.title();
    console.log('Page title:', pageTitle);

    if (saveScreenshot) {
      const shotPath = 'streamlit_visit.png';
      await page.screenshot({ path: shotPath, fullPage: true });
      console.log('Saved screenshot to', shotPath);
    }

    // 可选：保存页面 HTML（仅用于调试）
    const html = await page.content();
    require('fs').writeFileSync('page_content.html', html);
    console.log('Saved page_content.html (truncated):', html.slice(0, 300));

    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error('Error during automation:', err);
    try { await page.screenshot({ path: 'error_screenshot.png', fullPage: true }); } catch(e){}
    await browser.close();
    process.exit(1);
  }
})();
