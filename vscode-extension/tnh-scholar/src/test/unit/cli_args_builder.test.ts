import test from "node:test";
import assert from "node:assert/strict";

import { CliArgsBuilder } from "../../services/cli_args_builder";

const builder = new CliArgsBuilder();

test("buildGlobalArgs prepends api and config", () => {
  const args = builder.buildGlobalArgs("/tmp/config.json", ["list"]);
  assert.deepEqual(args, ["--api", "--config", "/tmp/config.json", "list"]);
});

test("buildRunArgs includes required args and inline vars", () => {
  const args = builder.buildRunArgs({
    promptKey: "translate",
    inputFile: "/tmp/in.md",
    outputFile: "/tmp/out.md",
    inlineVars: { source_lang: "vi", target_lang: "en" },
  });
  assert.deepEqual(args, [
    "--prompt",
    "translate",
    "--input-file",
    "/tmp/in.md",
    "--output-file",
    "/tmp/out.md",
    "--var",
    "source_lang=vi",
    "--var",
    "target_lang=en",
  ]);
});

test("buildRunArgs includes optional overrides", () => {
  const args = builder.buildRunArgs({
    promptKey: "summarize",
    inputFile: "/tmp/in.md",
    outputFile: "/tmp/out.md",
    inlineVars: {},
    model: "gpt-4o-mini",
    temperature: 0.2,
    maxTokens: 512,
  });
  assert.deepEqual(args, [
    "--prompt",
    "summarize",
    "--input-file",
    "/tmp/in.md",
    "--output-file",
    "/tmp/out.md",
    "--model",
    "gpt-4o-mini",
    "--temperature",
    "0.2",
    "--max-tokens",
    "512",
  ]);
});
