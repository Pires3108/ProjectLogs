import httpx

from app.analysis.http import post_json, validate_analysis
from app.analysis.models import StructuredAnalysis
from app.analysis.prompt import SYSTEM_INSTRUCTION, analysis_json_schema, build_analysis_prompt
from app.analysis.provider import AnalysisProviderError


class GroqAnalysisProvider:
    name = "groq"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        url: str,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.url = url
        self.client = client or httpx.Client(timeout=180)

    def analyze(self, text: str) -> StructuredAnalysis:
        response = post_json(
            client=self.client,
            provider=self.name,
            url=self.url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            payload={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": build_analysis_prompt(text)},
                ],
                "temperature": 0.1,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "meeting_analysis",
                        "strict": True,
                        "schema": analysis_json_schema(),
                    },
                },
            },
        )
        try:
            raw_json = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exception:
            raise AnalysisProviderError(self.name, "invalid_response") from exception
        return validate_analysis(self.name, raw_json)
