---
title: "ADR-VSC02: VS Code Extension Integration with tnh-gen CLI"
description: "VS Code extension strategy for consuming tnh-gen CLI and providing GenAI text processing UI"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: proposed
created: "2025-01-28"
updated: "2025-12-27"
---

# ADR-VSC02: VS Code Extension Integration with tnh-gen CLI

This ADR defines how the VS Code extension integrates with the `tnh-gen` CLI to provide GenAI-powered text processing capabilities within the editor.

- **Status**: Proposed
- **Date**: 2025-01-28
- **Updated**: 2025-12-27
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, Claude Sonnet 4.5

## Context

TNH Scholar users work primarily in VS Code for text editing and translation workflows. The VS Code extension needs to provide:

1. **Prompt Discovery**: Browse available prompts without leaving the editor
2. **Text Processing**: Execute prompts on selected text or open files
3. **Configuration Management**: Configure prompt directories and GenAI settings
4. **Provenance Tracking**: Show metadata about generated content

### Design Constraints

- **No Direct GenAI Integration**: Extension should not directly call OpenAI/Anthropic APIs
- **CLI as Contract**: Extension consumes `tnh-gen` CLI as stable interface
- **JSON Protocol**: Structured JSON I/O enables programmatic consumption
- **Error Handling**: Extension must gracefully handle CLI errors with user-friendly messages

### Related Work

- **ADR-VSC01**: VS Code Integration Strategy (establishes CLI-based architecture)
- **ADR-TG01**: CLI Architecture (defines `tnh-gen` command structure, error codes, configuration)
- **ADR-TG01.1**: Human-Friendly CLI Defaults (defines `--api` flag for machine-readable contract output)
- **ADR-TG02**: Prompt System Integration (defines CLI ↔ prompt system integration patterns)

## Decision

### 1. Extension Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                   VS Code Extension                         │
│  (TypeScript, VSCode API, UI components)                    │
└────────────────┬────────────────────────┬───────────────────┘
                 │                        │
         ┌───────▼───────┐          ┌──────▼────────┐
         │ CLI Adapter   │          │ UI Components │
         │ (spawn tnh-gen│          │ (prompts list,│
         │  parse JSON)  │          │  progress,    │
         │               │          │  config)      │
         └───────┬───────┘          └───────────────┘
                 │
         ┌───────▼───────┐
         │  tnh-gen CLI  │
         │  (Python)     │
         └───────────────┘
```

### 2. CLI Invocation Strategy

The extension spawns `tnh-gen` as a child process and communicates via JSON using the `--api` flag for structured API output (ADR-TG01.1):

- **Always pass `--api`** for machine-readable output; do not rely on `--format json` without `--api`.
- **Parse stdout as JSON**; treat stderr as diagnostics (warnings, trace IDs, debug info).

```typescript
// src/cli/CliAdapter.ts
import { spawn } from 'child_process';

export class TnhGenCliAdapter {
  private cliPath: string;

  constructor(cliPath: string) {
    this.cliPath = cliPath; // e.g., /path/to/venv/bin/tnh-gen
  }

  async listPrompts(options?: { tag?: string; search?: string }): Promise<PromptListResponse> {
    const args = ['list', '--api']; // Use --api for full API metadata
    if (options?.tag) args.push('--tag', options.tag);
    if (options?.search) args.push('--search', options.search);

    const result = await this.spawnCli(args);
    return JSON.parse(result.stdout);
  }

  async runPrompt(request: RunPromptRequest): Promise<RunPromptResponse> {
    const args = ['run', '--prompt', request.promptKey, '--api']; // Use --api for full response metadata

    // Add input file
    if (request.inputFile) {
      args.push('--input-file', request.inputFile);
    }

    // Add variables
    for (const [key, value] of Object.entries(request.variables)) {
      args.push('--var', `${key}=${value}`);
    }

    // Add output file
    if (request.outputFile) {
      args.push('--output-file', request.outputFile);
    }

    const result = await this.spawnCli(args);
    return JSON.parse(result.stdout);
  }

  private async spawnCli(args: string[]): Promise<{ stdout: string; stderr: string; exitCode: number }> {
    return new Promise((resolve, reject) => {
      const proc = spawn(this.cliPath, args);
      let stdout = '';
      let stderr = '';

      proc.stdout.on('data', (data) => stdout += data.toString());
      proc.stderr.on('data', (data) => stderr += data.toString());

      proc.on('close', (code) => {
        if (code === 0) {
          resolve({ stdout, stderr, exitCode: code });
        } else {
          reject(new CliError(stdout, stderr, code || -1));
        }
      });
    });
  }
}
```

### 3. Error Handling

Parse JSON error responses from `--api` mode (ADR-TG01.1 §3.4) and map CLI exit codes (ADR-TG01 §5) to user-friendly messages:

**Diagnostics**: stderr contains trace IDs and warnings for correlation; stdout remains JSON for programmatic parsing.

```typescript
// src/cli/CliError.ts
export class CliError extends Error {
  constructor(
    public stdout: string,
    public stderr: string,
    public exitCode: number
  ) {
    super(CliError.formatMessage(stdout, exitCode));
  }

  static formatMessage(stdout: string, exitCode: number): string {
    try {
      // With --api, errors are JSON with full diagnostics
      const response = JSON.parse(stdout);
      if (response.status === 'failed' && response.error) {
        // Use CLI's structured error message (ADR-TG01.1 §3.4)
        return response.diagnostics?.suggestion
          ? `${response.error}\n\nSuggestion: ${response.diagnostics.suggestion}`
          : response.error;
      }
    } catch {
      // Fallback to generic message if JSON parse fails
      return CliError.genericMessage(exitCode);
    }
  }

  static genericMessage(exitCode: number): string {
    switch (exitCode) {
      case 1: return 'Policy error: Budget exceeded or validation failed';
      case 2: return 'Transport error: API failure or network issue';
      case 3: return 'Provider error: Model unavailable or rate limit exceeded';
      case 4: return 'Format error: Invalid JSON or schema validation failed';
      case 5: return 'Input error: Invalid arguments or missing required variables';
      default: return `Unknown error (exit code ${exitCode})`;
    }
  }
}
```

### 4. UI Components

#### 4.1 Prompt Picker (Quick Pick)

```typescript
// src/commands/runPrompt.ts
import * as vscode from 'vscode';
import { TnhGenCliAdapter } from '../cli/CliAdapter';

export async function runPromptCommand(context: vscode.ExtensionContext) {
  const cli = new TnhGenCliAdapter(getCliPath(context));

  // 1. List prompts
  const response = await cli.listPrompts();

  // 2. Show quick pick
  const selected = await vscode.window.showQuickPick(
    response.prompts.map(p => ({
      label: p.name,
      description: p.tags.join(', '),
      detail: p.description,
      promptKey: p.key,
      requiredVariables: p.required_variables
    })),
    { placeHolder: 'Select a prompt to run' }
  );

  if (!selected) return;

  // 3. Collect variables
  const variables: Record<string, string> = {};
  for (const varName of selected.requiredVariables) {
    const value = await vscode.window.showInputBox({
      prompt: `Enter value for ${varName}`,
      placeHolder: varName
    });
    if (!value) return; // User cancelled
    variables[varName] = value;
  }

  // 4. Get input file (active document)
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showErrorMessage('No active document');
    return;
  }

  // Save document to temp file
  const inputFile = await saveTempFile(editor.document.getText());

  // 5. Execute prompt
  try {
    await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: 'Processing...' },
      async () => {
        const result = await cli.runPrompt({
          promptKey: selected.promptKey,
          inputFile,
          variables,
          outputFile: inputFile + '.out'
        });

        // 6. Show result
        const doc = await vscode.workspace.openTextDocument(inputFile + '.out');
        await vscode.window.showTextDocument(doc);
      }
    );
  } catch (error) {
    if (error instanceof CliError) {
      vscode.window.showErrorMessage(error.message);
    } else {
      throw error;
    }
  }
}
```

#### 4.2 Configuration Management

```typescript
// src/config/ConfigManager.ts
export class ConfigManager {
  static getCliPath(context: vscode.ExtensionContext): string {
    // Precedence: workspace > user > auto-detect
    const workspaceConfig = vscode.workspace.getConfiguration('tnhScholar');
    const cliPath = workspaceConfig.get<string>('cliPath');

    if (cliPath) return cliPath;

    // Auto-detect from active Python environment
    return this.detectCliPath();
  }

  private static detectCliPath(): string {
    // Use Python extension API to get active interpreter
    const pythonExt = vscode.extensions.getExtension('ms-python.python');
    if (pythonExt?.isActive) {
      const pythonPath = pythonExt.exports.settings.getExecutionDetails().execCommand[0];
      // Assume tnh-gen is in same venv
      return pythonPath.replace(/python$/, 'tnh-gen');
    }

    // Fallback to $PATH
    return 'tnh-gen';
  }
}
```

### 5. CLI Discovery and Version Checking

```typescript
// src/cli/CliValidator.ts
export class CliValidator {
  static async validateCli(cliPath: string): Promise<{ valid: boolean; version?: string; error?: string }> {
    try {
      const proc = spawn(cliPath, ['version', '--api']);
      const stdout = await this.readStream(proc.stdout);
      const version = JSON.parse(stdout);

      // Check minimum version
      if (this.compareVersions(version.tnh_gen, '0.1.0') < 0) {
        return {
          valid: false,
          error: `tnh-gen version ${version.tnh_gen} is too old (minimum: 0.1.0)`
        };
      }

      return { valid: true, version: version.tnh_gen };
    } catch (error) {
      return {
        valid: false,
        error: `Failed to execute tnh-gen at ${cliPath}: ${error.message}`
      };
    }
  }
}
```

### 6. Extension Configuration Schema

```json
// package.json (contributes.configuration)
{
  "contributes": {
    "configuration": {
      "title": "TNH Scholar",
      "properties": {
        "tnhScholar.cliPath": {
          "type": "string",
          "default": null,
          "description": "Path to tnh-gen CLI executable (auto-detected if not set)"
        },
        "tnhScholar.promptDirectory": {
          "type": "string",
          "default": null,
          "description": "Path to prompt directory (overrides TNH_PROMPT_DIR)"
        },
        "tnhScholar.defaultModel": {
          "type": "string",
          "default": "gpt-4o-mini",
          "description": "Default GenAI model for prompts"
        },
        "tnhScholar.maxCostUsd": {
          "type": "number",
          "default": 0.10,
          "description": "Maximum cost per request (USD)"
        }
      }
    }
  }
}
```

## Consequences

### Positive

- **Stable Contract**: Extension depends only on CLI JSON protocol via `--api` flag, not Python internals
- **Version Independence**: Extension and CLI can evolve independently
- **Error Transparency**: CLI exit codes and structured JSON errors (ADR-TG01.1) enable rich error handling
- **Full Metadata Access**: `--api` provides complete prompt metadata, provenance, usage stats
- **Testability**: CLI can be mocked for extension unit tests
- **Reusability**: CLI implementation (ADR-TG01/TG01.1/TG02) serves both VS Code and command-line users
- **Human-Friendly CLI**: Interactive CLI users get readable output by default, while extension gets full API metadata via `--api`

### Negative

- **Process Overhead**: Spawning Python process for each operation introduces latency (mitigated by keeping CLI operations fast)
- **Version Synchronization**: Extension must validate CLI version compatibility
- **Error Mapping**: Extension must parse CLI JSON errors and present user-friendly messages

### Risks

- **CLI Path Discovery**: Auto-detection may fail in complex Python environments (mitigated by explicit configuration)
- **Breaking Changes**: CLI protocol changes require coordinated extension updates (mitigated by semantic versioning)

## Alternatives Considered

### Alternative 1: Direct Python Integration (via Python Extension)

**Approach**: Extension imports TNH Scholar Python modules directly via VS Code Python extension API.

**Rejected**: Tight coupling to Python implementation. Extension would need to handle Python environment activation, dependency resolution, and version compatibility.

### Alternative 2: Language Server Protocol (LSP)

**Approach**: Create TNH Scholar language server that VS Code extension communicates with via LSP.

**Rejected**: Overengineering for initial MVP. LSP is designed for language features (completion, diagnostics), not GenAI operations.

### Alternative 3: REST API

**Approach**: Run TNH Scholar as HTTP server, extension makes REST calls.

**Rejected**: Adds complexity (server lifecycle management, port conflicts). CLI spawn model is simpler for single-user desktop usage.

## Open Questions

1. **Streaming Support**: How should extension handle streaming CLI output (future `--streaming` flag)?
2. **Multi-Root Workspaces**: How to handle different prompt directories per workspace folder?
3. **Offline Mode**: Should extension cache prompt list to avoid repeated CLI calls?

## References

### Related ADRs

- **[ADR-VSC01: VS Code Integration Strategy](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md)** - Overall VS Code strategy
- **[ADR-TG01: CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)** - CLI command structure, error codes, configuration
- **[ADR-TG01.1: Human-Friendly CLI Defaults](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md)** - `--api` flag for machine-readable contract output
- **[ADR-TG02: Prompt System Integration](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md)** - CLI ↔ prompt system integration
- **[ADR-AT03: AI Text Processing Refactor](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md)** - ai_text_processing refactor

### External Resources

- [VS Code Extension API](https://code.visualstudio.com/api)
- [VS Code Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [Typer CLI Framework](https://typer.tiangolo.com/)

---

## Changelog

### 2025-12-27: Updated for ADR-TG01.1 `--api` flag

- Changed all CLI invocations to use `--api` flag (replacing earlier `--verbose` design)
- `--api` is the machine-readable API contract mode for structured output (ADR-TG01.1)
- Updated error handling to parse structured JSON errors from `--api` mode
- Updated version checking to use `--api` flag
- Added reference to ADR-TG01.1 in Related Work and References sections
- Interactive CLI users now get human-friendly output by default
- Extension receives full API metadata via `--api` flag
- This is a breaking change from the initial `--verbose` design, done while ADR is still in proposed status

---

*This ADR focuses on VS Code extension strategy. CLI implementation details are defined in ADR-TG01, ADR-TG01.1, and ADR-TG02.*
