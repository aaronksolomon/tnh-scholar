import * as vscode from "vscode";
import { OutputChannelProtocol } from "../protocols/extension_protocols";

export class OutputChannelLogger implements OutputChannelProtocol {
  private readonly channel: vscode.OutputChannel;

  constructor(name: string) {
    this.channel = vscode.window.createOutputChannel(name);
  }

  info(message: string): void {
    this.channel.appendLine(`[info] ${message}`);
  }

  warn(message: string): void {
    this.channel.appendLine(`[warn] ${message}`);
  }

  error(message: string): void {
    this.channel.appendLine(`[error] ${message}`);
  }

  show(): void {
    this.channel.show(true);
  }
}
