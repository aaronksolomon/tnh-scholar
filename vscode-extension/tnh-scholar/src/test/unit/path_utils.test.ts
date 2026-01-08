import test from "node:test";
import assert from "node:assert/strict";

import { buildOutputPath, sanitizePromptKey } from "../../utils/path_utils";

test("sanitizePromptKey collapses whitespace", () => {
  assert.equal(sanitizePromptKey("translate to en"), "translate-to-en");
});

test("buildOutputPath appends prompt key", () => {
  const output = buildOutputPath("/repo/notes.md", "summarize key");
  assert.equal(output, "/repo/notes.summarize-key.md");
});
