import httpx

from app.analysis.gemini import GeminiAnalysisProvider
from app.analysis.groq import GroqAnalysisProvider
from tests.analysis_fixtures import VALID_ANALYSIS_JSON


def test_gemini_requests_structured_output_without_exposing_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-goog-api-key"] == "synthetic-gemini-key"
        payload = __import__("json").loads(request.content)
        assert payload["generationConfig"]["responseMimeType"] == "application/json"
        assert "responseJsonSchema" in payload["generationConfig"]
        assert "fonte sintética" in payload["contents"][0]["parts"][0]["text"]
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": VALID_ANALYSIS_JSON}]}}]},
        )

    provider = GeminiAnalysisProvider(
        api_key="synthetic-gemini-key",
        model="gemini-test",
        base_url="https://gemini.invalid/v1beta",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = provider.analyze("fonte sintética")

    assert result.itens[0].status == "pendente"


def test_groq_uses_strict_json_schema() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = __import__("json").loads(request.content)
        assert payload["response_format"]["json_schema"]["strict"] is True
        assert payload["model"] == "openai/gpt-oss-120b"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": VALID_ANALYSIS_JSON}}]},
        )

    provider = GroqAnalysisProvider(
        api_key="synthetic-groq-key",
        model="openai/gpt-oss-120b",
        url="https://groq.invalid/chat/completions",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = provider.analyze("fonte sintética")

    assert result.objetivo.startswith("Planejar")


def test_groq_uses_distributed_excerpt_for_large_sources() -> None:
    captured_content = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_content
        payload = __import__("json").loads(request.content)
        captured_content = payload["messages"][1]["content"]
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": VALID_ANALYSIS_JSON}}]},
        )

    source = "A" * 10_000 + "B" * 10_000 + "C" * 10_000
    provider = GroqAnalysisProvider(
        api_key="synthetic-groq-key",
        model="openai/gpt-oss-120b",
        url="https://groq.invalid/chat/completions",
        max_input_characters=3_000,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    provider.analyze(source)

    assert "AAAA" in captured_content
    assert "BBBB" in captured_content
    assert "CCCC" in captured_content
    assert "trecho omitido" in captured_content
