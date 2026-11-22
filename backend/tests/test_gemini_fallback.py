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
