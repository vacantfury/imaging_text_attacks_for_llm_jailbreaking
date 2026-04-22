"""
FigStep image renderer: typographic text-in-image rendering.

Replicates the rendering approach from FigStep (Gong et al., AAAI 2025):
- FreeMonoBold font at 80pt
- 760×760 white canvas
- textwrap at 15 chars/line
- Numbered step suffixes ("1. \n2. \n3. ")

Reference: other_repos/FigStep/src/generate_prompts.py
"""
import os
import textwrap
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from src.imaging.base_image_renderer import BaseImageRenderer
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Defaults matching FigStep's original code
DEFAULT_FONT_SIZE = 80
DEFAULT_WIDTH = 760
DEFAULT_HEIGHT = 760
DEFAULT_BG_COLOR = "#FFFFFF"
DEFAULT_FG_COLOR = "#000000"
DEFAULT_X = 20
DEFAULT_Y = 10
DEFAULT_SPACING = 11
DEFAULT_WRAP_WIDTH = 15
DEFAULT_NUM_STEPS = 3


class FigstepImageRenderer(BaseImageRenderer):
    """
    FigStep-style renderer: text on clean white background.
    
    Faithfully replicates the typographic rendering from FigStep
    (Gong et al., AAAI 2025). The original code uses:
      - FreeMonoBold.ttf at 80pt
      - 760×760 white canvas
      - textwrap.fill(width=15) for line wrapping
      - Numbered step suffixes appended to prompts
    
    Attributes:
        font_size: Font size in points (default: 80, matching original)
        width: Image width in pixels (default: 760)
        height: Image height in pixels (default: 760)
        bg_color: Background color (default: white)
        fg_color: Text color (default: black)
        text_x: X offset for text starting position
        text_y: Y offset for text starting position
        spacing: Line spacing in pixels
        wrap_width: Character count for textwrap
        num_steps: Number of empty numbered steps to append (0 to disable)
        font_path: Optional path to .ttf font file
    """
    
    def __init__(
        self,
        font_size: int = DEFAULT_FONT_SIZE,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        bg_color: str = DEFAULT_BG_COLOR,
        fg_color: str = DEFAULT_FG_COLOR,
        text_x: int = DEFAULT_X,
        text_y: int = DEFAULT_Y,
        spacing: int = DEFAULT_SPACING,
        wrap_width: int = DEFAULT_WRAP_WIDTH,
        num_steps: int = DEFAULT_NUM_STEPS,
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
        self.text_x = text_x
        self.text_y = text_y
        self.spacing = spacing
        self.wrap_width = wrap_width
        self.num_steps = num_steps
        
        # Load font — FigStep uses FreeMonoBold
        if font_path and os.path.exists(font_path):
            self.font = ImageFont.truetype(font_path, font_size)
        else:
            for candidate in ["FreeMonoBold.ttf", "FreeMono.ttf", "DejaVuSansMono-Bold.ttf", "Courier New Bold.ttf"]:
                try:
                    self.font = ImageFont.truetype(candidate, font_size)
                    logger.debug(f"Loaded font: {candidate}")
                    break
                except (OSError, IOError):
                    continue
            else:
                logger.warning("FreeMonoBold not found, falling back to default monospace")
                try:
                    self.font = ImageFont.truetype("DejaVuSansMono.ttf", font_size)
                except (OSError, IOError):
                    self.font = ImageFont.load_default()
    
    def _format_text(self, text: str) -> str:
        """
        Format text following FigStep's approach:
        1. Strip trailing newline
        2. Wrap text at wrap_width characters
        3. Append numbered empty steps
        """
        text = text.removesuffix("\n")
        text = textwrap.fill(text, width=self.wrap_width)
        
        if self.num_steps > 0:
            for idx in range(1, self.num_steps + 1):
                text += f"\n{idx}. "
        
        return text
    
    def _render_clean(self, text: str) -> Image.Image:
        """Render text onto a clean white image, matching FigStep's text_to_image()."""
        formatted = self._format_text(text)
        
        # Match FigStep: fixed canvas size, draw text at (text_x, text_y)
        im = Image.new("RGB", (self.width, self.height), self.bg_color)
        dr = ImageDraw.Draw(im)
        dr.text(
            (self.text_x, self.text_y),
            formatted,
            fill=self.fg_color,
            font=self.font,
            spacing=self.spacing,
        )
        
        return im
    
    def get_config(self) -> dict:
        """Return renderer config for saving alongside output."""
        config = {
            "renderer_type": "figstep",
            "font_size": self.font_size,
            "width": self.width,
            "height": self.height,
            "bg_color": self.bg_color,
            "fg_color": self.fg_color,
            "text_x": self.text_x,
            "text_y": self.text_y,
            "spacing": self.spacing,
            "wrap_width": self.wrap_width,
            "num_steps": self.num_steps,
        }
        degradation = self.get_degradation_config()
        if degradation:
            config["degradation"] = degradation
        return config
