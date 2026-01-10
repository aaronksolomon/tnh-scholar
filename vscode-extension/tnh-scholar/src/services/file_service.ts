import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import * as vscode from "vscode";

import { buildOutputPath } from "../utils/path_utils";
export class FileService {
  async writeTempInput(document: vscode.TextDocument): Promise<string> {
    const token = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const ext = path.extname(document.fileName) || ".txt";
    const filename = `tnh-gen-input-${token}${ext}`;
    const tempPath = path.join(os.tmpdir(), filename);
    await fs.promises.writeFile(tempPath, document.getText(), "utf-8");
    return tempPath;
  }

  buildOutputPath(document: vscode.TextDocument, promptKey: string): string {
    return buildOutputPath(document.fileName, promptKey);
  }

  async openOutputFile(outputPath: string): Promise<void> {
    const document = await vscode.workspace.openTextDocument(outputPath);
    await vscode.window.showTextDocument(document, { viewColumn: vscode.ViewColumn.Beside });
  }
}
