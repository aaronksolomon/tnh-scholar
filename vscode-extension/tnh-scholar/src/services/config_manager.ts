import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import * as vscode from "vscode";

import { ExtensionSettings, ResolvedSettings, TempConfigFile } from "../models/settings";
import { ConfigManagerProtocol, OutputChannelProtocol } from "../protocols/extension_protocols";

export class ConfigManager implements ConfigManagerProtocol {
  private readonly logger: OutputChannelProtocol;

  constructor(logger: OutputChannelProtocol) {
    this.logger = logger;
  }

  async resolveSettings(): Promise<ResolvedSettings> {
    const settings = this.readSettings();
    const resolvedCliPath = await this.resolveCliPath(settings);
    return {
      cliPath: resolvedCliPath,
      promptDirectory: settings.promptDirectory ?? undefined,
      defaultModel: settings.defaultModel ?? undefined,
      maxCostUsd: settings.maxCostUsd ?? undefined,
    };
  }

  async writeTempConfig(settings: ResolvedSettings): Promise<TempConfigFile> {
    const payload: Record<string, unknown> = {};
    if (settings.promptDirectory) {
      payload.prompt_catalog_dir = settings.promptDirectory;
    }
    if (settings.defaultModel) {
      payload.default_model = settings.defaultModel;
    }
    if (settings.maxCostUsd !== undefined) {
      payload.max_dollars = settings.maxCostUsd;
    }
    const configPath = this.buildTempPath();
    await fs.promises.writeFile(configPath, JSON.stringify(payload, null, 2), "utf-8");
    return { path: configPath };
  }

  private readSettings(): ExtensionSettings {
    const config = vscode.workspace.getConfiguration("tnhScholar");
    const cliPath = this.resolveProjectOwned<string>(config, "cliPath");
    const promptDirectory = this.resolveProjectOwned<string>(config, "promptDirectory");
    const defaultModel = this.resolveUserOwned<string>(config, "defaultModel");
    const maxCostUsd = this.resolveUserOwned<number>(config, "maxCostUsd");
    return { cliPath, promptDirectory, defaultModel, maxCostUsd };
  }

  private resolveProjectOwned<T>(config: vscode.WorkspaceConfiguration, key: string): T | null {
    const inspected = config.inspect<T>(key);
    if (!inspected) {
      return null;
    }
    return this.coalesce(inspected.workspaceValue, inspected.globalValue, inspected.defaultValue);
  }

  private resolveUserOwned<T>(config: vscode.WorkspaceConfiguration, key: string): T | null {
    const inspected = config.inspect<T>(key);
    if (!inspected) {
      return null;
    }
    return this.coalesce(inspected.globalValue, inspected.workspaceValue, inspected.defaultValue);
  }

  private coalesce<T>(...values: Array<T | undefined>): T | null {
    for (const value of values) {
      if (value !== undefined && value !== null) {
        return value;
      }
    }
    return null;
  }

  private async resolveCliPath(settings: ExtensionSettings): Promise<string> {
    const candidates = await this.collectCliPathCandidates(settings);
    for (const candidate of candidates) {
      if (await this.isExecutable(candidate)) {
        return candidate;
      }
    }
    throw new Error("Unable to locate tnh-gen CLI. Set tnhScholar.cliPath or update PATH.");
  }

  private async collectCliPathCandidates(settings: ExtensionSettings): Promise<string[]> {
    const candidates: Array<string | undefined | null> = [];
    candidates.push(settings.cliPath);
    candidates.push(await this.tryPythonInterpreter());
    candidates.push(this.findInPath());
    return candidates.filter((value): value is string => Boolean(value));
  }

  private async tryPythonInterpreter(): Promise<string | undefined> {
    const config = vscode.workspace.getConfiguration("python");
    const interpreter = config.get<string>("defaultInterpreterPath")
      ?? config.get<string>("pythonPath");
    if (!interpreter) {
      return undefined;
    }
    return path.join(path.dirname(interpreter), this.executableName());
  }

  private findInPath(): string | undefined {
    const pathValue = process.env.PATH;
    if (!pathValue) {
      return undefined;
    }
    const parts = pathValue.split(path.delimiter);
    for (const entry of parts) {
      const candidate = path.join(entry, this.executableName());
      if (fs.existsSync(candidate)) {
        return candidate;
      }
    }
    return undefined;
  }

  private executableName(): string {
    return process.platform === "win32" ? "tnh-gen.exe" : "tnh-gen";
  }

  private async isExecutable(candidate: string): Promise<boolean> {
    try {
      await fs.promises.access(candidate, fs.constants.X_OK);
      return true;
    } catch {
      return false;
    }
  }

  private buildTempPath(): string {
    const token = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const filename = `tnh-gen-config-${token}.json`;
    const configPath = path.join(os.tmpdir(), filename);
    this.logger.info(`Writing temp config: ${configPath}`);
    return configPath;
  }
}
