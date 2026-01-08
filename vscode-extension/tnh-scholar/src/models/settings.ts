export interface ExtensionSettings {
  cliPath?: string | null;
  promptDirectory?: string | null;
  defaultModel?: string | null;
  maxCostUsd?: number | null;
}

export interface ResolvedSettings {
  cliPath: string;
  promptDirectory?: string;
  defaultModel?: string;
  maxCostUsd?: number;
}

export interface TempConfigFile {
  path: string;
}
