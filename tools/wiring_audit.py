#!/usr/bin/env node
/**
 * Scrapes YouTube search results for a query using a real headless
 * browser — NOT the official Data API (that's src/topic_research.py in
 * Python, already using OAuth and fully independent of this script).
 *
 * WHY THIS EXISTS AS NODE.JS RATHER THAN MORE PYTHON: this is the one
 * piece of the pipeline that genuinely benefits from a different
 * language's strength rather than just using Python everywhere for
 * consistency. Puppeteer (real headless Chrome automation, maintained by
 * the Chrome team) is a first-class, best-in-class Node.js tool; the
 * closest Python equivalents (Selenium, Playwright-for-Python) are
 * perfectly usable too, but there's no strong reason to prefer them here
 * over reusing the ecosystem Puppeteer is native to, and doing so keeps
 * this one well-scoped, swappable component cleanly separated from the
 * rest of the Python pipeline (see src/node_bridge.py for the boundary).
 *
 * WHAT THIS ADDS over src/topic_research.py's official API calls: a
 * rendered view of YouTube's actual search results page, including
 * YouTube's own "sort by upload date" view and the viewCountText/
 * publishedTimeText strings AS DISPLAYED to a real viewer — a slightly
 * different signal than the Data API's structured numeric fields, useful
 * as a cross-check rather than a replacement.
 *
 * TESTED STATUS (read before trusting this unattended):
 *   - lib/extract.js's JSON-parsing logic: tested for real with plain
 *     `node lib/extract.test.js` — no network or browser needed, genuinely
 *     verified in this repo's test history.
 *   - The Puppeteer launch/navigate/content code below: written against
 *     Puppeteer's standard, long-documented API (launch/goto/content) but
 *     NOT executed against real youtube.com from the environment this was
 *     built in — that sandbox has no outbound network access and
 *     `npm install puppeteer` itself failed there (403 from the npm
 *     registry, a network restriction, not a code problem). This is a
 *     real, stated gap: run this for the first time somewhere with actual
 *     network access (e.g. GitHub Actions, once `npm install` runs there)
 *     and read its output before trusting it unattended — the same
 *     caution this repo already applies to every other external service
 *     (see README's "Run #113-117 fixes" history of real production
 *     surprises from services that looked fine until actually exercised).
 */
const puppeteer = require("puppeteer");
const { extractYtInitialData, extractVideos } = require("./lib/extract");

async function scrapeNiche(query, maxResults) {
  maxResults = maxResults || 25;
  const browser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });
  try {
    const page = await browser.newPage();
    await page.setUserAgent(
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    );
    // sp=CAI%3D is YouTube's own "Sort by: Upload date" search filter —
    // biases results toward recent uploads, same intent as
    // topic_research.py's publishedAfter filter on the API side.
    const url = "https://www.youtube.com/results?search_query=" +
      encodeURIComponent(query) + "&sp=CAI%253D";
    await page.goto(url, { waitUntil: "networkidle2", timeout: 30000 });
    const html = await page.content();
    const data = extractYtInitialData(html);
    if (!data) {
      throw new Error(
        "Could not find ytInitialData in the page — YouTube's page " +
        "structure may have changed (see this file's top comment)."
      );
    }
    return extractVideos(data, maxResults);
  } finally {
    await browser.close();
  }
}

async function main() {
  const args = process.argv.slice(2);
  const queryIdx = args.indexOf("--query");
  const maxIdx = args.indexOf("--max-results");
  const query = queryIdx >= 0 ? args[queryIdx + 1] : null;
  const maxResults = maxIdx >= 0 ? parseInt(args[maxIdx + 1], 10) : 25;

  if (!query) {
    console.error(JSON.stringify({ error: "Missing --query argument" }));
    process.exit(1);
  }

  try {
    const videos = await scrapeNiche(query, maxResults);
    console.log(JSON.stringify({ query: query, videos: videos }));
  } catch (e) {
    console.error(JSON.stringify({ error: String((e && e.message) || e) }));
    process.exit(1);
  }
}

main();
