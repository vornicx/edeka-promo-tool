from __future__ import annotations

from app.adapters.base import AIAdapter
from app.schemas.promotion import CreativeDirection, EnrichmentSpec, PromotionSpec


SYSTEM_PROMPT = """Du bist Creative Director und Senior Grafikdesigner für EDEKA Mühlenbein.
Deine Aufgabe: visuell beeindruckende, moderne Werbedesigns entwerfen, die Aufmerksamkeit erregen.

VISUELLER ANSPRUCH:
- Mix aus aktuellen Designtrends: Swiss Design, Brutalismus, Editorial, Duoton, Gradients
- Mutige Typografie: grosszuegige Schriftgroessen, klare Kontraste, aber keine unlesbaren Ueberlappungen
- Farben: kühn, unerwartet, harmonisch — keine langweiligen Standardpaletten
- Negativraum gezielt einsetzen, nicht alles vollstopfen
- Moderne grafische Elemente: geometrische Formen, Linien, Farbflächen, Verläufe
- Bei Events: thematische Stimmung einfangen (Sommerfest ≠ Weinverkostung)
- Bei Produkten: das Produkt heroisch inszenieren, nicht nur abbilden
- Ergebnis soll wie ein professioneller Handelsflyer wirken: sauber gerastert, hochwertig, mit klaren Komponenten fuer Bild, Preis, Headline und Termin.

REGELN:
- EDEKA Blau (#004C96) und Gelb (#FFD600) MÜSSEN in jeder Palette vorkommen
- Ergänze sie mit 1-2 thematischen Akzentfarben (z.B. Koralle, Mint, Terrakotta, Violett)
- Der Waschbär darf subtil oder prominent eingebunden werden — nie Kindermalbuch-Stil
- Textbereiche klar definieren, Hierarchie beachten
- Kompositionen konkret beschreiben (nicht "schönes Layout", sondern "Produkt links im Spot, Headline rechts in fetter Serifen-Schrift, Preis als kreisförmiges Siegel unten rechts")

Antworte NUR mit JSON:
{
  "enrichment": {
    "campaign_type": "fresh_product_offer | daily_special | seasonal_campaign | brand_story | event",
    "product_family": "fruta | verdura | panaderia | lacteos | carnes | pescados | bebidas | limpieza | hogar | event | otros",
    "seasonality": "spring_summer | autumn_winter | all_year | holiday_specific",
    "communication_style": "close_and_fresh | elegant_restrained | bold_direct | warm_community",
    "price_priority": "high | medium | low",
    "visual_energy": "low | medium_low | medium | medium_high | high",
    "brand_mode": "muehlenbein_local | edeka_standard | waschbaer_featured",
    "waschbaer_presence": "none | subtle | graphic_accent | featured"
  },
  "directions": [
    {
      "name": "Name der Designrichtung (DEUTSCH, z.B. 'Sommerfrische')",
      "intent": "2-3 Sätze: visuelle Stimmung, Gefühl, was der Betrachter in 0.5s erfasst",
      "composition": "2-3 Sätze: konkrete Anordnung — wo steht Produkt/Headline/Preis, welche grafischen Elemente, wie fliesst der Blick",
      "palette": ["#004C96", "#FFD600", "#HEXAKZENT1", "#HEXAKZENT2"],
      "text_safe_area": "top_left | top_right | bottom_left | bottom_right | center",
      "boldness": "low | medium | high",
      "waschbaer_presence": "none | subtle | graphic_accent | featured"
    }
  ]
}

Erzeuge GENAU 3 Designrichtungen mit unterschiedlichen Stimmungen. Sei kreativ, mutig und professionell."""


VISION_APPEND = """

ZUSÄTZLICH ERHÄLTST DU EIN PRODUKTFOTO. Analysiere es als Designer:
- Dominierende Farben und deren Stimmung (warm/kühl, hell/dunkel, gesättigt/pastell)
- Texturen und Materialien (glänzend/matt, glatt/rau, transparent/opak)
- Form und natürliche Blickrichtung des Produkts
- Welcher Hintergrund das Produkt optimal zur Geltung bringt
- Ob das Produkt von oben, von vorne oder schräg am besten wirkt
Nutze all das für Palette, Komposition und visuelle Energie."""


def _product_family(spec: PromotionSpec) -> str:
    category = (spec.category or "").strip().lower()
    product = spec.product.lower()
    if category:
        return category
    keywords = {
        "fruta": ["erdbeer", "apfel", "banane", "orange", "traube", "himbeer", "heidelbeer", "kirsche", "pfirsich", "mango"],
        "verdura": ["tomate", "gurke", "paprika", "salat", "karotte", "spargel", "brokkoli", "blumenkohl"],
        "panaderia": ["brot", "croissant", "semmel", "brezel", "kuchen"],
        "lacteos": ["milch", "käse", "joghurt", "quark", "butter"],
        "carnes": ["fleisch", "wurst", "schinken", "steak", "huhn", "rind"],
        "pescados": ["fisch", "lachs", "thunfisch", "garnelen"],
        "bebidas": ["wein", "bier", "saft", "wasser", "limonade", "sekt"],
    }
    for family, terms in keywords.items():
        if any(term in product for term in terms):
            return family
    return "event" if spec.campaign_kind.value == "event" else "otros"


def _energy(spec: PromotionSpec) -> str:
    if spec.differentiation_level.value == "alto":
        return "high"
    if spec.differentiation_level.value == "bajo":
        return "medium_low"
    return "medium"


def _style(spec: PromotionSpec) -> str:
    if spec.tone.value == "premium":
        return "elegant_restrained"
    if spec.tone.value == "atrevido":
        return "bold_direct"
    if spec.tone.value == "local":
        return "warm_community"
    return "close_and_fresh"


def build_local_plan(spec: PromotionSpec) -> tuple[EnrichmentSpec, list[CreativeDirection]]:
    family = _product_family(spec)
    energy = _energy(spec)
    is_event = spec.campaign_kind.value == "event"
    event_desc = (spec.event_description or "").lower() if is_event else ""

    enrichment = EnrichmentSpec(
        campaign_type="event" if is_event else ("fresh_product_offer" if family in {"fruta", "verdura"} else "daily_special"),
        product_family="event" if is_event else family,
        seasonality="summer" if "sommer" in event_desc else ("autumn" if "herbst" in event_desc else "all_year"),
        communication_style=_style(spec),
        price_priority="medium" if is_event else "high",
        visual_energy=energy,
        brand_mode="muehlenbein_local",
        waschbaer_presence="subtle" if is_event else "none",
    )

    product = spec.product
    price_area = "top_right" if spec.format.value == "story" else "bottom_right"

    if is_event:
        # Event mood colours based on the description
        if "wein" in event_desc or "abend" in event_desc or "premium" in event_desc:
            mood_palette = ["#003B79", "#FFD600", "#800020", "#D4C5A9"]
            mood_palette2 = ["#003B79", "#FFD600", "#2D1B4E", "#C9A96E"]
        elif "sommer" in event_desc or "grill" in event_desc or "garten" in event_desc:
            mood_palette = ["#003B79", "#FFD600", "#E8612C", "#F4EDE4"]
            mood_palette2 = ["#003B79", "#FFD500", "#2A7F3F", "#FFF6E8"]
        elif "kinder" in event_desc or "familie" in event_desc:
            mood_palette = ["#004C96", "#FFD600", "#E6007E", "#00BFB2"]
            mood_palette2 = ["#004C96", "#FFD600", "#FF6B35", "#7BC8A4"]
        else:
            mood_palette = ["#003B79", "#FFD600", "#FFFFFF", "#E7F0FA"]
            mood_palette2 = ["#003B79", "#FFD600", "#D71920", "#FFF5E6"]

        directions = [
            CreativeDirection(
                name="Marktplatz-Design",
                intent=f"Als Eventplakat mit klarer Botschaft. {product} sofort lesbar, unterstützt von thematischen Grafikelementen.",
                composition=f"Grosser Titel oben, illustrative Farbflächen, Termin als prominenter Balken, EDEKA-Lockup und QR-Code im Footer.",
                palette=mood_palette,
                text_safe_area="center",
                boldness="high",
                waschbaer_presence="subtle",
            ),
            CreativeDirection(
                name="Magazin-Look",
                intent="Editoriale Anmutung mit starkem Foto-Moment und eleganter Typografie.",
                composition="Produktfoto oder Illustration als atmosphärischer Hintergrund, Headline als überlagerte Type, dezente Farbakzente.",
                palette=mood_palette2,
                text_safe_area="bottom_left",
                boldness="medium",
                waschbaer_presence="none",
            ),
            CreativeDirection(
                name="Plakat Pur",
                intent="Die Aktion als kraftvolles Statement. Reduziert auf das Wesentliche mit maximaler Signalwirkung.",
                composition="Zentrale Headline in XXL-Type, Termin und Ort klar darunter, EDEKA-Farben als dominante Flächen.",
                palette=["#003B79", "#FFD600", "#D71920", "#FFFFFF"],
                text_safe_area="center",
                boldness="high" if spec.differentiation_level.value == "alto" else "medium",
                waschbaer_presence="featured",
            ),
        ]
        return enrichment, directions

    directions = [
        CreativeDirection(
            name="Hero Shot",
            intent="Das Produkt als Held der Komposition. Sofortige Wiedererkennung, klare Preisaussage.",
            composition="Produkt gross im Zentrum mit weichem Scheinwerferlicht, Preis als markantes Siegel, kurzer Claim darunter.",
            palette=["#003B79", "#FFD600", "#FFFFFF", "#E7F0FA"],
            text_safe_area=price_area,
            boldness="medium",
            waschbaer_presence="none",
        ),
        CreativeDirection(
            name="Marktfrische",
            intent="Natürliche, vertrauensvolle Anmutung mit lokaler Note und klarer Angebotskommunikation.",
            composition="Produkt auf hellem Hintergrund mit natürlichem Schatten, grosse Headline links, Farbfläche rechts mit Preis.",
            palette=["#0B6E4F", "#FFD600", "#F7FAF7", "#003B79"],
            text_safe_area="bottom_left",
            boldness="medium",
            waschbaer_presence="none",
        ),
        CreativeDirection(
            name="Knallhart",
            intent="Maximale Signalwirkung für den schnellen Blick. Der Preis dominiert, das Produkt unterstützt.",
            composition="Gelbe Preis-Fläche als Eyecatcher über volle Breite, Produkt zentral mit Spot, Claim als Abschlusszeile.",
            palette=["#003B79", "#FFD600", "#D71920", "#FFFFFF"],
            text_safe_area="top_left",
            boldness="high" if spec.differentiation_level.value == "alto" else "medium",
            waschbaer_presence="none",
        ),
    ]
    return enrichment, directions


def _build_user_prompt(spec: PromotionSpec) -> str:
    is_event = spec.campaign_kind.value == "event"
    lines = [
        f"Art: {'Event/Marktaktion' if is_event else 'Produktangebot'}",
        f"Titel/Produkt: {spec.product}",
    ]
    if is_event and spec.event_description:
        lines.append(f"Event-Beschreibung: {spec.event_description}")
        lines.append(f"Termin: {spec.validity}")
        lines.append(f"Format: {spec.format.value}")
        lines.append(f"Tonalität: {spec.tone.value}")
        lines.append(f"Kreativniveau: {spec.differentiation_level.value}")
    else:
        lines += [
            f"Kategorie: {spec.category or 'nicht angegeben'}",
            f"Preis: {spec.price or 'nicht angegeben'}",
            f"Statt-Preis: {spec.old_price or 'nicht angegeben'}",
            f"Aktionszeitraum: {spec.validity}",
            f"Herkunft: {spec.origin or 'nicht angegeben'}",
            f"Claim: {spec.claim or 'nicht angegeben'}",
            f"Format: {spec.format.value}",
            f"Tonalität: {spec.tone.value}",
            f"Kreativniveau: {spec.differentiation_level.value}",
        ]
    return "\n".join(lines)


async def generate_ai_plan(
    ai: AIAdapter, spec: PromotionSpec, image_base64: str | None = None
) -> tuple[EnrichmentSpec, list[CreativeDirection]]:
    system_prompt = SYSTEM_PROMPT
    images: list[str] | None = None

    if image_base64 and ai.supports_vision:
        system_prompt += VISION_APPEND
        images = [image_base64]

    result = await ai.chat_json(
        system_prompt=system_prompt,
        user_prompt=_build_user_prompt(spec),
        temperature=0.55,
        max_tokens=950,
        images=images,
    )
    enrichment = EnrichmentSpec(**result["enrichment"])
    directions = [CreativeDirection(**item) for item in result["directions"][:3]]
    if len(directions) < 3:
        _, fallback = build_local_plan(spec)
        directions = (directions + fallback)[:3]
    return enrichment, directions
