"""Regression + behaviour checks for the review-5 Q2 paraphrase control arm."""
import sys
sys.path.insert(0, __file__.rsplit('/tests/', 1)[0])
from src.defense.modality_complete import (
    ModalityComplete, DECODE_VARIANTS, DECODE_PROMPT, NEUTRAL_DECODE_PROMPT,
    DECODE_PROMPT_V2, DECODE_PROMPT_V3, PARAPHRASE_DECODE_PROMPT,
)

d = ModalityComplete.__new__(ModalityComplete)
d._config = {'prompt_variant': 'v1'}

checks = []
# 1. every shipped style is byte-identical -- no published number can move
checks.append(('recover/v1 unchanged', d._decode_prompt('recover') == DECODE_PROMPT))
checks.append(('neutral/v1 unchanged', d._decode_prompt('neutral') == NEUTRAL_DECODE_PROMPT))
for v, want in (('v2', DECODE_PROMPT_V2), ('v3', DECODE_PROMPT_V3)):
    d._config = {'prompt_variant': v}
    checks.append((f'recover/{v} unchanged', d._decode_prompt('recover') == want))
d._config = {'prompt_variant': 'v1'}

# 2. the control arm resolves, and is genuinely a different instruction
para = d._decode_prompt('paraphrase')
checks.append(('paraphrase resolves', para == PARAPHRASE_DECODE_PROMPT))
checks.append(('paraphrase != decode', para != DECODE_PROMPT))
checks.append(('paraphrase != neutral', para != NEUTRAL_DECODE_PROMPT))

# 3. it must NOT ask the model to resolve the encoding (that would make it a decode arm)
low = para.lower()
checks.append(('control forbids decoding', 'do not' in low or 'do not' in low.replace('n’t', 'not')))
for banned in ('recover the plain, direct, real-world request',
               'what it is actually asking'):
    checks.append((f'control avoids decode phrasing: {banned[:34]}', banned not in low))
# 4. length is matched to the decode arm's budget
checks.append(('length budget matched', 'one or two sentences' in low
               and 'one or two plain-english sentences' in DECODE_PROMPT.lower()))
# 5. all three wordings carry the content slot
for v in ('v1', 'v2', 'v3'):
    checks.append((f'paraphrase/{v} has content slot',
                   '{content}' in DECODE_VARIANTS['paraphrase'][v]))

# 6. a typo must RAISE, never silently run the shipped arm
try:
    d._decode_prompt('paraphase')
    checks.append(('typo raises', False))
except ValueError as e:
    checks.append(('typo raises', 'unknown decode_style' in str(e)))

for name, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
bad = [n for n, ok in checks if not ok]
print()
print('FAILURES: ' + ', '.join(bad) if bad else
      f'PASS: {len(checks)} checks. Shipped arms byte-identical; control is a distinct, '
      'length-matched, non-decoding instruction; typos fail loud.')
raise SystemExit(1 if bad else 0)
