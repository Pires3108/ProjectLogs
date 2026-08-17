from pydantic import BaseModel, Field, model_validator


class TranscriptSegment(BaseModel):
    inicio_segundos: float = Field(ge=0)
    fim_segundos: float = Field(gt=0)
    texto: str = Field(min_length=1)
    locutor: str | None = None

    @model_validator(mode="after")
    def validate_time_range(self) -> "TranscriptSegment":
        if self.fim_segundos <= self.inicio_segundos:
            raise ValueError("fim_segundos deve ser maior que inicio_segundos")
        return self


class TranscriptionResult(BaseModel):
    texto: str = Field(min_length=1)
    idioma: str | None = None
    duracao_segundos: float | None = Field(default=None, gt=0)
    segmentos: list[TranscriptSegment] = Field(default_factory=list)
    provedor: str
    modelo: str
