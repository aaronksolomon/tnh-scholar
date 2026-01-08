import { ListApiPayload, RunSuccessPayload, VersionPayload } from "../models/api_payloads";
import { ResolvedSettings, TempConfigFile } from "../models/settings";

export interface RunPromptRequest {
  promptKey: string;
  inputFile: string;
  outputFile: string;
  inlineVars: Record<string, string>;
  model?: string;
  maxTokens?: number;
  temperature?: number;
}

export interface CliAdapterProtocol {
  listPrompts(configPath: string): Promise<ListApiPayload>;
  runPrompt(configPath: string, request: RunPromptRequest): Promise<RunSuccessPayload>;
  getVersion(configPath: string): Promise<VersionPayload>;
}

export interface ConfigManagerProtocol {
  resolveSettings(): Promise<ResolvedSettings>;
  writeTempConfig(settings: ResolvedSettings): Promise<TempConfigFile>;
}

export interface OutputChannelProtocol {
  info(message: string): void;
  warn(message: string): void;
  error(message: string): void;
}

export interface PromptRunnerProtocol {
  runOnActiveFile(): Promise<void>;
  refreshPromptCatalog(): Promise<void>;
}

export interface DiagnosticsProtocol {
  showDiagnostics(): Promise<void>;
}
