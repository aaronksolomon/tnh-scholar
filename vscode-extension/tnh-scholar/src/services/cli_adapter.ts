import { ErrorPayload, ListApiPayload, RunSuccessPayload, VersionPayload } from "../models/api_payloads";
import { CliAdapterProtocol, OutputChannelProtocol, RunPromptRequest } from "../protocols/extension_protocols";
import { CliArgsBuilder } from "./cli_args_builder";
import { CliError } from "./cli_errors";

export interface ExecRunner {
  run(command: string, args: string[]): Promise<{ stdout: string; stderr: string }>;
}

export class NodeExecRunner implements ExecRunner {
  private readonly execFileAsync: (
    command: string,
    args: string[],
    options?: { maxBuffer?: number },
  ) => Promise<{ stdout: string; stderr: string }>;

  constructor() {
    const { execFile } = require("child_process");
    const { promisify } = require("util");
    this.execFileAsync = promisify(execFile);
  }

  async run(command: string, args: string[]): Promise<{ stdout: string; stderr: string }> {
    return this.execFileAsync(command, args, { maxBuffer: 1024 * 1024 * 10 });
  }
}

export class TnhGenCliAdapter implements CliAdapterProtocol {
  private readonly cliPath: string;
  private readonly logger: OutputChannelProtocol;
  private readonly argsBuilder: CliArgsBuilder;
  private readonly runner: ExecRunner;

  constructor(cliPath: string, logger: OutputChannelProtocol, runner: ExecRunner = new NodeExecRunner()) {
    this.cliPath = cliPath;
    this.logger = logger;
    this.argsBuilder = new CliArgsBuilder();
    this.runner = runner;
  }

  async listPrompts(configPath: string): Promise<ListApiPayload> {
    return await this.runJsonCommand<ListApiPayload>(configPath, ["list"]);
  }

  async runPrompt(configPath: string, request: RunPromptRequest): Promise<RunSuccessPayload> {
    const args = this.argsBuilder.buildRunArgs(request);
    return this.runJsonCommand<RunSuccessPayload>(configPath, ["run", ...args]);
  }

  async getVersion(configPath: string): Promise<VersionPayload> {
    return this.runJsonCommand<VersionPayload>(configPath, ["version"]);
  }

  private async runJsonCommand<T>(configPath: string, commandArgs: string[]): Promise<T> {
    const args = this.argsBuilder.buildGlobalArgs(configPath, commandArgs);
    const result = await this.execute(args);
    return this.parseJson<T>(result.stdout, result.stderr);
  }

  private async execute(args: string[]): Promise<{ stdout: string; stderr: string }> {
    this.logger.info(`tnh-gen ${args.join(" ")}`);
    try {
      const { stdout, stderr } = await this.runner.run(this.cliPath, args);
      if (stderr) {
        this.logger.warn(stderr.trim());
      }
      return { stdout, stderr };
    } catch (error) {
      const execError = error as { stdout?: string; stderr?: string; message: string };
      const stdout = execError.stdout ?? "";
      const stderr = execError.stderr ?? "";
      const payload = this.parseError(stdout);
      const stderrTail = this.stderrTail(stderr);
      throw new CliError(payload?.error ?? execError.message, payload, stderrTail);
    }
  }

  private parseJson<T>(stdout: string, stderr: string): T {
    try {
      return JSON.parse(stdout) as T;
    } catch (error) {
      const stderrTail = this.stderrTail(stderr);
      throw new CliError("Failed to parse CLI JSON output.", undefined, stderrTail);
    }
  }

  private parseError(stdout: string): ErrorPayload | undefined {
    try {
      const payload = JSON.parse(stdout) as ErrorPayload;
      if (payload?.status === "failed") {
        return payload;
      }
    } catch {
      return undefined;
    }
    return undefined;
  }

  private stderrTail(stderr: string): string | undefined {
    if (!stderr) {
      return undefined;
    }
    const lines = stderr.trim().split(/\r?\n/);
    return lines.slice(-8).join("\n");
  }
}
