from pathlib import Path
from PIL import Image
from app.schemas.promotion import FormatType, EXPORT_FORMATS
from app.config import settings


def export_promotion(
    source_path: Path,
    format_type: FormatType,
    output_dir: Path | None = None,
) -> Path:
    fmt = EXPORT_FORMATS[format_type]
    out_dir = output_dir or settings.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    img = Image.open(source_path)
    img_resized = img.resize((fmt.width, fmt.height), Image.Resampling.LANCZOS)

    filename = f"{source_path.stem}_{format_type.value}.png"
    output_path = out_dir / filename
    img_resized.save(str(output_path), quality=95)
    return output_path


def export_all_formats(
    source_path: Path,
    formats: list[FormatType] | None = None,
    output_dir: Path | None = None,
) -> dict[FormatType, Path]:
    if formats is None:
        formats = list(FormatType)

    results = {}
    for fmt in formats:
        results[fmt] = export_promotion(source_path, fmt, output_dir)
    return results
