import httpx

from app.analysis.http import post_json, validate_analysis
from app.analysis.models import StructuredAnalysis
from app.analysis.prompt import SYSTEM_INSTRUCTION, analysis_json_schema, build_analysis_prompt
from app.analysis.provider import AnalysisProviderError


class GeminiAnalysisProvider:
    name = "gemini"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.url = f"{base_url.rstrip('/')}/models/{model}:generateContent"
        self.client = client or httpx.Client(timeout=180)

    def analyze(self, text: str) -> StructuredAnalysis:
        response = post_json(
            client=self.client,
            provider=self.name,
            url=self.url,
            headers={"x-goog-api-key": self.api_key},
            payload={
                "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
                "contents": [{"role": "user", "parts": [{"text": build_analysis_prompt(text)}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseJsonSchema": analysis_json_schema(),
                    "temperature": 0.1,
                },
            },
        )
        try:
            raw_json = response["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exception:
            raise AnalysisProviderError(self.name, "invalid_response") from exception
        return validate_analysis(self.name, raw_json)
