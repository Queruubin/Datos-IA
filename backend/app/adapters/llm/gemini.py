"""Gemini adapter (SDK `google-genai`) implementing `LLMPort` with MANUAL function calling.

Only function declarations are sent (never Python callables), so the SDK does not run tools on
its own: the use case executes every call deterministically and sends the results back.
"""

import json
from typing import Any, Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError

from app.application.prompts import COMPOSE_INSTRUCTIONS, wrap_question
from app.domain import DraftAnswer, ToolCall, ToolOutcome, ToolSpec
from app.ports import LLMOutputError


class FinalAnswerSchema(BaseModel):
    """Structured output requested from Gemini for the final answer."""

    answer: str = Field(description="Respuesta en español claro para el ciudadano.")
    cited_evidence_ids: list[str] = Field(description="Ids de evidencia usados, p. ej. ['E1'].")
    status: Literal["answered", "information_gap", "needs_clarification"]
    gap_topic: str = Field(default="", description="Tema del vacío de información, si aplica.")
    gap_missing_data: str = Field(default="", description="Dato que haría falta, si aplica.")


class GeminiLLM:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_instruction: str,
        temperature: float = 0.2,
        client: Any | None = None,
    ) -> None:
        self._client = client or genai.Client(api_key=api_key)
        self._model = model
        self._system_instruction = system_instruction
        self._temperature = temperature

    def start_planning(self, question: str, tools: list[ToolSpec]) -> "GeminiPlanningSession":
        tool = types.Tool(function_declarations=[
            types.FunctionDeclaration(
                name=spec.name,
                description=spec.description,
                parameters_json_schema=spec.parameters_json_schema,
            )
            for spec in tools
        ])
        config = types.GenerateContentConfig(
            tools=[tool],
            system_instruction=self._system_instruction,
            temperature=self._temperature,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        return GeminiPlanningSession(self._client, self._model, config, question)

    def compose_answer(self, question: str, results: list[ToolOutcome]) -> DraftAnswer:
        tool_results = [
            {"tool": outcome.call.name, "args": outcome.call.args, **outcome.to_model_payload()}
            for outcome in results
        ]
        prompt = (
            f"{wrap_question(question)}\n\n{COMPOSE_INSTRUCTIONS}\n"
            "Resultados de herramientas (JSON):\n"
            f"{json.dumps(tool_results, ensure_ascii=False, default=str)}"
        )
        config = types.GenerateContentConfig(
            system_instruction=self._system_instruction,
            temperature=self._temperature,
            response_mime_type="application/json",
            response_json_schema=FinalAnswerSchema.model_json_schema(),
        )
        response = self._client.models.generate_content(
            model=self._model, contents=prompt, config=config
        )
        try:
            parsed = FinalAnswerSchema.model_validate_json(response.text or "")
        except ValidationError as error:
            raise LLMOutputError("Gemini final answer does not match the schema") from error
        return DraftAnswer(
            answer=parsed.answer,
            cited_evidence_ids=parsed.cited_evidence_ids,
            status=parsed.status,
            gap_topic=parsed.gap_topic or None,
            gap_missing_data=parsed.gap_missing_data or None,
        )


class GeminiPlanningSession:
    """Keeps the raw conversation so model turns (and their thought signatures) are preserved."""

    def __init__(self, client: Any, model: str, config: types.GenerateContentConfig,
                 question: str) -> None:
        self._client = client
        self._model = model
        self._config = config
        self._contents: list[types.Content] = [
            types.Content(role="user", parts=[types.Part.from_text(text=wrap_question(question))])
        ]

    def next_tool_calls(self, results: list[ToolOutcome] | None) -> list[ToolCall]:
        if results:
            parts = []
            for outcome in results:
                part = types.Part.from_function_response(
                    name=outcome.call.name, response=outcome.to_model_payload()
                )
                if outcome.call.call_id and part.function_response is not None:
                    part.function_response.id = outcome.call.call_id
                parts.append(part)
            self._contents.append(types.Content(role="user", parts=parts))

        response = self._client.models.generate_content(
            model=self._model, contents=self._contents, config=self._config
        )
        calls = response.function_calls or []
        if calls:
            # Append the model turn as-is: it carries the thought signatures Gemini requires.
            self._contents.append(response.candidates[0].content)
        return [
            ToolCall(name=call.name or "", args=dict(call.args or {}), call_id=call.id)
            for call in calls
        ]
