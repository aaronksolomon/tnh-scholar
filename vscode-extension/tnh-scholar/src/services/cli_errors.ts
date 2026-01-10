import { ErrorPayload } from "../models/api_payloads";

export class CliError extends Error {
  readonly payload?: ErrorPayload;
  readonly stderrTail?: string;

  constructor(message: string, payload?: ErrorPayload, stderrTail?: string) {
    super(message);
    this.name = "CliError";
    this.payload = payload;
    this.stderrTail = stderrTail;
  }
}
