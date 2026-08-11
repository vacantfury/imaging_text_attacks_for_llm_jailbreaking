"""
GuardRouter — the channel-routed guard panel (AS-7 review 3, con 5).

WHY THIS EXISTS. The paper measures that a text-only guard's image-channel
decision is a CONSTANT (0/100 blocks on harmful image inputs and 0/100 on benign
ones alike), that a multimodal guard closes that hole, and that the multimodal
guard is nonetheless the WORSE choice on adversarially-hard benign text, where
the best-calibrated text guard beats it by a wide margin. From those two facts
the paper recommends a channel-routed panel rather than a substitution -- and
then never builds it. Review 3, con 5: *"the channel-routed panel proposed after
Table 4 is explicitly not built or evaluated end to end ... not a minor omission
because the proposed router is the paper's primary constructive deployment
recommendation."* This module is that panel.

MECHANISM, per prompt (not per cell -- the routing decision is per input):
  1. Does THIS prompt carry an image?
       yes -> classify with `image_guard` (a multimodal guard, image + text)
       no  -> classify with `text_guard`  (the better-calibrated text guard)
  2. UNSAFE -> return GUARD_REFUSAL_TEXT, no target call.
     SAFE   -> query the TARGET with the ORIGINAL input, unchanged.

The router therefore adds NO new capability: it only chooses which already-
measured classifier decides. That is the point. If the paper's account is right,
the panel should inherit the multimodal guard's image-channel coverage AND the
text guard's benign calibration, and its cells should be predictable from the
single-guard cells already collected. If it does not, the recommendation is
wrong and we would rather find that ourselves.

DELIBERATELY NOT DONE HERE. No guard-disagreement logic, no confidence
thresholds, no voting: routing is on modality alone, because modality is the
variable the paper measured. A panel that also arbitrates disagreements is a
different (and unmeasured) object.

`query_source` is accepted and forwarded so the router can be run under both
protocols, exactly like `guard_baseline`. Default "encoded" (deployable).
"""
from pathlib import Path
from typing import Optional

from src.experiment.schemas import Prompt
from llm_utils.base_llm_service import BaseLLMService
from llm_utils.llm_model import LLMModel
from llm_utils.llm_service_factory import LLMServiceFactory
from src.utils.logger import get_logger
from .base import Defense, build_conversation_message
from .defender_factory import register_defense
from .guard_utils import GUARD_REFUSAL_TEXT, TEXT_ONLY_GUARDS, query_guard

logger = get_logger(__name__)


@register_defense
class GuardRouter(Defense):
    """Route each prompt to a text or multimodal guard by image presence."""

    type_name = "guard_router"

    # Both guards are cluster-served and neither sits under the historical
    # `guard_model` key discovery scans, so without this declaration the
    # orchestrator starts no server for either and every task dies with
    # "No vLLM server was ever started for meta-llama/Llama-Guard-3-8B"
    # (observed, job 9066378, 2026-08-10).
    MODEL_CONFIG_KEYS = ("text_guard", "image_guard")

    def __init__(self, text_guard: str, image_guard: str, **kwargs):
        """
        Args:
            text_guard: guard for prompts with NO image (chosen for benign
                calibration).
            image_guard: guard for prompts WITH an image; must not be a
                text-only guard, or the router would rebuild the very blind
                spot it exists to remove -- checked at construction.
        """
        super().__init__(text_guard=text_guard, image_guard=image_guard, **kwargs)
        self._text_name, self._image_name = text_guard, image_guard
        # Resolve now so a typo fails before any cluster job is submitted.
        self._text_model = LLMModel.from_string(text_guard)
        self._image_model = LLMModel.from_string(image_guard)
        if self._image_model in TEXT_ONLY_GUARDS:
            raise ValueError(
                f"image_guard={image_guard!r} is a TEXT-ONLY guard. Routing "
                "image-bearing prompts to it reproduces the blind spot this "
                "defense exists to close; pick a multimodal guard.")
        self._services: dict[str, BaseLLMService] = {}

    def _service(self, name: str) -> BaseLLMService:
        if name not in self._services:
            self._services[name] = LLMServiceFactory.create(name)
        return self._services[name]

    def query(
        self,
        prompts: list[Prompt],
        target_service: BaseLLMService,
        is_multimodal: bool,
        source_dir: Optional[Path] = None,
        system_message: Optional[str] = None,
    ) -> list[tuple[str, str]]:
        query_source = self._config.get("query_source", "encoded")
        if query_source not in ("original", "encoded"):
            raise ValueError(
                f"unknown guard_router query_source {query_source!r} "
                "(expected 'original' or 'encoded')")

        text_items: list[tuple[str, str, object]] = []
        image_items: list[tuple[str, str, object]] = []
        for p in prompts:
            messages = build_conversation_message(p, is_multimodal, source_dir)
            text_side, image_side = messages[0]
            if query_source == "original":
                # Granted arm: the unencoded request is pure text and has no
                # image channel, so it routes to the text guard by the router's
                # own rule -- the grant erases the routing decision. Recorded
                # explicitly rather than left implicit, since it means the
                # granted arm does NOT exercise the panel.
                text_items.append((p.id, p.original or p.encoded or "", None))
            elif image_side is not None:
                image_items.append((p.id, text_side or "", image_side))
            else:
                text_items.append((p.id, p.encoded or text_side or "", None))

        logger.info(
            f"GuardRouter: routed {len(image_items)} image-bearing -> "
            f"{self._image_name}, {len(text_items)} text-only -> "
            f"{self._text_name} (query_source={query_source})")

        verdicts: dict[str, bool] = {}
        for name, model, items in (
            (self._text_name, self._text_model, text_items),
            (self._image_name, self._image_model, image_items),
        ):
            if items:
                verdicts.update(
                    query_guard(self._service(name), model, items, is_test=True))

        # Fail-closed, same contract as guard_baseline: a prompt with no verdict
        # is treated as unsafe and never forwarded to the target.
        target_convs: list[tuple[str, list]] = []
        for p in prompts:
            if not verdicts.get(p.id, True):
                target_convs.append(
                    (p.id, build_conversation_message(p, is_multimodal, source_dir)))

        logger.info(
            f"GuardRouter: {len(target_convs)}/{len(prompts)} passed -> target")
        target_results: dict[str, str] = {}
        if target_convs:
            target_results = dict(target_service.batch_chat(
                conversations=target_convs,
                system_message=system_message,
                is_test=True,
            ))

        return [
            (p.id, target_results.get(p.id, GUARD_REFUSAL_TEXT))
            for p in prompts
        ]

    def get_usage(self) -> Optional[dict]:
        """Usage per guard, kept separate so the panel's cost can be attributed
        to the arm that incurred it. The target's usage is tracked by
        target_service, not re-counted here."""
        if not self._services:
            return None
        return {name: svc.get_usage() for name, svc in self._services.items()}
