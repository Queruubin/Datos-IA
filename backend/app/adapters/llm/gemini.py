"""Gemini adapter (SDK `google-genai`) implementing `LLMPort` with MANUAL function calling.

Only function declarations are sent (never Python callables), so the SDK does not run tools on
its own: the use case executes every call deterministically and sends the results back.
"""

import json
import logging
from typing import Any, Literal

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field, ValidationError

from app.application.prompts import COMPOSE_INSTRUCTIONS, wrap_question
from app.domain import DraftAnswer, ToolCall, ToolOutcome, ToolSpec
from app.ports import LLMOutputError

logger = logging.getLogger(__name__)

# Provider-side conditions where trying another model makes sense.
RETRYABLE_CODES = {429, 503, 504}


class ModelSelector:
    """Calls Gemini with the current model and moves to the next one when it is overloaded.

    The choice is sticky for the whole question: once a planning conversation moved to a fallback
    model it stays there, because thought signatures belong to the model that produced them.
    """

    def __init__(self, client: Any, models: list[str]) -> None:
        self._client = client
        self._models = models
        self._index = 0

    def generate(self, contents: Any, config: types.GenerateContentConfig) -> Any:
        while True:
            model = self._models[self._index]
            try:
                return self._client.models.generate_content(
                    model=model, contents=contents, config=config
                )
            except errors.APIError as error:
                is_last = self._index == len(self._models) - 1
                if error.code not in RETRYABLE_CODES or is_last:
                    raise
                logger.warning("Gemini model %s unavailable (code=%s); falling back to %s",
                               model, error.code, self._models[self._index + 1])
                self._index += 1


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
        fallback_models: list[str] | None = None,
        timeout_seconds: float = 30,
        client: Any | None = None,
    ) -> None:
        # Without a timeout an overloaded model can hold the request for minutes.
        self._client = client or genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=int(timeout_seconds * 1000)),
        )
        self._models = [model, *(fallback_models or [])]
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
        return GeminiPlanningSession(ModelSelector(self._client, self._models), config, question)

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
        response = ModelSelector(self._client, self._models).generate(prompt, config)
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

    def __init__(self, selector: ModelSelector, config: types.GenerateContentConfig,
                 question: str) -> None:
        self._selector = selector
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

        response = self._selector.generate(self._contents, self._config)
        calls = response.function_calls or []
        if calls:
            # Append the model turn as-is: it carries the thought signatures Gemini requires.
            self._contents.append(response.candidates[0].content)
        return [
            ToolCall(name=call.name or "", args=dict(call.args or {}), call_id=call.id)
            for call in calls
        ]
