/**
 * Pure extraction logic, separated from scrape.js's Puppeteer browser code
 * on purpose: this file has NO dependency on Puppeteer or a live browser,
 * so it's testable with plain `node lib/extract.test.js` — no network, no
 * npm install, nothing but Node itself. See extract.test.js.
 *
 * YouTube's search results page is client-rendered from a large JSON blob
 * embedded in a <script> tag (conventionally assigned to `ytInitialData`).
 * Reading that JSON directly is the standard, more-stable-than-CSS-classes
 * approach many YouTube scraping tools use, since YouTube's actual CSS
 * class names are frequently obfuscated/regenerated while this general
 * JSON shape has stayed comparatively stable across many community tools
 * over time. "Comparatively stable" is not "guaranteed stable" — YouTube
 * can and does change this structure. Every extraction step below is
 * defensive (optional chaining, skip-malformed-items) specifically so a
 * partial structure change degrades the RESULT COUNT rather than crashing
 * the whole scrape.
 */

function extractYtInitialData(html) {
  // Several known variants of how this gets embedded; try each.
  const patterns = [
    /var ytInitialData = (\{.*?\});<\/script>/s,
    /ytInitialData"\]\s*=\s*(\{.*?\});/s,
    /window\["ytInitialData"\]\s*=\s*(\{.*?\});/s,
  ];
  for (const pattern of patterns) {
    const match = html.match(pattern);
    if (match) {
      try {
        return JSON.parse(match[1]);
      } catch (e) {
        // Try the next pattern rather than failing on the first match
        // that happens not to parse cleanly.
        continue;
      }
    }
  }
  return null;
}

function extractVideos(ytInitialData, maxResults) {
  maxResults = maxResults || 25;
  const videos = [];
  try {
    const sections =
      (ytInitialData &&
        ytInitialData.contents &&
        ytInitialData.contents.twoColumnSearchResultsRenderer &&
        ytInitialData.contents.twoColumnSearchResultsRenderer.primaryContents &&
        ytInitialData.contents.twoColumnSearchResultsRenderer.primaryContents.sectionListRenderer &&
        ytInitialData.contents.twoColumnSearchResultsRenderer.primaryContents.sectionListRenderer.contents) ||
      [];

    for (const section of sections) {
      const items = (section.itemSectionRenderer && section.itemSectionRenderer.contents) || [];
      for (const item of items) {
        const vr = item.videoRenderer;
        if (!vr) continue; // non-video items (ads, shelves, etc.) — skip, don't crash
        videos.push({
          videoId: vr.videoId || null,
          title: (vr.title && vr.title.runs && vr.title.runs[0] && vr.title.runs[0].text) ||
                 (vr.title && vr.title.simpleText) || "",
          channel: (vr.ownerText && vr.ownerText.runs && vr.ownerText.runs[0] && vr.ownerText.runs[0].text) || "",
          viewCountText: (vr.viewCountText && vr.viewCountText.simpleText) ||
                         (vr.shortViewCountText && vr.shortViewCountText.simpleText) || "",
          publishedTimeText: (vr.publishedTimeText && vr.publishedTimeText.simpleText) || "",
        });
        if (videos.length >= maxResults) return videos;
      }
    }
  } catch (e) {
    // A structure change partway through shouldn't discard everything
    // already extracted — return what we got.
  }
  return videos;
}

module.exports = { extractYtInitialData, extractVideos };
