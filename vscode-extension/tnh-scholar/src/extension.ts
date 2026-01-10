import * as vscode from "vscode";

import { PromptRunner } from "./services/prompt_runner";
import { ConfigManager } from "./services/config_manager";
import { EditorService } from "./services/editor_service";
import { FileService } from "./services/file_service";
import { OutputChannelLogger } from "./services/output_channel";
import { DiagnosticsService } from "./services/diagnostics_service";

export function activate(context: vscode.ExtensionContext): void {
  const logger = new OutputChannelLogger("TNH Scholar");
  const configManager = new ConfigManager(logger);
  const editor = new EditorService();
  const files = new FileService();
  const runner = new PromptRunner(configManager, editor, files, logger);
  const diagnostics = new DiagnosticsService(configManager, logger);

  const runCommand = vscode.commands.registerCommand("tnhScholar.runPromptOnActiveFile", () => {
    void runner.runOnActiveFile();
  });

  const refreshCommand = vscode.commands.registerCommand("tnhScholar.refreshPromptCatalog", () => {
    void runner.refreshPromptCatalog();
  });

  const diagnosticsCommand = vscode.commands.registerCommand("tnhScholar.showDiagnostics", () => {
    void diagnostics.showDiagnostics();
  });

  context.subscriptions.push(runCommand, refreshCommand, diagnosticsCommand);
}

export function deactivate(): void {
  return;
}
