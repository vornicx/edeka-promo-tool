from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class FormatType(str, Enum):
    STORY = "story"
    POST = "post"
    POSTER_A4 = "poster_a4"
    POSTER_A5 = "poster_a5"


class ToneType(str, Enum):
    FRESCO = "fresco"
    PREMIUM = "premium"
    ATREVIDO = "atrevido"
    LOCAL = "local"


class DifferentiationLevel(str, Enum):
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"


class PromotionSpec(BaseModel):
    product: str = Field(..., min_length=1, description="Nombre del producto")
    category: Optional[str] = Field(None, description="Categoría del producto")
    price: str = Field(..., min_length=1, description="Precio actual")
    old_price: Optional[str] = Field(None, description="Precio anterior (tachado)")
    validity: str = Field(..., min_length=1, description="Vigencia de la oferta")
    origin: Optional[str] = Field(None, description="Origen del producto")
    claim: Optional[str] = Field(None, description="Claim corto promocional")
    format: FormatType = Field(default=FormatType.POST, description="Formato de salida")
    tone: ToneType = Field(default=ToneType.FRESCO, description="Tono visual")
    differentiation_level: DifferentiationLevel = Field(
        default=DifferentiationLevel.MEDIO,
        description="Nivel de diferenciación visual",
    )


class EnrichmentSpec(BaseModel):
    campaign_type: str = Field(..., description="Tipo de campaña")
    product_family: str = Field(..., description="Familia del producto")
    seasonality: str = Field(..., description="Estacionalidad detectada")
    communication_style: str = Field(..., description="Estilo de comunicación")
    price_priority: str = Field(..., description="Prioridad del precio (high/medium/low)")
    visual_energy: str = Field(..., description="Energía visual (low/medium_low/medium/medium_high/high)")
    brand_mode: str = Field(..., description="Modo de marca")
    waschbaer_presence: str = Field(..., description="Presencia del Waschbär")


class CreativeDirection(BaseModel):
    name: str = Field(..., description="Nombre de la dirección")
    intent: str = Field(..., description="Intención visual")
    composition: str = Field(..., description="Descripción de la composición")
    palette: list[str] = Field(..., description="Colores dominantes en hex")
    text_safe_area: str = Field(..., description="Zona segura para texto")
    boldness: str = Field(..., description="Nivel de atrevimiento")
    waschbaer_presence: str = Field(..., description="Presencia del Waschbär")


class CreativeDirectionsResponse(BaseModel):
    directions: list[CreativeDirection] = Field(..., min_length=1, max_length=3)


class QualityReport(BaseModel):
    approved: bool
    score: float = Field(ge=0, le=10)
    checks: dict[str, str] = Field(default_factory=dict)
    suggestions: list[str] = Field(default_factory=list)


class ExportFormat(BaseModel):
    format: FormatType
    width: int
    height: int
    label: str


EXPORT_FORMATS: dict[FormatType, ExportFormat] = {
    FormatType.STORY: ExportFormat(
        format=FormatType.STORY, width=1080, height=1920, label="Instagram Story"
    ),
    FormatType.POST: ExportFormat(
        format=FormatType.POST, width=1080, height=1080, label="Instagram Post"
    ),
    FormatType.POSTER_A4: ExportFormat(
        format=FormatType.POSTER_A4, width=2480, height=3508, label="Poster A4"
    ),
    FormatType.POSTER_A5: ExportFormat(
        format=FormatType.POSTER_A5, width=1748, height=2480, label="Poster A5"
    ),
}
