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


class CampaignKind(str, Enum):
    PRODUCT = "product"
    EVENT = "event"


class PromotionSpec(BaseModel):
    campaign_kind: CampaignKind = Field(default=CampaignKind.PRODUCT, description="Art der Promotion")
    product: str = Field(..., min_length=1, description="Produktname oder Eventtitel")
    category: Optional[str] = Field(None, description="Produktkategorie")
    price: str = Field(default="", description="Aktueller Preis oder Event-Hinweis")
    old_price: Optional[str] = Field(None, description="Vorheriger Preis (durchgestrichen)")
    validity: str = Field(..., min_length=1, description="Gültigkeit des Angebots")
    origin: Optional[str] = Field(None, description="Herkunft des Produkts")
    claim: Optional[str] = Field(None, description="Kurzer Werbeclaim")
    product_image: Optional[str] = Field(
        None,
        description="Bildquelle: leer/auto = nach Name, 'builtin:<key>' = integriertes Motiv, 'custom:<id>' = eigenes Foto",
    )
    format: FormatType = Field(default=FormatType.POST, description="Ausgabeformat")
    style: str = Field(default="edeka", description="Designstil: 'edeka' (Markenlook) | 'kreativ' (KI-Farben)")
    tone: ToneType = Field(default=ToneType.FRESCO, description="Visuelle Tonalität")
    differentiation_level: DifferentiationLevel = Field(
        default=DifferentiationLevel.MEDIO,
        description="Grad der visuellen Differenzierung",
    )


class EnrichmentSpec(BaseModel):
    campaign_type: str = Field(..., description="Kampagnentyp")
    product_family: str = Field(..., description="Produktfamilie")
    seasonality: str = Field(..., description="Erkannte Saisonalitaet")
    communication_style: str = Field(..., description="Kommunikationsstil")
    price_priority: str = Field(..., description="Preisprioritaet (high/medium/low)")
    visual_energy: str = Field(..., description="Visuelle Energie (low/medium_low/medium/medium_high/high)")
    brand_mode: str = Field(..., description="Markenmodus")
    waschbaer_presence: str = Field(..., description="Waschbaer-Praesenz")


class CreativeDirection(BaseModel):
    name: str = Field(..., description="Name der Richtung")
    intent: str = Field(..., description="Visuelle Absicht")
    composition: str = Field(..., description="Beschreibung der Komposition")
    palette: list[str] = Field(..., description="Dominante Farben als Hexwerte")
    text_safe_area: str = Field(..., description="Sicherer Textbereich")
    boldness: str = Field(..., description="Mutigkeitsgrad")
    waschbaer_presence: str = Field(..., description="Waschbaer-Praesenz")


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
    # 4K-class social formats for wide, high-quality use.
    FormatType.STORY: ExportFormat(
        format=FormatType.STORY, width=2160, height=3840, label="Instagram Story"
    ),
    FormatType.POST: ExportFormat(
        format=FormatType.POST, width=2160, height=2160, label="Instagram Post"
    ),
    FormatType.POSTER_A4: ExportFormat(
        format=FormatType.POSTER_A4, width=2480, height=3508, label="Poster A4"
    ),
    FormatType.POSTER_A5: ExportFormat(
        format=FormatType.POSTER_A5, width=1748, height=2480, label="Poster A5"
    ),
}
