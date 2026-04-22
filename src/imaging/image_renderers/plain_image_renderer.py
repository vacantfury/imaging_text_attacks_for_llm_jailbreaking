"""
Plain image renderer: renders text directly onto a clean image.

The simplest possible text-to-image renderer with no prompt engineering,
no numbered steps, no special formatting. This is the purest baseline
for isolating the modality effect (text vs. image-rendered text).

Uses sensible typographic defaults for maximum readability:
  - Sans-serif font (Arial/DejaVuSans) at readable size
  - Black text on white background
  - Automatic word wrapping within padded area
"""
import os
import textwrap
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from src.imaging.base_image_renderer import BaseImageRenderer
from src.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_FONT_SIZE = 28
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 768
DEFAULT_BG_COLOR = "#FFFFFF"
DEFAULT_FG_COLOR = "#000000"
DEFAULT_PADDING = 40
DEFAULT_LINE_SPACING = 8


class PlainImageRenderer(BaseImageRenderer):
    """
    Plain text-on-image renderer — the simplest baseline.
    
    Renders the full prompt text onto a white image with automatic
    word wrapping. No numbered steps, no prompt tricks, no special
    formatting. Used as the clean baseline for encoding × modality
    experiments where we want to measure the pure modality gap.
    
    Attributes:
        font_size: Font size in points
        width: Image width in pixels
        height: Image height in pixels
        bg_color: Background color
        fg_color: Text color
        padding: Padding around text area
        line_spacing: Extra spacing between lines
        font_path: Optional explicit path to .ttf file
    """
    
    def __init__(
        self,
        font_size: int = DEFAULT_FONT_SIZE,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        bg_color: str = DEFAULT_BG_COLOR,
        fg_color: str = DEFAULT_FG_COLOR,
        padding: int = DEFAULT_PADDING,
        line_spacing: int = DEFAULT_LINE_SPACING,
        font_path: Optional[str] = None,
        # Degradation params (passed to base)
        blur_radius: float = 0,
        jpeg_quality: int = 100,
        noise_std: float = 0,
    ):
        super().__init__(blur_radius=blur_radius, jpeg_quality=jpeg_quality, noise_std=noise_std)
        self.font_size = font_size
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.padding = padding
        self.line_spacing = line_spacing
        
        # Load a clean, readable font
        self.font = self._load_font(font_size, font_path)
        
        # Estimate wrap width based on font metrics
        self._wrap_width = self._estimate_wrap_width()
    
    def _load_font(self, size: int, explicit_path: Optional[str]) -> ImageFont.FreeTypeFont:
        """Load a readable sans-serif font."""
        if explicit_path and os.path.exists(explicit_path):
            return ImageFont.truetype(explicit_path, size)
        
        # Try common readable fonts in priority order
        for candidate in ["Arial.ttf", "DejaVuSans.ttf", "Helvetica.ttf", "FreeSans.ttf"]:
            try:
                font = ImageFont.truetype(candidate, size)
                logger.debug(f"Loaded font: {candidate}")
                return font
            except (OSError, IOError):
                continue
        
        logger.warning("No preferred font found, using Pillow default")
        return ImageFont.load_default()
    
    def _estimate_wrap_width(self) -> int:
        """Estimate character wrap width based on font and available space."""
        available = self.width - 2 * self.padding
        # Measure average character width
        try:
            avg_char_w = self.font.getlength("x")
        except AttributeError:
            avg_char_w = self.font_size * 0.6  # fallback estimate
        
        if avg_char_w > 0:
            return max(10, int(available / avg_char_w))
        return 60  # safe default
    
    def _render_clean(self, text: str) -> Image.Image:
        """Render text directly onto a clean white image."""
        wrapped = textwrap.fill(text, width=self._wrap_width)
        
        im = Image.new("RGB", (self.width, self.height), self.bg_color)
        dr = ImageDraw.Draw(im)
        dr.text(
            (self.padding, self.padding),
            wrapped,
            fill=self.fg_color,
            font=self.font,
            spacing=self.line_spacing,
        )
        
        return im
    
    def get_config(self) -> dict:
        """Return renderer config for saving alongside output."""
        config = {
            "renderer_type": "plain",
            "font_size": self.font_size,
            "width": self.width,
            "height": self.height,
            "bg_color": self.bg_color,
            "fg_color": self.fg_color,
            "padding": self.padding,
            "line_spacing": self.line_spacing,
            "wrap_width": self._wrap_width,
        }
        degradation = self.get_degradation_config()
        if degradation:
            config["degradation"] = degradation
        return config
