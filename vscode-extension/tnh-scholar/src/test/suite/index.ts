import * as path from "path";

import Mocha from "mocha";
import { glob } from "glob";

export async function run(): Promise<void> {
  const mocha = new Mocha({
    ui: "tdd",
    color: true,
  });

  const testsRoot = path.resolve(__dirname, "..", "integration");
  const files = await glob("**/*.test.js", { cwd: testsRoot });
  files.forEach((file) => mocha.addFile(path.join(testsRoot, file)));

  return new Promise((resolve, reject) => {
    try {
      mocha.run((failures: number) => {
        if (failures > 0) {
          reject(new Error(`${failures} test(s) failed.`));
          return;
        }
        resolve();
      });
    } catch (error) {
      reject(error);
    }
  });
}
