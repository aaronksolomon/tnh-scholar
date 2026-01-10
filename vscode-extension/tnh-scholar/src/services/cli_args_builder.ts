import { RunPromptRequest } from "../protocols/extension_protocols";

export class CliArgsBuilder {
  buildGlobalArgs(configPath: string, commandArgs: string[]): string[] {
    return ["--api", "--config", configPath, ...commandArgs];
  }

  buildRunArgs(request: RunPromptRequest): string[] {
    const args = [
      "--prompt",
      request.promptKey,
      "--input-file",
      request.inputFile,
      "--output-file",
      request.outputFile,
    ];
    if (request.model) {
      args.push("--model", request.model);
    }
    if (request.temperature !== undefined) {
      args.push("--temperature", String(request.temperature));
    }
    if (request.maxTokens !== undefined) {
      args.push("--max-tokens", String(request.maxTokens));
    }
    for (const [key, value] of Object.entries(request.inlineVars)) {
      args.push("--var", `${key}=${value}`);
    }
    return args;
  }
}
