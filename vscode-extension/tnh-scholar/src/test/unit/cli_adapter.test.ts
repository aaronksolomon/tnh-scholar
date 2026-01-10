import test from "node:test";
import assert from "node:assert/strict";

import { CliError } from "../../services/cli_errors";
import { ExecRunner, TnhGenCliAdapter } from "../../services/cli_adapter";
import { OutputChannelProtocol } from "../../protocols/extension_protocols";

class FakeRunner implements ExecRunner {
  private readonly stdout: string;
  private readonly stderr: string;
  private readonly shouldThrow: boolean;

  constructor(stdout: string, stderr: string, shouldThrow = false) {
    this.stdout = stdout;
    this.stderr = stderr;
    this.shouldThrow = shouldThrow;
  }

  async run(): Promise<{ stdout: string; stderr: string }> {
    if (this.shouldThrow) {
      const error = new Error("command failed") as Error & { stdout?: string; stderr?: string };
      error.stdout = this.stdout;
      error.stderr = this.stderr;
      throw error;
    }
    return { stdout: this.stdout, stderr: this.stderr };
  }
}

class TestLogger implements OutputChannelProtocol {
  info(): void {}
  warn(): void {}
  error(): void {}
}

test("listPrompts parses JSON payload", async () => {
  const payload = JSON.stringify({ prompts: [], count: 0, sources: ["defaults"] });
  const adapter = new TnhGenCliAdapter("tnh-gen", new TestLogger(), new FakeRunner(payload, ""));
  const result = await adapter.listPrompts("/tmp/config.json");
  assert.equal(result.count, 0);
  assert.deepEqual(result.sources, ["defaults"]);
});

test("runPrompt surfaces structured error", async () => {
  const errorPayload = JSON.stringify({
    status: "failed",
    error: "Policy blocked",
    diagnostics: { suggestion: "Increase max_dollars" },
    trace_id: "abc123",
  });
  const adapter = new TnhGenCliAdapter("tnh-gen", new TestLogger(), new FakeRunner(errorPayload, "stderr", true));
  await assert.rejects(
    () => adapter.runPrompt("/tmp/config.json", {
      promptKey: "translate",
      inputFile: "/tmp/input.txt",
      outputFile: "/tmp/output.txt",
      inlineVars: {},
    }),
    (error: unknown) => {
      const cliError = error as CliError;
      assert.equal(cliError.payload?.error, "Policy blocked");
      assert.equal(cliError.stderrTail, "stderr");
      return true;
    },
  );
});
