"""Precompute AMIA's automatic masking in an ISOLATED environment.

WHY THIS EXISTS
---------------
AMIA = automatic masking + joint intention analysis. Its masking stage needs
VisRAG-Ret, a `trust_remote_code` model whose vendored MiniCPM sources are frozen at
their 2024 revision. This repo resolves transformers to 5.x, under which
`modeling_minicpmv._convert_to_tensors` receives a `property` object and raises —
tokenizer SEMANTICS, not an API rename, so it cannot be shimmed without porting
openbmb's tokenizer logic into a third-party baseline we are supposed to be
reproducing faithfully. And we cannot pin transformers back, because CIDER's encoder
path needs the >=4.52 LLaVA layout in the same environment.

Running AMIA with `masking: false` would sidestep all of that, but it is NOT AMIA:
the authors' own ablation says "both masking and intention analysis are essential",
so an IA-only number invites the reviewer response that we ran the half the authors
already reported as insufficient.

Masking depends only on the (image, text) pair — it is a pure function, exactly like
CIDER's deltas. So it can be computed AHEAD of time, in its own environment, and the
result fed to the main pipeline as an ordinary upstream. The published method stays
intact and nothing is hand-patched.

VERIFIED 2026-08-10 on an AICR GPU node: transformers 4.44.2 + torch 2.13.0 loads
VisRAG-Ret and runs the exact `_encode()` call `src/defense/amia_ia.py` makes
(text (2,2304), image (2,2304)) — the transformers-5 blocker is absent.

THE ALGORITHM IS COPIED FROM `src/defense/amia_ia.py::_VisRagMasker`, not
re-derived: same sqrt(N) x sqrt(N) tiling with exact edges on the last row/column,
same VisRAG query prefix, same weighted-mean pooling, same L2 normalisation, same
"black out the K least text-relevant tiles". Any change to one MUST be mirrored in
the other or the precomputed masks stop matching the in-process implementation.

SETUP (once per cluster; ~/venvs/visrag is deliberately OUTSIDE the repo venv):
    uv venv --python 3.12 ~/venvs/visrag
    VIRTUAL_ENV=$HOME/venvs/visrag uv pip install \
        "transformers==4.44.2" torch pillow sentencepiece accelerate timm

USAGE — reads a prompt_transform subdir, writes a masked twin beside it:
    ~/venvs/visrag/bin/python src/defense/amia_precompute_mask.py \
        --src outputs/autoattack_defense/prompt_transform/harmbench/<ts>/<chain> \
        --out outputs/autoattack_defense/prompt_transform/harmbench/<ts>/<chain>__amiamask

The output is prompt_transform-shaped, so an AMIA cell consumes it with
`source_transform_subdir: <out>` and `defense_config: {masking: false}` — masking
false because it has ALREADY been applied. That combination is the FULL method; bare
`masking: false` on an unmasked upstream is the IA-only ablation. Do not conflate
them in a results table.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

VISRAG_QUERY_PREFIX = "Represent this query for retrieving relevant documents: "
MODEL = "openbmb/VisRAG-Ret"


def build_masker(n_patches: int, k_mask: int, device: str):
    import math

    import torch
    import torch.nn.functional as F
    from PIL import ImageDraw
    from transformers import AutoModel, AutoTokenizer

    grid = int(math.isqrt(n_patches))
    if grid * grid != n_patches:
        raise SystemExit(f'n_patches must be a perfect square, got {n_patches}')
    if not 0 < k_mask < n_patches:
        raise SystemExit(f'k_mask must be in (0, {n_patches}), got {k_mask}')

    tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        MODEL, trust_remote_code=True,
        torch_dtype=torch.bfloat16 if device == 'cuda' else torch.float32,
    ).to(device).eval()

    def wmp(hidden, attention_mask):
        m = attention_mask * attention_mask.cumsum(dim=1)
        return ((hidden * m.unsqueeze(-1).float()).sum(dim=1)
                / m.sum(dim=1, keepdim=True).float())

    def encode(texts=None, images=None):
        payload = ({'text': texts, 'image': [None] * len(texts), 'tokenizer': tok}
                   if texts is not None
                   else {'text': [''] * len(images), 'image': images, 'tokenizer': tok})
        with torch.no_grad():
            out = model(**payload)
            return F.normalize(wmp(out.last_hidden_state, out.attention_mask),
                               p=2, dim=1).float()

    def tiles(image):
        w, h = image.size
        out = []
        for r in range(grid):
            for c in range(grid):
                box = (w * c // grid, h * r // grid,
                       w * (c + 1) // grid if c < grid - 1 else w,
                       h * (r + 1) // grid if r < grid - 1 else h)
                out.append((box, image.crop(box)))
        return out

    def mask(image, text: str):
        rgb = image.convert('RGB')
        bt = tiles(rgb)
        t_emb = encode(texts=[VISRAG_QUERY_PREFIX + (text or '')])
        i_emb = encode(images=[t for _, t in bt])
        sims = (i_emb @ t_emb.T).squeeze(-1)
        lowest = sims.argsort()[:k_mask].tolist()
        masked = rgb.copy()
        draw = ImageDraw.Draw(masked)
        for idx in lowest:
            draw.rectangle(bt[idx][0], fill=(0, 0, 0))
        return masked, sorted(lowest)

    return mask


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='a prompt_transform subdir')
    ap.add_argument('--out', required=True, help='destination for the masked twin')
    ap.add_argument('--n-patches', type=int, default=16)   # paper §4.1
    ap.add_argument('--k-mask', type=int, default=3)       # paper §4.1
    ap.add_argument('--device', default='cuda')
    ap.add_argument('--limit', type=int, default=0, help='pilot on the first N rows')
    args = ap.parse_args()

    src_prompts = os.path.join(args.src, 'prompts.jsonl')
    if not os.path.exists(src_prompts):
        raise SystemExit(f'no prompts.jsonl under {args.src}')
    rows = [json.loads(l) for l in open(src_prompts, encoding='utf-8') if l.strip()]
    if args.limit:
        rows = rows[:args.limit]
    if not any(r.get('image_encoded') for r in rows):
        raise SystemExit(
            f'{args.src} has no image_encoded — AMIA masking is an IMAGE-channel '
            'operation. A text-only chain needs no precompute; run it with '
            'masking:false, which for a text-only input is the whole method.')

    from PIL import Image

    os.makedirs(os.path.join(args.out, 'images'), exist_ok=True)
    mask = build_masker(args.n_patches, args.k_mask, args.device)

    n_img = 0
    trace = []
    for row in rows:
        paths = row.get('image_encoded') or []
        newp = []
        for p in paths:
            ap_ = p if os.path.isabs(p) else os.path.join(args.src, os.path.basename(
                os.path.dirname(p)), os.path.basename(p))
            if not os.path.exists(ap_):
                ap_ = os.path.join(args.src, 'images', os.path.basename(p))
            if not os.path.exists(ap_):
                raise SystemExit(f'image not found for {row.get("id")}: {p}')
            masked, blacked = mask(Image.open(ap_), row.get('encoded') or '')
            dst_rel = os.path.join('images', os.path.basename(ap_))
            masked.save(os.path.join(args.out, dst_rel))
            newp.append(dst_rel)
            trace.append({'id': row.get('id'), 'image': os.path.basename(ap_),
                          'blacked_tiles': blacked})
            n_img += 1
        row['image_encoded'] = newp

    with open(os.path.join(args.out, 'prompts.jsonl'), 'w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row) + '\n')

    # Carry the upstream's metadata, stamped so a masked twin can never be mistaken
    # for the original in an output tree.
    meta_path = os.path.join(args.src, 'results.json')
    meta = json.load(open(meta_path, encoding='utf-8')) if os.path.exists(meta_path) else {}
    meta['amia_masking'] = {
        'source_dir': args.src, 'model': MODEL,
        'n_patches': args.n_patches, 'k_mask': args.k_mask,
        'transformers': __import__('transformers').__version__,
        'note': ('AMIA automatic masking precomputed in an isolated environment; '
                 'consume with defense_config.masking=false, which together with '
                 'this upstream is the FULL published method.'),
    }
    meta['count'] = len(rows)
    with open(os.path.join(args.out, 'results.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)
    with open(os.path.join(args.out, 'mask_trace.jsonl'), 'w', encoding='utf-8') as f:
        for t in trace:
            f.write(json.dumps(t) + '\n')

    print(f'masked {n_img} images over {len(rows)} prompts -> {args.out}')


if __name__ == '__main__':
    sys.exit(main())
