import test from "node:test";
import assert from "node:assert/strict";
import { getPublicAppUrl } from "../lib/public-app-url.mjs";

test("uses local origin when no public URL is configured", () => {
  assert.equal(getPublicAppUrl(""), "http://localhost:3000");
  assert.equal(getPublicAppUrl(undefined), "http://localhost:3000");
});

test("normalizes a valid preview origin", () => {
  assert.equal(
    getPublicAppUrl("https://preview.example.vercel.app/"),
    "https://preview.example.vercel.app"
  );
});

test("rejects non-HTTP protocols", () => {
  assert.throws(() => getPublicAppUrl("javascript:alert(1)"), /HTTP or HTTPS/);
});

test("rejects credentials, paths, query strings and fragments", () => {
  for (const value of [
    "https://user:pass@example.com",
    "https://example.com/app",
    "https://example.com?next=/",
    "https://example.com#section",
  ]) {
    assert.throws(() => getPublicAppUrl(value));
  }
});

test("rejects malformed absolute URLs", () => {
  assert.throws(() => getPublicAppUrl("not-a-url"), /absolute HTTP\(S\) URL/);
});
