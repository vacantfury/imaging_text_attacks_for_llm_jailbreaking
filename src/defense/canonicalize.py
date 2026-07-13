"""Canonicalize defense — effective-N reduction against Best-of-N (Paper D).

Best-of-N wins by *budget*: it samples N stochastically-augmented variants of one
request and succeeds if any slips past the guard/model. Ordinary per-input guards
only lower the per-try slip probability p, leaving 1-(1-p)^N -> 1 intact. This
defense instead collapses the attacker's EFFECTIVE N by deterministically
canonicalizing the input before the target sees it, so surface-form variants of
one request map to the SAME (or few) canonical forms — a large sampling budget
then buys few distinct decisions.

It handles the *canonicalizable head* of BoN's text augmentation space
losslessly — random capitalization (case-fold), whitespace, Unicode
homoglyph/compatibility variants (NFKC), and zero-width/control characters. The
*irreducible tail* (word scrambling, ASCII noising) survives here and is left for
spell-correction (future work); characterizing that head-vs-tail carve is exactly
the paper's contribution. Cite Hughes et al. (NEURIPS2025_69f3eb24) for the
attack; the effective-N framing is ours. Scope: text channel only.
"""
import re
import unicodedata
from pathlib import Path
from typing import Optional

from src.experiment.schemas import Prompt
from src.llm_utils.base_llm_service import BaseLLMService
from src.utils.logger import get_logger
from .base import Defense, build_conversation_message
from .defender_factory import register_defense

logger = get_logger(__name__)

# C0 controls (\x00-\x1f), DEL + C1 (\x7f-\x9f), zero-width + bidi marks
# (​-‏) and BOM/ZWNBSP (﻿).
_CTRL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f​-‏﻿]")
_WS_RE = re.compile(r"\s+")


def canonicalize_text(text: str, *, nfkc: bool = True, strip_control: bool = True,
                      case_fold: bool = True, normalize_whitespace: bool = True) -> str:
    """Deterministic surface-form canonicalization (the canonicalizable head)."""
    t = text
    if nfkc:
        t = unicodedata.normalize("NFKC", t)
    if strip_control:
        t = _CTRL_RE.sub("", t)
    if case_fold:
        t = t.casefold()
    if normalize_whitespace:
        t = _WS_RE.sub(" ", t).strip()
    return t


@register_defense
class CanonicalizeDefense(Defense):
    """Canonicalize the input text, then query the target once."""

    type_name = "canonicalize"

    def __init__(self, nfkc: bool = True, strip_control: bool = True,
                 case_fold: bool = True, normalize_whitespace: bool = True, **kwargs):
        super().__init__(nfkc=nfkc, strip_control=strip_control, case_fold=case_fold,
                         normalize_whitespace=normalize_whitespace, **kwargs)
        self.opts = dict(nfkc=nfkc, strip_control=strip_control, case_fold=case_fold,
                         normalize_whitespace=normalize_whitespace)

    def query(
        self,
        prompts: list[Prompt],
        target_service: BaseLLMService,
        is_multimodal: bool,
        source_dir: Optional[Path] = None,
        system_message: Optional[str] = None,
    ) -> list[tuple[str, str]]:
        conversations: list[tuple[str, list]] = []
        for p in prompts:
            canon = p.model_copy(
                update={"encoded": canonicalize_text(p.encoded, **self.opts)})
            messages = build_conversation_message(
                canon, is_multimodal=is_multimodal, source_dir=source_dir)
            conversations.append((p.id, messages))
        logger.info(
            f"CanonicalizeDefense: canonicalized + forwarding {len(conversations)} "
            f"prompts (is_multimodal={is_multimodal})")
        return target_service.batch_chat(
            conversations=conversations, system_message=system_message, is_test=True)
