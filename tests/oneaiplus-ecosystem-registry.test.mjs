import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const registry = JSON.parse(await readFile(new URL("../docs/architecture/oneaiplus-ecosystem-registry.json", import.meta.url), "utf8"));

test("registry contains 113 unique component IDs across 10 categories", () => {
  const components = registry.categories.flatMap((category) => category.components);
  assert.equal(registry.categories.length, 10);
  assert.equal(components.length, 113);
  assert.equal(new Set(components.map((item) => item.id)).size, 113);
  for (const category of registry.categories) {
    assert.equal(category.components.length, category.declaredCount, category.name);
  }
});

test("registry preserves 15 unique identities separately", () => {
  assert.equal(registry.identities.length, 15);
  assert.equal(new Set(registry.identities.map((item) => item.id)).size, 15);
  assert.ok(registry.identities.every((item) => /^P\\d{3}$/.test(item.id)));
});

test("component statuses use the controlled evidence vocabulary", () => {
  const allowed = new Set(registry.statusVocabulary);
  for (const item of registry.categories.flatMap((category) => category.components)) {
    assert.ok(allowed.has(item.status), `${item.id}: ${item.status}`);
  }
});

test("independent products remain outside the identity register", () => {
  assert.deepEqual(registry.independenceRules.independentProducts, ["NexAI", "IDEAS"]);
  assert.ok(!registry.identities.some((item) => ["NexAI", "IDEAS"].includes(item.name)));
});
