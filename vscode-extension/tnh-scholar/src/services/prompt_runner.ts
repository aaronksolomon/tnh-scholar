import { ListApiEntry } from "../models/api_payloads";
import { ResolvedSettings, TempConfigFile } from "../models/settings";
import {
  CliAdapterProtocol,
  ConfigManagerProtocol,
  OutputChannelProtocol,
  PromptRunnerProtocol,
} from "../protocols/extension_protocols";
import { CliError } from "./cli_errors";
import { TnhGenCliAdapter } from "./cli_adapter";
import { EditorService } from "./editor_service";
import { FileService } from "./file_service";

interface RunContext {
  document: import("vscode").TextDocument;
  settings: ResolvedSettings;
  tempConfig: TempConfigFile;
  cliAdapter: CliAdapterProtocol;
}

export class PromptRunner implements PromptRunnerProtocol {
  private readonly configManager: ConfigManagerProtocol;
  private readonly editor: EditorService;
  private readonly files: FileService;
  private readonly logger: OutputChannelProtocol;

  constructor(
    configManager: ConfigManagerProtocol,
    editor: EditorService,
    files: FileService,
    logger: OutputChannelProtocol,
  ) {
    this.configManager = configManager;
    this.editor = editor;
    this.files = files;
    this.logger = logger;
  }

  async runOnActiveFile(): Promise<void> {
    try {
      const context = await this.prepareContext();
      const selected = await this.selectPrompt(context);
      if (!selected) {
        return;
      }
      const variables = await this.collectVariables(selected);
      if (!variables) {
        return;
      }
      await this.executePrompt(context, selected, variables);
    } catch (error) {
      this.handleError(error);
    }
  }

  async refreshPromptCatalog(): Promise<void> {
    try {
      const context = await this.prepareContext();
      const listPayload = await context.cliAdapter.listPrompts(context.tempConfig.path);
      this.editor.showInfo(`Prompt catalog refreshed (${listPayload.count} prompts).`);
    } catch (error) {
      this.handleError(error);
    }
  }

  private async prepareContext(): Promise<RunContext> {
    const document = this.editor.getActiveDocument();
    const settings = await this.configManager.resolveSettings();
    const tempConfig = await this.configManager.writeTempConfig(settings);
    const cliAdapter = this.createCliAdapter(settings.cliPath);
    return { document, settings, tempConfig, cliAdapter };
  }

  private async selectPrompt(context: RunContext): Promise<ListApiEntry | undefined> {
    const listPayload = await context.cliAdapter.listPrompts(context.tempConfig.path);
    if (!listPayload.prompts.length) {
      this.editor.showError("No prompts found. Check your prompt directory settings.");
      return undefined;
    }
    return this.editor.pickPrompt(listPayload.prompts);
  }

  private async collectVariables(prompt: ListApiEntry): Promise<Record<string, string> | undefined> {
    const required = await this.editor.collectRequiredVariables(prompt.required_variables);
    if (!required) {
      return undefined;
    }
    const optional = await this.editor.collectOptionalVariables(prompt.optional_variables);
    return { ...required, ...optional };
  }

  private async executePrompt(
    context: RunContext,
    prompt: ListApiEntry,
    variables: Record<string, string>,
  ): Promise<void> {
    const inputFile = await this.files.writeTempInput(context.document);
    const outputFile = this.files.buildOutputPath(context.document, prompt.key);
    await context.cliAdapter.runPrompt(context.tempConfig.path, {
      promptKey: prompt.key,
      inputFile,
      outputFile,
      inlineVars: variables,
    });
    await this.files.openOutputFile(outputFile);
    this.editor.showInfo(`Prompt "${prompt.name || prompt.key}" completed.`);
  }

  private handleError(error: unknown): void {
    if (error instanceof CliError) {
      const suggestion = error.payload?.diagnostics?.suggestion;
      const message = suggestion ? `${error.message} (${suggestion})` : error.message;
      this.editor.showError(message);
      if (error.stderrTail) {
        this.logger.warn(error.stderrTail);
      }
      return;
    }
    const message = error instanceof Error ? error.message : "Unexpected error";
    this.editor.showError(message);
  }

  private createCliAdapter(cliPath: string): CliAdapterProtocol {
    return new TnhGenCliAdapter(cliPath, this.logger);
  }
}
