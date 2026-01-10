export interface ErrorDiagnostics {
  error_type?: string;
  error_code?: string;
  suggestion?: string;
}

export interface ErrorPayload {
  status: string;
  error: string;
  diagnostics: ErrorDiagnostics;
  trace_id: string;
}

export interface ListApiEntry {
  key: string;
  name: string;
  description: string;
  tags: string[];
  required_variables: string[];
  optional_variables: string[];
  default_variables: Record<string, unknown>;
  default_model: string | null;
  output_mode: string | null;
  version: string;
  warnings: string[];
}

export interface ListApiPayload {
  prompts: ListApiEntry[];
  count: number;
  sources: string[];
}

export interface RunUsagePayload {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface RunResultPayload {
  text: string;
  model: string | null;
  provider: string | null;
  usage: RunUsagePayload | null;
  finish_reason: string | null;
}

export interface RunProvenancePayload {
  backend: string;
  model: string;
  prompt_key: string;
  prompt_fingerprint: string;
  prompt_version: string;
  started_at: string;
  completed_at: string;
  schema_version: string;
}

export interface RunSuccessPayload {
  status: string;
  result: RunResultPayload;
  provenance: RunProvenancePayload;
  warnings: string[] | null;
  prompt_warnings: string[];
  policy_applied: Record<string, unknown>;
  sources: string[];
  trace_id: string;
}

export interface VersionPayload {
  tnh_scholar: string;
  tnh_gen: string;
  python: string;
  platform: string;
  prompt_system_version: string;
  genai_service_version: string;
  trace_id: string;
}
