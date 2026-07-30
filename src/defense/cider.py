"""CIDER — Cross-modality Information DEtectoR (Xu et al., Findings of EMNLP 2024).

A reimplementation of the published black-box consistency detector, added as the
comparison baseline cspaper reviews 15 and 18 both name (review 18 con 7: "Section 2
explicitly acknowledges that CIDER and DefenSee are eligible black-box
consistency-based baselines … then the conclusion should not imply the reported
frontier covers black-box VLM defense generally").

MECHANISM, transcribed from the authors' released code (`other_repos/CIDER`,
`code/defender.py` + `code/utils.py`), not from the paper prose:

  1. Embed the text channel and the image with a shared vision--language encoder.
  2. Denoise the image, recording the embedding at each denoise checkpoint.
  3. Let delta = cos(text, img_denoised) - cos(text, img_original) at each checkpoint.
     Flag the input as adversarial if min(delta) < tau, i.e. if denoising costs
     MORE cross-modal similarity than a clean image would lose.
  4. Flagged -> block (canned refusal). Passed -> the target sees the ORIGINAL input.

So CIDER is a GATE defense in this repo's taxonomy (like `guard_baseline`): it
classifies and blocks, it never transforms the prompt.

TAU IS CALIBRATED, NOT CHOSEN. `defender.py` sets it as a percentile of the
delta distribution measured on CLEAN images:
    self.threshold = np.percentile(decrease, (1 - ratio) * 100)
so tau is a false-positive-rate budget on benign traffic, exactly like our own
guard-threshold sweep. Run this defense once with `threshold: null` over the benign
channel to collect deltas (everything passes, which also gives CIDER's over-refusal
floor for free), then set `threshold` from `paper_c_cider_threshold.py`.

TWO DECLARED DEVIATIONS, both forced and both stated in the paper:

  * DENOISER. The authors' headline results use a guided-diffusion denoiser whose
    ImageNet checkpoint (`256x256_diffusion_uncond.pt`, ~2GB) is NOT shipped in
    their repo; the DnCNN alternative their own `utils.py` implements IS shipped
    (`code/models/DnCNN/checkpoint.pth.tar`). We use their DnCNN weights and their
    DnCNN architecture, vendored below with attribution. Their code notes DnCNN
    "currently only denoise[s] once for each img", so the checkpoint sequence has
    length 1 rather than the diffusion path's seven.
  * ENCODER. Their embeddings come from the target MLLM's own encoder, and their
    primary target is LLaVA-1.5-7B, whose vision tower IS CLIP ViT-L/14-336. We
    call that CLIP checkpoint directly, which reproduces their primary setup
    without loading a VLM in-process purely to read embeddings.

WHAT WE EXPECT, PRE-REGISTERED. CIDER detects *optimization-based pixel
perturbations*: the whole signal is that denoising strips adversarial noise. Our
attacks are clean synthetic renders (typography, flowcharts, low-contrast text,
distraction grids) carrying no perturbation at all, so the denoise-induced
similarity shift should look like a clean image's and CIDER should pass them. If
that holds, con 7 is answered on the merits rather than conceded: the eligible
consistency detector is calibrated for a different threat model and does not reach
representation-shifting renders, so it occupies the low-cost/low-coverage corner of
the same frontier. A surprise in the other direction would be the more interesting
result and would need reporting as such.

SCOPE. CIDER is defined only where an image exists. Five of our eleven attacks are
text-only; on those the detector has no image to denoise and this implementation
passes the prompt through unchanged (logged, and reported as an inapplicability
rather than a pass rate).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.experiment.schemas import Prompt
from llm_utils.base_llm_service import BaseLLMService
from src.utils.logger import get_logger
from .base import Defense, build_conversation_message
from .defender_factory import register_defense
from .guard_utils import GUARD_REFUSAL_TEXT

logger = get_logger(__name__)


# --------------------------------------------------------------------------
# DnCNN, vendored from the CIDER release (code/models/DnCNN/DnCNN.py), which
# itself notes "a modified implementation of the DnCNN from
# https://github.com/cszn/DnCNN". Copied rather than re-derived so the weights
# in their shipped checkpoint load into the architecture they were trained on.
# torch is imported lazily inside the builder: this module is imported by the
# defense factory on every run, including API-only runs with no torch present.
# --------------------------------------------------------------------------
def _build_dncnn(depth: int = 17, n_channels: int = 64, image_channels: int = 3):
    import torch.nn as nn

    class DnCNN(nn.Module):
        def __init__(self):
            super().__init__()
            padding = 1
            kernel_size = 3
            layers = [
                nn.Conv2d(image_channels, n_channels, kernel_size,
                          padding=padding, bias=True),
                nn.ReLU(inplace=True),
            ]
            for _ in range(depth - 2):
                layers += [
                    nn.Conv2d(n_channels, n_channels, kernel_size,
                              padding=padding, bias=False),
                    nn.BatchNorm2d(n_channels, eps=0.0001, momentum=0.95),
                    nn.ReLU(inplace=True),
                ]
            layers.append(nn.Conv2d(n_channels, image_channels, kernel_size,
                                    padding=padding, bias=False))
            self.dncnn = nn.Sequential(*layers)

        def forward(self, x):
            return x - self.dncnn(x)   # residual: predicts the noise

    return DnCNN()


def _load_dncnn(ckpt_path: str, device):
    """Load the authors' shipped checkpoint, tolerating either layout.

    Their loader wraps the net in `torch.nn.DataParallel`, so the saved keys may
    carry a `module.` prefix, and the file may be either a bare state_dict or a
    training checkpoint dict with one under `state_dict`.
    """
    import torch

    net = _build_dncnn()
    raw = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    state = raw
    if isinstance(raw, dict):
        for key in ("state_dict", "model", "net"):
            if key in raw and isinstance(raw[key], dict):
                state = raw[key]
                break
    if hasattr(state, "state_dict"):        # a pickled nn.Module
        state = state.state_dict()
    state = {k.replace("module.", "", 1): v for k, v in state.items()}
    missing, unexpected = net.load_state_dict(state, strict=False)
    if missing or unexpected:
        logger.warning(
            f"CIDER DnCNN load: {len(missing)} missing / {len(unexpected)} "
            f"unexpected keys. First missing: {list(missing)[:3]}")
        if len(missing) > len(list(net.state_dict())) // 2:
            raise RuntimeError(
                f"CIDER DnCNN checkpoint at {ckpt_path} does not match the "
                f"architecture ({len(missing)} keys unfilled) — refusing to run "
                f"a randomly-initialised denoiser, which would silently make "
                f"the baseline meaningless.")
    return net.to(device).eval()


@register_defense
class Cider(Defense):
    """Published cross-modal consistency detector, as a gate defense."""

    type_name = "cider"

    def __init__(self,
                 clip_model: str = "openai/clip-vit-large-patch14-336",
                 dncnn_checkpoint: str = "",
                 threshold: Optional[float] = None,
                 device: str = "cuda",
                 batch_size: int = 16,
                 trace_dir: str = "outputs/autoattack_defense/cider_deltas",
                 **kwargs):
        super().__init__(clip_model=clip_model, dncnn_checkpoint=dncnn_checkpoint,
                         threshold=threshold, device=device,
                         batch_size=batch_size, trace_dir=trace_dir, **kwargs)
        self._clip_name = clip_model
        self._ckpt = dncnn_checkpoint
        self._tau = threshold
        self._device_str = device
        self._batch_size = batch_size
        self._trace_dir = trace_dir
        self._clip = None
        self._processor = None
        self._denoiser = None
        self._device = None

    # ---------------- lazy model construction ----------------
    def _load(self):
        if self._clip is not None:
            return
        import torch
        from transformers import CLIPModel, CLIPProcessor

        self._device = torch.device(
            self._device_str if torch.cuda.is_available() else "cpu")
        if self._device.type == "cpu":
            logger.warning("CIDER: no CUDA visible — running CLIP + DnCNN on CPU, "
                           "which is slow but correct.")
        logger.info(f"CIDER: loading {self._clip_name} on {self._device}")
        self._clip = CLIPModel.from_pretrained(self._clip_name).to(self._device).eval()
        self._processor = CLIPProcessor.from_pretrained(self._clip_name)
        if not self._ckpt:
            raise ValueError(
                "CIDER needs dncnn_checkpoint — the denoiser weights shipped in "
                "the authors' repo at code/models/DnCNN/checkpoint.pth.tar. Set it "
                "in conf/defense/cider.yaml (other_repos/ is gitignored, so the "
                "file must be placed on each cluster).")
        self._denoiser = _load_dncnn(self._ckpt, self._device)

    # ---------------- the detector ----------------
    def _deltas(self, items: list[tuple[str, str, object]]) -> dict[str, float]:
        """min(delta) per prompt id; delta = cos(text,denoised) - cos(text,orig)."""
        import numpy as np
        import torch

        self._load()
        out: dict[str, float] = {}
        for start in range(0, len(items), self._batch_size):
            chunk = items[start:start + self._batch_size]
            ids = [c[0] for c in chunk]
            texts = [c[1] or "" for c in chunk]
            images = [c[2] for c in chunk]
            # The paginating renderer can emit several pages; CIDER scores one
            # image, so take the first page and note it in the trace.
            images = [im[0] if isinstance(im, list) else im for im in images]
            images = [im.convert("RGB") for im in images]

            with torch.no_grad():
                enc = self._processor(text=texts, images=images, return_tensors="pt",
                                      padding=True, truncation=True)
                enc = {k: v.to(self._device) for k, v in enc.items()}
                pixels = enc["pixel_values"]

                # Use the FULL forward, not get_text_features/get_image_features:
                # in transformers 5.x those return a BaseModelOutputWithPooling
                # rather than a tensor. `text_embeds` / `image_embeds` are the
                # PROJECTED embeddings CLIP's own contrastive similarity is defined
                # over, which is the space a cosine similarity should live in, and
                # the field names are stable across 4.x and 5.x.
                out = self._clip(input_ids=enc["input_ids"],
                                 attention_mask=enc["attention_mask"],
                                 pixel_values=pixels)
                t_emb = out.text_embeds
                i_emb = out.image_embeds
                t_emb = t_emb / t_emb.norm(dim=-1, keepdim=True)
                i_emb = i_emb / i_emb.norm(dim=-1, keepdim=True)

                # DnCNN expects [0,1] pixels; CLIP's processor hands us normalised
                # tensors, so denoise in CLIP's own space is wrong. Re-derive the
                # [0,1] tensor from the PIL images at CLIP's input resolution.
                size = pixels.shape[-1]
                raw = torch.stack([
                    torch.from_numpy(
                        np.asarray(im.resize((size, size))).astype("float32") / 255.0
                    ).permute(2, 0, 1)
                    for im in images
                ]).to(self._device)
                den = torch.clamp(self._denoiser(raw), 0, 1)

                # Back into CLIP's normalisation for the denoised embedding.
                mean = torch.tensor(self._processor.image_processor.image_mean,
                                    device=self._device).view(1, 3, 1, 1)
                std = torch.tensor(self._processor.image_processor.image_std,
                                   device=self._device).view(1, 3, 1, 1)
                out_d = self._clip(input_ids=enc["input_ids"],
                                   attention_mask=enc["attention_mask"],
                                   pixel_values=(den - mean) / std)
                d_emb = out_d.image_embeds
                d_emb = d_emb / d_emb.norm(dim=-1, keepdim=True)

                cos_o = (t_emb * i_emb).sum(-1)
                cos_d = (t_emb * d_emb).sum(-1)
                diffs = (cos_d - cos_o).detach().cpu().reshape(-1).tolist()
                if len(diffs) != len(ids):
                    raise RuntimeError(
                        f"CIDER: {len(diffs)} deltas for {len(ids)} inputs — the "
                        f"CLIP batch and the id list disagree, which would "
                        f"mis-attribute every score in this chunk.")
                for pid, delta in zip(ids, diffs):
                    # Keys are forced to str: a prompt id that arrives as a tensor
                    # or numpy scalar silently breaks the JSON trace downstream.
                    out[str(pid)] = float(delta)
        return out

    def query(
        self,
        prompts: list[Prompt],
        target_service: BaseLLMService,
        is_multimodal: bool,
        source_dir: Optional[Path] = None,
        system_message: Optional[str] = None,
    ) -> list[tuple[str, str]]:
        deltas: dict[str, float] = {}
        if is_multimodal:
            items = []
            for p in prompts:
                messages = build_conversation_message(p, is_multimodal, source_dir)
                text_side, image_side = messages[0]
                if image_side is None:
                    continue
                items.append((p.id, text_side or "", image_side))
            if items:
                deltas = self._deltas(items)
        else:
            logger.info(
                f"CIDER: text-only input ({len(prompts)} prompts) — the detector "
                f"has no image to denoise, so it is INAPPLICABLE here and every "
                f"prompt passes. Reported as inapplicability, not as coverage.")

        # tau=None is the calibration pass: measure deltas, block nothing.
        blocked: set[str] = set()
        if self._tau is not None:
            blocked = {pid for pid, d in deltas.items() if d < self._tau}
        logger.info(
            f"CIDER: tau={self._tau}, scored {len(deltas)} images, "
            f"blocked {len(blocked)}/{len(prompts)}"
            + (" (CALIBRATION PASS — nothing blocked by design)"
               if self._tau is None else ""))

        # Deltas depend ONLY on (text, image) — not on the guard, the condition, or
        # the target — so the trace is keyed by the upstream attack/channel and one
        # file per attack is both correct and collision-free across cells. It is
        # written to its OWN tree, never into the shared prompt_transform artifact
        # dir, which cells read concurrently.
        if source_dir is not None and deltas:
            try:
                out_dir = Path(self._trace_dir)
                out_dir.mkdir(parents=True, exist_ok=True)
                trace = out_dir / f"{Path(source_dir).name}.jsonl"
                with open(trace, "w") as fh:
                    for pid, d in deltas.items():
                        fh.write(json.dumps({"id": pid, "delta": d,
                                             "blocked": pid in blocked}) + "\n")
            except OSError as exc:
                logger.warning(f"CIDER: could not write delta trace: {exc}")

        target_convs = [
            (p.id, build_conversation_message(p, is_multimodal, source_dir))
            for p in prompts if p.id not in blocked
        ]
        results: dict[str, str] = {}
        if target_convs:
            results = dict(target_service.batch_chat(
                conversations=target_convs,
                system_message=system_message,
                is_test=True,
            ))
        return [(p.id, results.get(p.id, GUARD_REFUSAL_TEXT)) for p in prompts]
