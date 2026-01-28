"""OpenAI Responses API client for Codex harness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from tnh_scholar.agent_orchestration.codex_harness.models import CodexRequest, CodexResponseText
from tnh_scholar.agent_orchestration.codex_harness.protocols import ResponsesClientProtocol, ToolRegistryProtocol
from tnh_scholar.agent_orchestration.codex_harness.tools import (
    ToolCall,
    ToolDefinition,
    ToolName,
    ToolResult,
)


@dataclass(frozen=True)
class OpenAIResponsesClient(ResponsesClientProtocol):
    """Responses API client for Codex harness."""

    api_key: str | None
    schema_builder: object | None = None

    def run(self, request: CodexRequest, tool_registry: ToolRegistryProtocol) -> CodexResponseText:
        """Execute the request and return response text."""
        client = OpenAI(api_key=self.api_key)
        tools = self._build_tools(tool_registry.definitions())
        response = self._create_response(client, request, tools)
        for _ in range(request.max_tool_rounds):
            tool_calls = self._parse_tool_calls(response)
            if not tool_calls:
                break
            tool_outputs = self._execute_tool_calls(tool_registry, tool_calls)
            response = self._submit_tool_outputs(client, request, response.id, tool_outputs, tools)
        text = self._extract_text(response)
        raw_payload = self._serialize_response(response)
        return CodexResponseText(text=text, raw_payload=raw_payload)

    def _extract_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text
        output = getattr(response, "output", [])
        chunks: list[str] = []
        for item in output:
            content = getattr(item, "content", [])
            if not content:
                continue
            for part in content:
                text = getattr(part, "text", None)
                if text:
                    chunks.append(text)
        return "".join(chunks)

    def _serialize_response(self, response: Any) -> str:
        dump = getattr(response, "model_dump_json", None)
        if callable(dump):
            return dump(indent=2)
        return str(response)

    def _create_response(self, client: OpenAI, request: CodexRequest, tools: list[dict]) -> Any:
        input_payload = [
            {"role": message.role, "content": message.content}
            for message in request.messages
        ]
        payload = {
            "model": request.model,
            "input": input_payload,
            "max_output_tokens": request.max_output_tokens,
        }
        if tools:
            payload["tools"] = tools
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        return client.responses.create(**payload)

    def _submit_tool_outputs(
        self,
        client: OpenAI,
        request: CodexRequest,
        previous_response_id: str,
        tool_outputs: list[dict],
        tools: list[dict],
    ) -> Any:
        input_items = list(tool_outputs)
        input_items.append(
            {
                "role": "user",
                "content": "Continue the task using repo-relative paths and return ONLY JSON output.",
            }
        )
        payload = {
            "model": request.model,
            "input": input_items,
            "previous_response_id": previous_response_id,
            "max_output_tokens": request.max_output_tokens,
        }
        if tools:
            payload["tools"] = tools
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        return client.responses.create(**payload)

    def _build_tools(self, definitions: list[ToolDefinition]) -> list[dict]:
        payloads = []
        for definition in definitions:
            payloads.append(
                {
                    "type": "function",
                    "name": definition.name.value,
                    "description": definition.description,
                    "parameters": definition.parameters_schema,
                    "strict": True,
                }
            )
        return payloads

    def _parse_tool_calls(self, response: Any) -> list[ToolCall]:
        output = getattr(response, "output", [])
        calls: list[ToolCall] = []
        for item in output:
            if getattr(item, "type", None) != "function_call":
                continue
            call_id = getattr(item, "call_id", None)
            name = getattr(item, "name", None)
            arguments = getattr(item, "arguments", None)
            if not call_id or not name or arguments is None:
                continue
            calls.append(ToolCall(name=ToolName(name), call_id=call_id, arguments_json=arguments))
        return calls

    def _execute_tool_calls(
        self,
        tool_registry: ToolRegistryProtocol,
        tool_calls: list[ToolCall],
    ) -> list[dict]:
        outputs: list[dict] = []
        for call in tool_calls:
            result = tool_registry.execute(call)
            outputs.append(self._tool_output_item(result))
        return outputs

    def _tool_output_item(self, result: ToolResult) -> dict:
        return {
            "type": "function_call_output",
            "call_id": result.call_id,
            "output": result.output_json,
        }
