/**
 * Puppeteer 自动登录 GitHub + 访问 Streamlit
 * 可部署在 GitHub Actions
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const GITHUB_USERNAME = process.env.GITHUB_USERNAME;
const GITHUB_PASSWORD = process.env.GITHUB_PASSWORD;
const TARGET_URL = 'https://nacvnejvddvitifldre34r.streamlit.app/';
const COOKIE_FILE = path.resolve(__dirname, 'cookies.json');

// 随机延时 1~30 分钟
function getRandomDelayMs() {
    const minutes = Math.floor(Math.random() * 30) + 1;
    return minutes * 60 * 1000;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function loadCookies(page) {
    if (fs.existsSync(COOKIE_FILE)) {
        const cookiesString = fs.readFileSync(COOKIE_FILE);
        const cookies = JSON.parse(cookiesString);
        await page.setCookie(...cookies);
        console.log('Loaded cookies from file');
    }
}

async function saveCookies(page) {
    const cookies = await page.cookies();
    fs.writeFileSync(COOKIE_FILE, JSON.stringify(cookies, null, 2));
    console.log('Saved cookies to file');
}

async function loginGitHub(page) {
    console.log('Logging in to GitHub...');
    await page.goto('https://github.com/login', { waitUntil: 'networkidle2' });

    await page.type('#login_field', GITHUB_USERNAME, { delay: 50 });
    await page.type('#password', GITHUB_PASSWORD, { delay: 50 });
    await page.click('input[name="commit"]');

    await page.waitForNavigation({ waitUntil: 'networkidle2' });

    if (page.url().includes('github.com/session')) {
        throw new Error('GitHub login failed, check credentials or 2FA');
    }

    console.log('GitHub login successful');
}

async function visitTarget(page) {
    await page.goto(TARGET_URL, { waitUntil: 'networkidle2' });
    console.log(`Visited ${TARGET_URL} at ${new Date().toISOString()}`);
}

async function main() {
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage();

    await loadCookies(page);

    try {
        await page.goto(TARGET_URL, { waitUntil: 'networkidle2', timeout: 10000 });
        console.log('Accessed target with existing session');
    } catch (err) {
        console.log('Session expired or not found, performing login');
        await loginGitHub(page);
        await saveCookies(page);
        await visitTarget(page);
    }

    // 随机循环访问
    const delay = getRandomDelayMs();
    console.log(`Next visit in ${(delay / 60000).toFixed(1)} minutes`);
    await sleep(delay);

    try {
        await visitTarget(page);
    } catch (err) {
        console.error('Visit failed, retry login', err);
        await loginGitHub(page);
        await saveCookies(page);
        await visitTarget(page);
    }

    await browser.close();
}

main().catch(err => {
    console.error('Script crashed:', err);
    process.exit(1);
});
