"""Shared helpers for cover thumbnail generation."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from labooke_core.extract.base import PathLike

DEFAULT_COVER_SIZE = (320, 480)


def save_webp(image: Image.Image, destination: PathLike) -> Path:
    """Resize ``image`` into a WEBP thumbnail and return its path."""
    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = image.convert("RGB")
    rendered.thumbnail(DEFAULT_COVER_SIZE)
    rendered.save(output, format="WEBP")
    return output


def load_image_bytes(content: bytes) -> Image.Image:
    """Decode image ``content`` into a Pillow image."""
    return Image.open(BytesIO(content))


def write_placeholder_cover(destination: PathLike, label: str) -> Path:
    """Write a simple placeholder cover for text-like formats."""
    image = Image.new("RGB", DEFAULT_COVER_SIZE, color="#e7dcc2")
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 24, 296, 456), outline="#3f3422", width=4)
    draw.text((48, 72), label[:28], fill="#3f3422")
    return save_webp(image, destination)
