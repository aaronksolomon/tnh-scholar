import * as fs from "fs";

import { DiagnosticsProtocol } from "../protocols/extension_protocols";
import { CliError } from "./cli_errors";
import { TnhGenCliAdapter } from "./cli_adapter";
import { ConfigManager } from "./config_manager";
import { OutputChannelProtocol } from "../protocols/extension_protocols";

export class DiagnosticsService implements DiagnosticsProtocol {
  private readonly configManager: ConfigManager;
  private readonly logger: OutputChannelProtocol;

  constructor(configManager: ConfigManager, logger: OutputChannelProtocol) {
    this.configManager = configManager;
    this.logger = logger;
  }

  async showDiagnostics(): Promise<void> {
    this.logger.info("Running TNH Scholar diagnostics...");
    const settings = await this.configManager.resolveSettings();
    this.logger.info(`Resolved cliPath: ${settings.cliPath}`);
    if (settings.promptDirectory) {
      this.logger.info(`Resolved promptDirectory: ${settings.promptDirectory}`);
    }
    if (settings.defaultModel) {
      this.logger.info(`Resolved defaultModel: ${settings.defaultModel}`);
    }
    if (settings.maxCostUsd !== undefined) {
      this.logger.info(`Resolved maxCostUsd: ${settings.maxCostUsd}`);
    }

    const tempConfig = await this.configManager.writeTempConfig(settings);
    this.logger.info(`Temp config path: ${tempConfig.path}`);
    try {
      const contents = await fs.promises.readFile(tempConfig.path, "utf-8");
      this.logger.info(`Temp config contents: ${contents}`);
    } catch (error) {
      this.logger.warn("Unable to read temp config file.");
    }

    const cliAdapter = new TnhGenCliAdapter(settings.cliPath, this.logger);
    try {
      const version = await cliAdapter.getVersion(tempConfig.path);
      this.logger.info(`tnh-gen version: ${version.tnh_gen}`);
      this.logger.info(`tnh-scholar version: ${version.tnh_scholar}`);
      this.logger.info(`python: ${version.python}`);
      this.logger.info(`platform: ${version.platform}`);
    } catch (error) {
      if (error instanceof CliError) {
        this.logger.error(`CLI error: ${error.message}`);
        if (error.stderrTail) {
          this.logger.warn(error.stderrTail);
        }
      } else {
        this.logger.error("Unable to fetch tnh-gen version.");
      }
    }
  }
}
