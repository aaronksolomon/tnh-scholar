import * as path from "path";
import * as os from "os";

import { runTests } from "@vscode/test-electron";

async function main(): Promise<void> {
  try {
    const extensionDevelopmentPath = path.resolve(__dirname, "..", "..");
    const extensionTestsPath = path.resolve(__dirname, "./suite/index");
    const userDataDir = path.join(os.tmpdir(), "tnh-scholar-vscode-test-user");
    const extensionsDir = path.join(os.tmpdir(), "tnh-scholar-vscode-test-extensions");
    await runTests({
      extensionDevelopmentPath,
      extensionTestsPath,
      launchArgs: ["--user-data-dir", userDataDir, "--extensions-dir", extensionsDir],
    });
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error("Failed to run VS Code integration tests.");
    // eslint-disable-next-line no-console
    console.error(error);
    process.exit(1);
  }
}

void main();
