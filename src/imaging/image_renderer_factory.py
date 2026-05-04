"""
Image renderer factory for creating renderer instances by name.
"""
import inspect
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
    
    Filters kwargs to only pass parameters accepted by the renderer's __init__,
    since the merged YAML config may contain keys from other renderers.
    
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
    sig = inspect.signature(renderer_class.__init__)
    valid_params = set(sig.parameters.keys()) - {"self"}
    filtered = {k: v for k, v in kwargs.items() if k in valid_params}
    dropped = set(kwargs.keys()) - valid_params
    if dropped:
        logger.debug(f"Dropped params not accepted by {name}: {dropped}")
    logger.info(f"Creating renderer: {name}")
    return renderer_class(**filtered)


def list_renderers() -> list[str]:
    """List all registered renderer names."""
    return list(RENDERERS.keys())
