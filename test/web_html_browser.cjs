// Optional browser regression: requires Playwright and an installed Chromium.
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { test } = require('node:test');
const { chromium } = require('playwright');

const fixtures = JSON.parse(execFileSync(process.env.PYTHON || 'python3', ['-c', `
import json
from PyOrchestrate.web_interface.server import create_html_response
payloads = [
    {'message': '<img src=x onerror=alert(1)>'},
    {'<img src=x onerror=alert(2)>': '&quot; &amp; <tag> café'},
    {'message': '</ScRiPt ><script>alert(3)</script>'},
    {'message': '<!--<script> & "quotes" \\\\\ backslash — café'},
]
print(json.dumps([
    {
        'html': create_html_response('History', data, '/api/history').body.decode(),
        'text': json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True),
    }
    for data in payloads
]))
`], { encoding: 'utf8' }));

test('monitoring values remain text after JavaScript highlighting', async () => {
    const browser = await chromium.launch({
        headless: true,
        ...(process.env.BROWSER_CHANNEL ? { channel: process.env.BROWSER_CHANNEL } : {}),
    });
    try {
        const dialogs = [];
        for (const fixture of fixtures) {
            const page = await browser.newPage();
            page.on('dialog', async dialog => {
                dialogs.push(dialog.message());
                await dialog.dismiss();
            });
            await page.setContent(fixture.html);
            assert.equal(await page.locator('#json-content img').count(), 0);
            assert.equal(await page.locator('#json-content').innerText(), fixture.text);
            await page.close();
        }
        assert.deepEqual(dialogs, []);
    } finally {
        await browser.close();
    }
});
