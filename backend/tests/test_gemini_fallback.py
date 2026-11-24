import pytest
from google.genai import errors, types

from app.adapters.llm.gemini import ModelSelector


def _error(code: int) -> errors.APIError:
    error_class = errors.ServerError if code >= 500 else errors.ClientError
    return error_class(code, {"error": {"code": code, "message": "test", "status": "TEST"}})


class FakeModels:
    def __init__(self, failures: dict[str, int]) -> None:
        self.failures = failures
        self.calls: list[str] = []

    def generate_content(self, model, contents, config):
        self.calls.append(model)
        if model in self.failures:
            raise _error(self.failures[model])
        return f"response from {model}"


class FakeClient:
    def __init__(self, failures: dict[str, int]) -> None:
        self.models = FakeModels(failures)


CONFIG = types.GenerateContentConfig()


def test_overloaded_primary_falls_back_and_stays_on_fallback():
    client = FakeClient({"primary": 503})
    selector = ModelSelector(client, ["primary", "lite"])

    assert selector.generate("q", CONFIG) == "response from lite"
    assert selector.generate("q", CONFIG) == "response from lite"
    assert client.models.calls == ["primary", "lite", "lite"]


@pytest.mark.parametrize("code", [429, 504])
def test_rate_limited_or_timed_out_primary_also_falls_back(code):
    client = FakeClient({"primary": code})
    assert ModelSelector(client, ["primary", "lite"]).generate("q", CONFIG) == "response from lite"


def test_non_retryable_error_is_raised_without_fallback():
    client = FakeClient({"primary": 404})
    with pytest.raises(errors.ClientError):
        ModelSelector(client, ["primary", "lite"]).generate("q", CONFIG)
    assert client.models.calls == ["primary"]


def test_error_is_raised_when_every_model_is_overloaded():
    client = FakeClient({"primary": 503, "lite": 503})
    with pytest.raises(errors.ServerError):
        ModelSelector(client, ["primary", "lite"]).generate("q", CONFIG)


class _JsonResponse:
    def __init__(self, text: str) -> None:
        self.text = text
        self.usage_metadata = None


class _JsonModels:
    def __init__(self, text: str) -> None:
        self.text = text

    def generate_content(self, model, contents, config):
        return _JsonResponse(self.text)


def _compose(text: str):
    from app.adapters.llm.gemini import GeminiLLM

    client = type("Client", (), {"models": _JsonModels(text)})()
    llm = GeminiLLM(api_key="k", model="m", system_instruction="s", client=client)
    return llm.compose_answer("pregunta", [])


def test_final_answer_carries_gap_kind_only_for_gaps():
    gap = _compose('{"answer": "No doy nombres.", "cited_evidence_ids": [], '
                   '"status": "information_gap", "gap_kind": "out_of_scope"}')
    answered = _compose('{"answer": "Hola", "cited_evidence_ids": [], "status": "answered", '
                        '"gap_kind": "out_of_scope"}')
    default = _compose('{"answer": "No está.", "cited_evidence_ids": [], '
                       '"status": "information_gap"}')

    assert gap.gap_kind == "out_of_scope"
    assert answered.gap_kind is None
    assert default.gap_kind == "unpublished_data"


def test_answered_draft_carries_partial_gap_when_missing_data_is_named():
    partial = _compose('{"answer": "Solo hay presupuesto de malla vial (E1).", '
                       '"cited_evidence_ids": ["E1"], "status": "answered", "gap_topic": "vías", '
                       '"gap_missing_data": "huecos tapados en 2025", '
                       '"gap_kind": "unpublished_data"}')
    complete = _compose('{"answer": "Se ejecutó el 60 % (E1).", "cited_evidence_ids": ["E1"], '
                        '"status": "answered"}')

    assert partial.status == "answered"
    assert partial.gap_topic == "vías"
    assert partial.gap_missing_data == "huecos tapados en 2025"
    assert partial.gap_kind == "unpublished_data"
    assert complete.gap_missing_data is None
    assert complete.gap_kind is None  # the field default alone never makes a partial answer
