"""Prove the mechanism-error guard fires on every evaluator, not just HarmBench.

Reproduces the 2026-07-10 official-HarmBench failure: every judge call returns an
HTTP 400 sentinel, the parser reads each as a fail-safe default, and the cell would
previously have shipped a clean-looking rate with PERFECT coverage.
"""
from llm_utils.base_llm_service import make_mechanism_error

from src.evaluation.harmbench_evaluation.evaluator import HarmBenchEvaluator
from src.evaluation.jailbreakbench_evaluation.evaluator import JailbreakBenchEvaluator
from src.evaluation.jailbreakbench_refusal_evaluation.evaluator import JailbreakBenchRefusalEvaluator
from src.evaluation.orbench_evaluation.evaluator import ORBenchEvaluator
from src.evaluation.wildguard_evaluation.evaluator import WildGuardEvaluator

ERR = make_mechanism_error(
    "Error code: 400 - max_tokens=16384 cannot be greater than max_model_len=2048")


class FakeService:
    def __init__(self, mode, healthy_text):
        self.mode = mode
        self.healthy_text = healthy_text

    def batch_chat(self, conversations, system_message=None, is_test=False):
        payload = ERR if self.mode == "broken" else self.healthy_text
        return [(pid, payload) for pid, _ in conversations]


N = 10
prompts = [{"id": f"b{i}", "prompt": f"behavior {i}", "category": "test"} for i in range(N)]
processed = [p["prompt"] for p in prompts]
responses = {f"b{i}": f"a generation {i}" for i in range(N)}

CASES = [
    ("HarmBench", HarmBenchEvaluator, '<json>{"answer": "yes", "reasoning": "r"}</json>'),
    ("JailbreakBench", JailbreakBenchEvaluator, '<json>{"answer": "unsafe", "reasoning": "r"}</json>'),
    ("JBB-Refusal", JailbreakBenchRefusalEvaluator, '<json>{"answer": "yes", "reasoning": "r"}</json>'),
    ("ORBench", ORBenchEvaluator, "[[direct_answer]]"),
    ("WildGuard", WildGuardEvaluator,
     "Harmful request: yes\nResponse refusal: no\nHarmful response: yes"),
]

print(f"{'evaluator':<16}{'mode':<9}{'rate':>8}{'covered':>9}{'MECH':>6}   verdict")
print("-" * 62)
failures = []
for name, cls, healthy in CASES:
    for mode in ("broken", "healthy"):
        ev = cls.__new__(cls)
        ev.model = "stub-judge"
        ev._service = FakeService(mode, healthy)
        try:
            _, stats = ev.evaluate(prompts, processed, responses)
        except Exception as exc:  # noqa: BLE001
            print(f"{name:<16}{mode:<9}{'ERR':>8}{'-':>9}{'-':>6}   {type(exc).__name__}: {exc}")
            failures.append(f"{name}/{mode} raised")
            continue
        rate = stats.get("attack_success_rate")
        if rate is None:
            rate = stats.get("refusal_rate")
        covered = stats.get("total_evaluated")
        mech = stats.get("mechanism_error_count")
        if mode == "broken":
            ok = mech == N and covered == N
            note = "CAUGHT (coverage was perfect)" if ok else "MISSED"
            if not ok:
                failures.append(f"{name}: broken run not caught (mech={mech}, covered={covered})")
        else:
            ok = not mech
            note = "clean" if ok else "false positive"
            if not ok:
                failures.append(f"{name}: healthy run flagged (mech={mech})")
        rate_s = "n/a" if rate is None else f"{rate:.1f}"
        print(f"{name:<16}{mode:<9}{rate_s:>8}{str(covered):>9}{str(mech):>6}   {note}")

print()
if failures:
    print("FAILURES:")
    for f in failures:
        print("  -", f)
    raise SystemExit(1)
print("PASS: every evaluator reports mechanism errors, and none false-positives on a healthy run.")
