"""
FC-Typography image renderer: varied font/contrast rendering.

Inspired by FC-Attack (Zhang et al., EMNLP Findings 2025) which showed 
that font style alone swings ASR from 4% to 28% on Claude-3.5.

This renderer uses the same FigStep-style text layout but varies the 
font family, size, and color/contrast to test OCR clarity's impact on ASR.

FC-Attack tested: Creepster, Fruktur Italic, Pacifico, Shojumaru, 
UnifrakturMaguntia (all from Google Fonts, chosen for low readability).
"""
import os
import textwrap
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from src.imaging.base_image_renderer import BaseImageRenderer
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Default: Pacifico (FC-Attack's best-performing font for Claude-3.5)
DEFAULT_FONT_FAMILY = "Pacifico"
DEFAULT_FONT_SIZE = 40
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 768
DEFAULT_BG_COLOR = "#FFFFFF"
DEFAULT_FG_COLOR = "#333333"
DEFAULT_PADDING = 30
DEFAULT_SPACING = 8
DEFAULT_WRAP_WIDTH = 40

# Google Fonts used in FC-Attack ablation
FC_ATTACK_FONTS = [
    "Pacifico",          # Cursive handwriting style
    "Creepster",         # Horror/distorted style
    "Shojumaru",         # Japanese calligraphy-inspired
    "UnifrakturMaguntia",  # Blackletter/Fraktur
]


class FCTypographyImageRenderer(BaseImageRenderer):
    """
    FC-Attack-inspired typography renderer with varied fonts/contrast.
    
    Uses decorative / low-readability fonts that FC-Attack showed 
    significantly affect ASR. The text layout follows FigStep-style 
    (text on white, word-wrapped), but with fonts chosen to reduce 
    OCR clarity.
    
    Attributes:
        font_family: Name of the font (searched on system)
        font_size: Font size in points
        width: Image width in pixels
        height: Image height in pixels  
        bg_color: Background color (can lower contrast)
        fg_color: Text color (can lower contrast)
        padding: Padding around text
        spacing: Line spacing
        wrap_width: Character count for textwrap
        font_path: Explicit path to .ttf file (overrides font_family search)
    """
    
    def __init__(
        self,
        font_family: str = DEFAULT_FONT_FAMILY,
        font_size: int = DEFAULT_FONT_SIZE,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        bg_color: str = DEFAULT_BG_COLOR,
        fg_color: str = DEFAULT_FG_COLOR,
        padding: int = DEFAULT_PADDING,
        spacing: int = DEFAULT_SPACING,
        wrap_width: int = DEFAULT_WRAP_WIDTH,
        font_path: Optional[str] = None,
        # Degradation params (passed to base)
        blur_radius: float = 0,
        jpeg_quality: int = 100,
        noise_std: float = 0,
    ):
        super().__init__(blur_radius=blur_radius, jpeg_quality=jpeg_quality, noise_std=noise_std)
        self.font_family = font_family
        self.font_size = font_size
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.padding = padding
        self.spacing = spacing
        self.wrap_width = wrap_width
        
        # Load font
        self.font = self._load_font(font_family, font_size, font_path)
    
    def _load_font(self, family: str, size: int, explicit_path: Optional[str]) -> ImageFont.FreeTypeFont:
        """Try to load the specified font, with fallback chain."""
        if explicit_path and os.path.exists(explicit_path):
            logger.info(f"Loading font from path: {explicit_path}")
            return ImageFont.truetype(explicit_path, size)
        
        # Try various common locations and extensions
        candidates = [
            f"{family}.ttf",
            f"{family}-Regular.ttf",
            f"{family}-regular.ttf",
            f"fonts/{family}.ttf",
            f"fonts/{family}-Regular.ttf",
        ]
        
        for candidate in candidates:
            try:
                font = ImageFont.truetype(candidate, size)
                logger.info(f"Loaded font: {candidate}")
                return font
            except (OSError, IOError):
                continue
        
        logger.warning(f"Font '{family}' not found, falling back to default")
        try:
            return ImageFont.truetype("Arial.ttf", size)
        except (OSError, IOError):
            return ImageFont.load_default()
    
    def _render_clean(self, text: str) -> Image.Image:
        """Render text with typography variation."""
        wrapped = textwrap.fill(text, width=self.wrap_width)
        
        im = Image.new("RGB", (self.width, self.height), self.bg_color)
        dr = ImageDraw.Draw(im)
        dr.text(
            (self.padding, self.padding),
            wrapped,
            fill=self.fg_color,
            font=self.font,
            spacing=self.spacing,
        )
        
        return im
    
    def get_config(self) -> dict:
        """Return renderer config for saving alongside output."""
        config = {
            "renderer_type": "fc_typography",
            "font_family": self.font_family,
            "font_size": self.font_size,
            "width": self.width,
            "height": self.height,
            "bg_color": self.bg_color,
            "fg_color": self.fg_color,
            "padding": self.padding,
            "spacing": self.spacing,
            "wrap_width": self.wrap_width,
        }
        degradation = self.get_degradation_config()
        if degradation:
            config["degradation"] = degradation
        return config
