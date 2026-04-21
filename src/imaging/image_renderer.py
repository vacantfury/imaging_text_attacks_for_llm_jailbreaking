"""
Image renderer: converts text prompts to images using Pillow.

Used for the image modality condition in the Encoding × Modality experiment.
Renders text onto a clean background and saves as PNG or returns as base64.
"""
import base64
import os
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Defaults — can be overridden via config.yaml
DEFAULT_FONT_SIZE = 16
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 768
DEFAULT_BG_COLOR = "white"
DEFAULT_FG_COLOR = "black"
DEFAULT_PADDING = 40


class ImageRenderer:
    """
    Renders text onto images for multimodal LLM input.
    
    Attributes:
        font_size: Font size in points
        width: Image width in pixels
        height: Image height in pixels
        bg_color: Background color
        fg_color: Text color
        padding: Padding around text in pixels
        font_path: Optional path to .ttf font file
    """
    
    def __init__(
        self,
        font_size: int = DEFAULT_FONT_SIZE,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        bg_color: str = DEFAULT_BG_COLOR,
        fg_color: str = DEFAULT_FG_COLOR,
        padding: int = DEFAULT_PADDING,
        font_path: Optional[str] = None,
    ):
        self.font_size = font_size
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.padding = padding
        
        # Load font
        if font_path and os.path.exists(font_path):
            self.font = ImageFont.truetype(font_path, font_size)
        else:
            try:
                # Try common system fonts
                self.font = ImageFont.truetype("Arial.ttf", font_size)
            except (OSError, IOError):
                logger.warning("Custom font not found, using Pillow default")
                self.font = ImageFont.load_default()
    
    def render(self, text: str) -> Image.Image:
        """
        Render text onto an image.
        
        Args:
            text: The text to render
            
        Returns:
            PIL Image object
        """
        img = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Calculate text area
        max_width = self.width - 2 * self.padding
        
        # Word-wrap text
        lines = self._wrap_text(draw, text, max_width)
        
        # Draw lines
        y = self.padding
        for line in lines:
            draw.text((self.padding, y), line, fill=self.fg_color, font=self.font)
            bbox = self.font.getbbox(line)
            line_height = bbox[3] - bbox[1] + 4  # small line spacing
            y += line_height
            if y > self.height - self.padding:
                break  # Don't overflow
        
        return img
    
    def render_to_file(self, text: str, output_path: str) -> str:
        """
        Render text and save to PNG file.
        
        Args:
            text: The text to render
            output_path: Path to save the PNG
            
        Returns:
            Absolute path to saved file
        """
        img = self.render(text)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
        logger.debug(f"Saved image: {output_path}")
        return os.path.abspath(output_path)
    
    def render_to_base64(self, text: str) -> str:
        """
        Render text and return as base64-encoded PNG string.
        
        Args:
            text: The text to render
            
        Returns:
            Base64-encoded PNG string
        """
        img = self.render(text)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    def _wrap_text(self, draw: ImageDraw.Draw, text: str, max_width: int) -> list[str]:
        """Word-wrap text to fit within max_width pixels."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = self.font.getbbox(test_line)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines
    
    def get_config(self) -> dict:
        """Return renderer config for saving alongside output."""
        return {
            "font_size": self.font_size,
            "width": self.width,
            "height": self.height,
            "bg_color": self.bg_color,
            "fg_color": self.fg_color,
            "padding": self.padding,
        }
