import * as vscode from "vscode";

import { ListApiEntry } from "../models/api_payloads";

export class EditorService {
  getActiveDocument(): vscode.TextDocument {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      throw new Error("No active editor. Open a file to run a prompt.");
    }
    return editor.document;
  }

  async pickPrompt(prompts: ListApiEntry[]): Promise<ListApiEntry | undefined> {
    const items = prompts.map((prompt) => ({
      label: prompt.name || prompt.key,
      description: prompt.description,
      detail: prompt.key,
      prompt,
    }));
    const selected = await vscode.window.showQuickPick(items, {
      placeHolder: "Select a prompt",
      matchOnDescription: true,
      matchOnDetail: true,
    });
    return selected?.prompt;
  }

  async collectRequiredVariables(required: string[]): Promise<Record<string, string> | undefined> {
    const values: Record<string, string> = {};
    for (const variable of required) {
      const input = await vscode.window.showInputBox({
        prompt: `Enter value for ${variable}`,
        ignoreFocusOut: true,
      });
      if (input === undefined) {
        return undefined;
      }
      values[variable] = input;
    }
    return values;
  }

  async collectOptionalVariables(optional: string[]): Promise<Record<string, string>> {
    const values: Record<string, string> = {};
    for (const variable of optional) {
      const input = await vscode.window.showInputBox({
        prompt: `Optional value for ${variable}`,
        placeHolder: "Leave blank to skip",
        ignoreFocusOut: true,
      });
      if (input === undefined) {
        break;
      }
      if (input.trim() !== "") {
        values[variable] = input;
      }
    }
    return values;
  }

  showInfo(message: string): void {
    void vscode.window.showInformationMessage(message);
  }

  showError(message: string): void {
    void vscode.window.showErrorMessage(message);
  }
}
