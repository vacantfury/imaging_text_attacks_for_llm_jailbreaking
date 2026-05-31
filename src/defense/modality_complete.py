"""
ModalityComplete — the minimal coverage-complete black-box defense (Paper C).

Motivation (Paper C, RQ-C): SAGE-as-system covers only the text channel, and
ECSO branches on `has_image`; an attacker who places the payload in the
modality a defense doesn't cover defeats it. The minimal fix is to cover ALL
modalities unconditionally.

Mechanism (built from ECSO's caption + SAGE's discrimination primitives):
  Step 1 — RECOVER (only if multimodal): ask the target VLM to transcribe all
           text in the image verbatim + briefly describe non-text content.
  Step 2 — GUARD (always, eyes-closed / no image): wrap the UNION of the text
           channel + the recovered image content in the SAGE discrimination
           prompt and answer. The model self-discriminates over the full
           recovered content with the stronger text-side safety alignment.

This removes both blind spots at once: the text channel is read directly, and
the image channel is folded into the same text-side safety check. For pure-text
inputs it degrades to SAGE-over-text (which is already coverage-complete there).

Same target VLM for both calls (provider-agnostic via batch_chat), so all usage
is the target's — no separate defense model. Calls/query: 2 multimodal, 1 text.
"""
from pathlib import Path
from typing import Optional

from src.experiment.schemas import Prompt
from src.llm_utils.base_llm_service import BaseLLMService
from src.utils.logger import get_logger
from .base import Defense, build_conversation_message
from .defender_factory import register_defense
from .sage import SAGE_TEMPLATE

logger = get_logger(__name__)


# Maximize recovery: the whole point is to surface image-resident content to
# the text-side safety check, so we ask for a verbatim transcription first.
RECOVER_PROMPT = (
    "Transcribe ALL text that appears in the image, exactly and completely. "
    "Then, in one sentence, describe any non-text visual content. "
    "Output only the transcription followed by the one-sentence description."
)

# How the recovered image content is folded into the text channel before the
# unified safety check sees it.
_UNION_TEMPLATE = (
    "{text_channel}\n\n"
    "[Content recovered from the attached image]:\n{image_content}"
)


@register_defense
class ModalityComplete(Defense):
    """Cover every modality: recover the image into text, then one unified
    SAGE-style safety check over the union of both channels (eyes-closed)."""

    type_name = "modality_complete"

    def query(
        self,
        prompts: list[Prompt],
        target_service: BaseLLMService,
        is_multimodal: bool,
        source_dir: Optional[Path] = None,
        system_message: Optional[str] = None,
    ) -> list[tuple[str, str]]:
        # ---------- Step 1: RECOVER image content (multimodal only) ----------
        recovered_by_id: dict[str, str] = {}
        if is_multimodal:
            recover_convs = []
            for p in prompts:
                img_messages = build_conversation_message(p, True, source_dir)
                _, img = img_messages[0]
                recover_convs.append((p.id, [(RECOVER_PROMPT, img)]))
            logger.info(
                f"ModalityComplete step 1 (RECOVER): {len(recover_convs)} images")
            recover_results = target_service.batch_chat(
                conversations=recover_convs, system_message=None, is_test=True,
            )
            recovered_by_id = dict(recover_results)

        # ---------- Step 2: GUARD over the union, eyes-closed (no image) ----------
        guard_convs: list[tuple[str, list]] = []
        for p in prompts:
            text_channel = p.encoded or ""
            if is_multimodal:
                content = _UNION_TEMPLATE.format(
                    text_channel=text_channel,
                    image_content=recovered_by_id.get(p.id, ""),
                )
            else:
                content = text_channel
            wrapped = SAGE_TEMPLATE.format(content=content)
            guard_convs.append((p.id, [(wrapped, None)]))  # eyes closed

        logger.info(
            f"ModalityComplete step 2 (GUARD): {len(guard_convs)} unified "
            f"safety checks (is_multimodal={is_multimodal})")
        return target_service.batch_chat(
            conversations=guard_convs,
            system_message=system_message,
            is_test=True,
        )
