"""
Image rendering model backends.

Houses model loading, inference, and lifecycle management for
AI-based image renderers (e.g., diffusion, handwriting generation).

Renderers in image_renderers/ call into these models rather than
managing model loading themselves.

Example future structure:
    image_render_models/
    ├── __init__.py
    ├── handwriting_model.py     # IAM handwriting synthesis
    ├── diffusion_model.py       # Stable Diffusion text-to-image
    └── typography_optimizer.py  # Adversarial font/layout search
"""
