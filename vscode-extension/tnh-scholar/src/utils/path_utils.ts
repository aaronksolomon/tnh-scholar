import * as path from "path";

export function sanitizePromptKey(value: string): string {
  return value.trim().replace(/\s+/g, "-");
}

export function buildOutputPath(fileName: string, promptKey: string): string {
  const parsed = path.parse(fileName);
  const suffix = sanitizePromptKey(promptKey);
  return path.join(parsed.dir, `${parsed.name}.${suffix}${parsed.ext}`);
}
