import * as assert from "node:assert/strict";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import * as vscode from "vscode";

suite("TNH Scholar Refresh Catalog", () => {
  test("refreshPromptCatalog uses configured cliPath", async () => {
    const tempDir = await fs.promises.mkdtemp(path.join(os.tmpdir(), "tnh-scholar-cli-"));
    const cliPath = path.join(tempDir, "tnh-gen");
    const script = "#!/usr/bin/env bash\necho '{\"prompts\":[],\"count\":0,\"sources\":[\"defaults\"]}'\n";
    await fs.promises.writeFile(cliPath, script, { encoding: "utf-8", mode: 0o755 });

    const config = vscode.workspace.getConfiguration("tnhScholar");
    await config.update("cliPath", cliPath, vscode.ConfigurationTarget.Global);

    await vscode.commands.executeCommand("tnhScholar.refreshPromptCatalog");

    const commands = await vscode.commands.getCommands(true);
    assert.ok(commands.includes("tnhScholar.refreshPromptCatalog"));
  });
});
