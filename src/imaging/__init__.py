"""
Imaging module: text → image rendering for multimodal jailbreak experiments.

Usage:
    from src.imaging import create_renderer

    renderer = create_renderer("figstep")
    renderer.render_to_file("Hello world", "output.png")
    
    # With degradation
    renderer = create_renderer("figstep", blur_radius=2, jpeg_quality=50)
"""

from .base_image_renderer import BaseImageRenderer
from .image_renderer_factory import create_renderer, list_renderers, RENDERERS
from .image_renderers import PlainImageRenderer, FigstepImageRenderer, FCTypographyImageRenderer, FCFlowchartImageRenderer

# Backward compat alias
ImageRenderer = PlainImageRenderer

__all__ = [
    'BaseImageRenderer',
    'PlainImageRenderer',
    'FigstepImageRenderer',
    'FCTypographyImageRenderer',
    'FCFlowchartImageRenderer',
    'ImageRenderer',
    'create_renderer',
    'list_renderers',
    'RENDERERS',
]
