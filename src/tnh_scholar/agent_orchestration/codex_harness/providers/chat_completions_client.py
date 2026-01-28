"""OpenAI Chat Completions API client for Codex harness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from tnh_scholar.agent_orchestration.codex_harness.models import (
    CodexRequest,
    CodexResponseText,
    CodexStructuredOutput,
)
from tnh_scholar.agent_orchestration.codex_harness.protocols import ResponsesClientProtocol, ToolRegistryProtocol
from tnh_scholar.agent_orchestration.codex_harness.tools import ToolCall, ToolDefinition, ToolName, ToolResult


@dataclass(frozen=True)
class ChatCompletionsClient(ResponsesClientProtocol):
    """Chat Completions API client for Codex harness."""

    api_key: str | None

    def run(self, request: CodexRequest, tool_registry: ToolRegistryProtocol) -> CodexResponseText:
        """Execute the request and return response text."""
        client = OpenAI(api_key=self.api_key)
        tools = self._build_tools(tool_registry.definitions())
        response, messages = self._create_completion(client, request, tools)
        for _ in range(request.max_tool_rounds):
            tool_calls = self._parse_tool_calls(response)
            if not tool_calls:
                break
            tool_outputs = self._execute_tool_calls(tool_registry, tool_calls)
            response, messages = self._submit_tool_outputs(
                client,
                request,
                messages,
                tool_calls,
                tool_outputs,
                tools,
            )
        text = self._extract_text(response)
        raw_payload = self._serialize_response(response)
        return CodexResponseText(text=text, raw_payload=raw_payload)

    def _create_completion(
        self,
        client: OpenAI,
        request: CodexRequest,
        tools: list[dict[str, object]],
    ) -> tuple[Any, list[dict[str, object]]]:
        messages = [{"role": message.role, "content": message.content} for message in request.messages]
        payload = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_output_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "codex_output",
                    "schema": CodexStructuredOutput.model_json_schema(),
                },
            },
        }
        if tools:
            payload["tools"] = tools
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        response = client.chat.completions.create(**payload)
        return response, messages

    def _submit_tool_outputs(
        self,
        client: OpenAI,
        request: CodexRequest,
        messages: list[dict[str, object]],
        tool_calls: list[ToolCall],
        tool_outputs: list[dict[str, object]],
        tools: list[dict[str, object]],
    ) -> tuple[Any, list[dict[str, object]]]:
        assistant_message = {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": call.call_id,
                    "type": "function",
                    "function": {"name": call.name.value, "arguments": call.arguments_json},
                }
                for call in tool_calls
            ],
        }
        messages.append(assistant_message)
        for output in tool_outputs:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": output["tool_call_id"],
                    "content": output["content"],
                }
            )
        payload = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_output_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "codex_output",
                    "schema": CodexStructuredOutput.model_json_schema(),
                },
            },
        }
        if tools:
            payload["tools"] = tools
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        response = client.chat.completions.create(**payload)
        return response, messages

    def _extract_text(self, response: Any) -> str:
        choices = getattr(response, "choices", [])
        if not choices:
            return ""
        message = getattr(choices[0], "message", None)
        if not message:
            return ""
        content = getattr(message, "content", None)
        return content or ""

    def _serialize_response(self, response: Any) -> str:
        dump = getattr(response, "model_dump_json", None)
        if callable(dump):
            return dump(indent=2)
        return str(response)

    def _build_tools(self, definitions: list[ToolDefinition]) -> list[dict[str, object]]:
        payloads: list[dict[str, object]] = []
        for definition in definitions:
            payloads.append(
                {
                    "type": "function",
                    "function": {
                        "name": definition.name.value,
                        "description": definition.description,
                        "parameters": definition.parameters_schema,
                    },
                }
            )
        return payloads

    def _parse_tool_calls(self, response: Any) -> list[ToolCall]:
        choices = getattr(response, "choices", [])
        if not choices:
            return []
        message = getattr(choices[0], "message", None)
        if not message:
            return []
        tool_calls = getattr(message, "tool_calls", None)
        if not tool_calls:
            return []
        calls: list[ToolCall] = []
        for call in tool_calls:
            call_id = getattr(call, "id", None)
            function = getattr(call, "function", None)
            name = getattr(function, "name", None) if function else None
            arguments = getattr(function, "arguments", None) if function else None
            if not call_id or not name or arguments is None:
                continue
            calls.append(ToolCall(name=ToolName(name), call_id=call_id, arguments_json=arguments))
        return calls

    def _execute_tool_calls(
        self,
        tool_registry: ToolRegistryProtocol,
        tool_calls: list[ToolCall],
    ) -> list[dict[str, object]]:
        outputs: list[dict[str, object]] = []
        for call in tool_calls:
            result = tool_registry.execute(call)
            outputs.append(self._tool_output_item(result))
        return outputs

    def _tool_output_item(self, result: ToolResult) -> dict[str, object]:
        return {
            "tool_call_id": result.call_id,
            "content": result.output_json,
        }
