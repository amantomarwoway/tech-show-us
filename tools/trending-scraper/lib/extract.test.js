/**
 * Runnable with plain `node lib/extract.test.js` — no npm install, no
 * network, no test framework dependency. Tests extract.js's parsing logic
 * against a fixture shaped like YouTube's embedded JSON structure (see
 * extract.js's top comment for the honesty caveat on how closely a
 * fixture like this can really track YouTube's actual current markup).
 */
const assert = require("assert");
const { extractYtInitialData, extractVideos } = require("./extract");

const fixtureHtml = `
<html><body>
<script>var ytInitialData = {"contents":{"twoColumnSearchResultsRenderer":{"primaryContents":{"sectionListRenderer":{"contents":[{"itemSectionRenderer":{"contents":[
  {"videoRenderer":{"videoId":"abc123","title":{"runs":[{"text":"Dark Mystery Story Full"}]},"ownerText":{"runs":[{"text":"MysteryTales"}]},"viewCountText":{"simpleText":"150,000 views"},"publishedTimeText":{"simpleText":"2 weeks ago"}}},
  {"somethingElseRenderer":{"ignored":true}},
  {"videoRenderer":{"videoId":"def456","title":{"runs":[{"text":"Locked Room Crime Thriller"}]},"ownerText":{"runs":[{"text":"CrimeStories"}]},"viewCountText":{"simpleText":"89,000 views"},"publishedTimeText":{"simpleText":"5 days ago"}}}
]}}]}}}}};</script>
</body></html>
`;

function run() {
  const data = extractYtInitialData(fixtureHtml);
  assert.ok(data, "Should extract ytInitialData JSON from the fixture HTML");

  const videos = extractVideos(data, 10);
  assert.strictEqual(videos.length, 2, "Should extract exactly 2 videoRenderer items, skipping the non-video item");
  assert.strictEqual(videos[0].videoId, "abc123");
  assert.strictEqual(videos[0].title, "Dark Mystery Story Full");
  assert.strictEqual(videos[0].channel, "MysteryTales");
  assert.strictEqual(videos[0].viewCountText, "150,000 views");
  assert.strictEqual(videos[1].videoId, "def456");

  const limited = extractVideos(data, 1);
  assert.strictEqual(limited.length, 1, "Should respect maxResults limit");

  assert.strictEqual(extractYtInitialData("<html>no data here</html>"), null,
    "Should return null, not throw, when ytInitialData isn't present");
  assert.deepStrictEqual(extractVideos(null, 10), [],
    "Should return an empty array, not throw, for null input");

  // A video item with a missing/malformed field shouldn't crash extraction
  // of the OTHER items around it.
  const partiallyBrokenData = {
    contents: { twoColumnSearchResultsRenderer: { primaryContents: { sectionListRenderer: { contents: [
      { itemSectionRenderer: { contents: [
        { videoRenderer: { videoId: "ok1", title: { runs: [{ text: "Fine" }] } } },
        { videoRenderer: { videoId: "broken1" /* no title at all */ } },
        { videoRenderer: { videoId: "ok2", title: { runs: [{ text: "Also fine" }] } } },
      ] } },
    ] } } } },
  };
  const partial = extractVideos(partiallyBrokenData, 10);
  assert.strictEqual(partial.length, 3, "Malformed title shouldn't drop the item, just leave title empty");
  assert.strictEqual(partial[1].title, "", "Missing title should default to empty string, not throw");

  console.log("All extract.js tests passed");
}

run();
