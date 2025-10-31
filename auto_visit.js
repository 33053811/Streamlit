/**
 * Puppeteer 自动登录 GitHub + 循环访问 Streamlit
 * 兼容 GitHub Actions
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const GITHUB_USER = process.env.GITHUB_USER; // 用户名或邮箱
const GITHUB_PASS = process.env.GITHUB_PASS; // PAT 或密码
const TARGET_URL = 'https://nacvnejvddvitifldre34r.streamlit.app/';
const COOKIE_FILE = path.resolve(__dirname, 'cookies.json');

// 每次运行循环访问次数
const LOOP_COUNT = 5;

// 随机延时 1~30 分钟
function getRandomDelayMs() {
  const minutes = Math.floor(Math.random() * 30) + 1;
  return minutes * 60 * 1000;
}

// 睡眠函数
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// 加载 cookie
async function loadCookies(page) {
  if (fs.existsSync(COOKIE_FILE)) {
    try {
      const cookies = JSON.parse(fs.readFileSync(COOKIE_FILE));
      await page.setCookie(...cookies);
      console.log('✅ Cookies 已加载');
    } catch (e) {
      console.log('⚠️ Cookies 文件损坏，忽略');
    }
  }
}

// 保存 cookie
async function saveCookies(page) {
  const cookies = await page.cookies();
  fs.writeFileSync(COOKIE_FILE, JSON.stringify(cookies, null, 2));
  console.log('💾 Cookies 已保存');
}

// GitHub 登录
async function loginGitHub(page) {
  console.log('🔐 开始登录 GitHub...');
  await page.goto('https://github.com/login', { waitUntil: 'networkidle2' });
  await page.type('#login_field', GITHUB_USER, { delay: 50 });
  await page.type('#password', GITHUB_PASS, { delay: 50 });
  await page.click('input[name="commit"]');
  await page.waitForNavigation({ waitUntil: 'networkidle2' });

  if (page.url().includes('session')) throw new Error('❌ GitHub 登录失败');
  console.log('✅ 登录成功');
}

// 访问目标网址
async function visitTarget(page) {
  try {
    await page.goto(TARGET_URL, { waitUntil: 'networkidle2', timeout: 60000 });
    console.log(`🌐 成功访问：${TARGET_URL} (${new Date().toLocaleString()})`);
  } catch (err) {
    console.error('⚠️ 访问失败：', err.message);
  }
}

// 主流程
async function main() {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  await loadCookies(page);

  try {
    await page.goto('https://github.com/', { waitUntil: 'networkidle2' });
    const isLoggedIn = !(await page.$('a[href="/login"]'));
    if (!isLoggedIn) {
      console.log('🔄 未登录，重新登录...');
      await loginGitHub(page);
      await saveCookies(page);
    }
  } catch {
    console.log('❌ 无法验证登录状态，尝试重新登录');
    await loginGitHub(page);
    await saveCookies(page);
  }

  // 循环访问
  for (let i = 1; i <= LOOP_COUNT; i++) {
    console.log(`\n🚀 [${i}/${LOOP_COUNT}] 第 ${i} 次访问开始`);
    await visitTarget(page);
    if (i < LOOP_COUNT) {
      const delay = getRandomDelayMs();
      console.log(`⏳ 随机等待 ${(delay / 60000).toFixed(1)} 分钟后继续...`);
      await sleep(delay);
    }
  }

  await browser.close();
  console.log('\n✅ 全部访问完成，任务结束。');
}

main().catch(err => {
  console.error('💥 脚本运行出错：', err);
  process.exit(1);
});
