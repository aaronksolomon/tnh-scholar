import * as assert from "node:assert/strict";
import * as vscode from "vscode";

defineSuite();

function defineSuite(): void {
  suite("TNH Scholar Extension", () => {
    test("registers commands on activation", async () => {
      const extension = vscode.extensions.getExtension("tnh-scholar.tnh-scholar");
      assert.ok(extension, "Extension not found");
      await extension?.activate();

      const commands = await vscode.commands.getCommands(true);
      assert.ok(commands.includes("tnhScholar.runPromptOnActiveFile"));
      assert.ok(commands.includes("tnhScholar.refreshPromptCatalog"));
    });
  });
}
