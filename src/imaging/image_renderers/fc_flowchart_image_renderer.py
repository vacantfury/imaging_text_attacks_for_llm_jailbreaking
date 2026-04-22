"""
FC-Flowchart image renderer: Graphviz-based flowchart rendering.

Replicates the rendering approach from FC-Attack (Zhang et al., EMNLP Findings 2025).
Generates Graphviz DOT flowcharts with:
  - Goal node (ellipse) containing the prompt
  - Step nodes (boxes) — we don't decompose into steps (no fine-tuned generator),
    so the full prompt text is rendered in the goal node.
  - Layouts: vertical (TB), horizontal (LR), tortuous (S-shaped)
  - dpi=600 for high resolution

FC-Attack uses a fine-tuned step-description generator to split harmful queries 
into numbered steps. Since our experiment tests rendering (not decomposition), 
we render the FULL prompt text in the goal node. This isolates the rendering 
variable from the decomposition confound.

Requires: graphviz Python package and Graphviz system binary.
  pip install graphviz
  brew install graphviz  (macOS) / apt install graphviz (Linux)
"""
import os
import textwrap
from io import BytesIO
from typing import Optional

from PIL import Image

from src.imaging.base_image_renderer import BaseImageRenderer
from src.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_DPI = 600
DEFAULT_LAYOUT = "vertical"  # vertical | horizontal | tortuous


class FCFlowchartImageRenderer(BaseImageRenderer):
    """
    FC-Attack-style flowchart renderer using Graphviz.
    
    Renders text inside a Graphviz directed graph with:
    - Goal node (ellipse) containing the full prompt
    - Optional numbered step nodes (box) if steps are provided
    - Configurable layout direction
    
    Attributes:
        layout: Flowchart layout — "vertical" (TB), "horizontal" (LR), "tortuous" (S-shaped)
        dpi: Dots per inch for rendering (default: 600, matching FC-Attack)
        wrap_width: Character count for text wrapping inside nodes
        font_name: Graphviz font name
        font_size: Graphviz font size string
    """
    
    def __init__(
        self,
        layout: str = DEFAULT_LAYOUT,
        dpi: int = DEFAULT_DPI,
        wrap_width: int = 30,
        font_name: str = "Times-Roman",
        font_size: str = "14",
        # Degradation params (passed to base)
        blur_radius: float = 0,
        jpeg_quality: int = 100,
        noise_std: float = 0,
    ):
        super().__init__(blur_radius=blur_radius, jpeg_quality=jpeg_quality, noise_std=noise_std)
        self.layout = layout
        self.dpi = dpi
        self.wrap_width = wrap_width
        self.font_name = font_name
        self.font_size = font_size
        
        # Verify graphviz is available
        try:
            import graphviz
            self._graphviz = graphviz
        except ImportError:
            raise ImportError(
                "FC-Flowchart renderer requires 'graphviz' package. "
                "Install with: pip install graphviz && brew install graphviz"
            )
    
    def _wrap_node_text(self, text: str) -> str:
        """Wrap text for Graphviz node labels (newline-separated)."""
        return textwrap.fill(text, width=self.wrap_width).replace("\n", "\\n")
    
    def _build_vertical(self, text: str) -> "graphviz.Digraph":
        """Build vertical (top-to-bottom) flowchart — FC-Attack's default."""
        dot = self._graphviz.Digraph()
        dot.attr(dpi=str(self.dpi))
        
        wrapped = self._wrap_node_text(text)
        dot.node("goal", wrapped, shape="ellipse")
        
        return dot
    
    def _build_horizontal(self, text: str) -> "graphviz.Digraph":
        """Build horizontal (left-to-right) flowchart."""
        dot = self._graphviz.Digraph()
        dot.attr(dpi=str(self.dpi), rankdir="LR")
        
        wrapped = self._wrap_node_text(text)
        dot.node("goal", wrapped, shape="ellipse")
        
        return dot
    
    def _build_tortuous(self, text: str) -> "graphviz.Digraph":
        """Build S-shaped (tortuous) flowchart — FC-Attack's zigzag layout."""
        dot = self._graphviz.Digraph()
        dot.attr(dpi=str(self.dpi), rankdir="TB")
        
        # Split text into chunks and lay out in zigzag rows
        words = text.split()
        chunk_size = max(1, len(words) // 3)
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i + chunk_size]))
        
        # Create nodes in rows of ~3, alternating direction
        prev_node = None
        for i, chunk in enumerate(chunks[:6]):  # Max 6 chunks
            node_id = f"step_{i}"
            wrapped = self._wrap_node_text(chunk)
            shape = "ellipse" if i == 0 else "box"
            dot.node(node_id, wrapped, shape=shape, style="filled", fillcolor="white")
            if prev_node:
                dot.edge(prev_node, node_id)
            prev_node = node_id
        
        return dot
    
    def _render_clean(self, text: str) -> Image.Image:
        """Render text as a Graphviz flowchart."""
        builders = {
            "vertical": self._build_vertical,
            "horizontal": self._build_horizontal,
            "tortuous": self._build_tortuous,
        }
        
        if self.layout not in builders:
            raise ValueError(f"Unknown layout '{self.layout}'. Options: {list(builders.keys())}")
        
        dot = builders[self.layout](text)
        
        # Set global font
        dot.attr("node", fontname=self.font_name, fontsize=self.font_size)
        
        # Render to PNG bytes
        png_bytes = dot.pipe(format="png")
        img = Image.open(BytesIO(png_bytes)).convert("RGB")
        
        return img
    
    def get_config(self) -> dict:
        """Return renderer config for saving alongside output."""
        config = {
            "renderer_type": "fc_flowchart",
            "layout": self.layout,
            "dpi": self.dpi,
            "wrap_width": self.wrap_width,
            "font_name": self.font_name,
            "font_size": self.font_size,
        }
        degradation = self.get_degradation_config()
        if degradation:
            config["degradation"] = degradation
        return config
