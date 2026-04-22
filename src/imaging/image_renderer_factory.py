"""
Image renderer factory for creating renderer instances by name.
"""
from typing import Dict
from src.utils.logger import get_logger

from .image_renderers.plain_image_renderer import PlainImageRenderer
from .image_renderers.figstep_image_renderer import FigstepImageRenderer
from .image_renderers.fc_typography_image_renderer import FCTypographyImageRenderer
from .image_renderers.fc_flowchart_image_renderer import FCFlowchartImageRenderer

logger = get_logger(__name__)

# Registry: renderer name → class
RENDERERS: Dict[str, type] = {
    "plain": PlainImageRenderer,
    "figstep": FigstepImageRenderer,
    "fc_typography": FCTypographyImageRenderer,
    "fc_flowchart": FCFlowchartImageRenderer,
}


def create_renderer(name: str = "figstep", **kwargs):
    """
    Factory function to create a renderer instance by name.
    
    Args:
        name: Renderer name ("plain", "figstep", "fc_typography", "fc_flowchart")
        **kwargs: Renderer-specific parameters
            
    Returns:
        Renderer instance
        
    Raises:
        ValueError: If renderer name not found
    """
    if name not in RENDERERS:
        available = ", ".join(RENDERERS.keys())
        raise ValueError(f"Unknown renderer '{name}'. Available: {available}")
    
    renderer_class = RENDERERS[name]
    logger.info(f"Creating renderer: {name}")
    return renderer_class(**kwargs)


def list_renderers() -> list[str]:
    """List all registered renderer names."""
    return list(RENDERERS.keys())
