"""
Experiment orchestrator for Encoding × Modality jailbreaking.

Two independent parameters control execution:

  num_main_job_threads  — thread pool size inside the orchestrator process.
      Tasks arrive in queue order; each occupies a thread, runs, and
      releases the thread on completion so the next queued task can start.
      Implemented via asyncio.Semaphore.

  num_cluster_jobs      — total SLURM job budget (orchestrator counts as 1,
      remaining slots are available for vLLM servers).  Hard-capped by
      MAX_SUBMIT_JOBS_PER_USER (cluster QOS restriction).

Cluster models: vLLM servers are started before task execution and shut
down afterward.  Tasks using cluster models get endpoints via
LLMServiceFactory.

Usage:
    exp = Experiment(conf_dir, num_main_job_threads=5, num_cluster_jobs=8)
    exp.add_tasks(mixed_tasks)
    results = exp.run()
"""
from __future__ import annotations

import asyncio
import time
import traceback
from collections import deque
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml

from .task import run_task
from .constants import MAX_SUBMIT_JOBS_PER_USER
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ==================== Config Loading ====================

def load_preset(name: str, conf_dir: Optional[Path] = None) -> "ExperimentPreset":
    """Load and validate an experiment preset from conf/experiment/<name>.yaml.

    Returns a typed ExperimentPreset; pydantic validation fails loud at this
    boundary so YAML typos surface with field paths, not deep in a runner.
    """
    from .schemas import ExperimentPreset

    if conf_dir is None:
        conf_dir = Path(__file__).resolve().parent.parent.parent / "conf"

    path = conf_dir / "experiment" / f"{name}.yaml"
    if not path.exists():
        available = sorted(
            p.stem for p in (conf_dir / "experiment").glob("*.yaml")
        )
        raise FileNotFoundError(
            f"Preset '{name}' not found at {path}\n"
            f"Available presets: {', '.join(available)}"
        )
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return ExperimentPreset.model_validate(data)


# ==================== Task Classification ====================

class TaskType(str, Enum):
    """Task type based on model requirements."""
    API_MODEL = "api_model"          # uses cloud API (GPT-4o, Gemini, Claude)
    CLUSTER_MODEL = "cluster_model"  # uses vLLM server on cluster GPU
    NO_MODEL = "no_model"            # no model query (imaging)


def _target_model_for_task(task) -> Optional[str]:
    """Return the model-string this task targets (None if the mode doesn't have one).

    Only defense+evaluate tasks have a top-level target model. prompt_transform
    chains may invoke an encoder LLM (via merged conf/text_encoding YAML) but
    those don't drive orchestrator-level cluster-server discovery — the
    factory handles them inline.
    """
    from .schemas import DefenseEvaluateTask
    if isinstance(task, DefenseEvaluateTask):
        return task.target_model
    return None


def _infer_task_type(task) -> TaskType:
    """Infer task type from a typed TaskConfig variant."""
    from .schemas import PromptTransformTask
    if isinstance(task, PromptTransformTask):
        # prompt_transform may make LLM calls inside encoders, but those go
        # through API-based encoder LLMs (gpt-4.1-mini etc.) — not cluster.
        return TaskType.NO_MODEL

    model_str = _target_model_for_task(task)
    if model_str:
        from src.llm_utils import LLMModel, Provider
        try:
            m = LLMModel.from_string(model_str)
            if m.provider == Provider.NU_CLUSTER:
                return TaskType.CLUSTER_MODEL
        except ValueError:
            pass
        return TaskType.API_MODEL

    return TaskType.NO_MODEL


def _resolve_model(model_str: str) -> Optional[Any]:
    """Resolve model string to LLMModel enum, or None."""
    from src.llm_utils import LLMModel
    try:
        return LLMModel.from_string(model_str)
    except ValueError:
        return None


# Pre-canonical-refactor design: ALL evaluators share one judge LLM config,
# read from conf/evaluation/default.yaml::judge_llm_config.model. So
# "judge_method" → judge model is constant across methods at any point in
# time — they all use whatever's in the YAML.
_KNOWN_JUDGE_METHODS = {"harmbench", "jailbreakbench", "refusal", "orbench"}


def _judge_model_for_method(judge_method: str) -> Optional[Any]:
    """Resolve a judge_method slug to the LLMModel currently configured to
    judge it (from conf/evaluation/default.yaml::judge_llm_config.model).

    Returns None for unknown methods or if the YAML can't be loaded. Used
    by the orchestrator to pre-discover cluster-hosted judges so vLLM
    servers can be started before tasks run. When the configured judge is
    an API model (e.g. gpt-5-nano), discovery correctly returns a
    Provider.OPENAI model → orchestrator skips cluster setup for judges.
    """
    if judge_method not in _KNOWN_JUDGE_METHODS:
        return None
    try:
        from .config import load_conf
        from src.llm_utils import LLMModel
        eval_config = load_conf("evaluation")
        judge_cfg = eval_config.get("judge_llm_config", {})
        model_str = judge_cfg.get("model")
        if not model_str:
            return None
        return LLMModel.from_string(model_str)
    except Exception:
        return None


def _required_cluster_models_for_task(info: "TaskInfo") -> set:
    """Return the set of cluster-hosted LLMModels this task needs.

    Covers the target model (if cluster-hosted), the judge model(s) for the
    evaluator(s) that will run, AND any cluster-hosted SECOND model a defense
    itself references (Round-3 guard amplifier's `guard_model`, or
    SemanticSmooth's `perturbation_model`). Judge discovery has two paths:

      1. Explicit override: task.judge_method set in YAML.
      2. Canonical inference: derive judge_method list from the benchmark
         slug (via EvaluatorFactory.judge_methods_for_benchmark). The
         benchmark itself comes from task.benchmark or the upstream
         source_transform_subdir path.

    Without path (2), removing `judge_method` from task YAMLs would silently
    bypass cluster judge discovery — tasks would hang on acquire_endpoint().

    Defense-config scan is DELIBERATELY narrow: only the two known
    second-model keys (`guard_model`, `perturbation_model`) are looked up —
    defense_config is a free-form dict and we don't want to guess at
    arbitrary keys. Extend this tuple deliberately if a new defense adds
    another second-model config key.

    Budget note: a defense+evaluate task with a cluster target AND a cluster
    guard AND a cluster judge needs orchestrator + 3 vLLM servers = 4 SLURM
    jobs (well under MAX_SUBMIT_JOBS_PER_USER=8, but each cluster-hosted
    second model directly consumes num_cluster_jobs — account for it when
    sizing a round with multiple concurrent cluster-guard tasks).
    """
    from src.llm_utils import Provider
    from .schemas import DefenseEvaluateTask
    from .task import _infer_benchmark
    from src.evaluation.evaluator_factory import judge_methods_for_benchmark

    task = info.task
    required: set = set()

    # Target model (only meaningful for defense+evaluate)
    target = _target_model_for_task(task)
    if target:
        m = _resolve_model(target)
        if m is not None and m.provider == Provider.NU_CLUSTER:
            required.add(m)

    # Judge model(s) for defense+evaluate
    if isinstance(task, DefenseEvaluateTask):
        if task.judge_method:
            judge = _judge_model_for_method(task.judge_method)
            if judge is not None and judge.provider == Provider.NU_CLUSTER:
                required.add(judge)
        else:
            try:
                benchmark = task.benchmark or _infer_benchmark(
                    task.source_transform_subdir)
                methods = judge_methods_for_benchmark(benchmark)
            except ValueError:
                methods = []
            for method in methods:
                judge = _judge_model_for_method(method)
                if judge is not None and judge.provider == Provider.NU_CLUSTER:
                    required.add(judge)

        # Defense-owned second model(s) — guard_baseline / modality_complete's
        # guard_model, and semantic_smooth's perturbation_model. Only these
        # two keys are scanned (see docstring).
        for key in ("guard_model", "perturbation_model"):
            model_str = task.defense_config.get(key)
            if model_str:
                m = _resolve_model(model_str)
                if m is not None and m.provider == Provider.NU_CLUSTER:
                    required.add(m)

    return required


@dataclass
class TaskInfo:
    """Task metadata for scheduling. Holds a typed TaskConfig."""
    index: int
    task: Any            # TaskConfig (discriminated union); kept as Any to avoid forward-ref
    name: str

    @property
    def mode(self) -> str:
        return self.task.mode

    @property
    def task_type(self) -> TaskType:
        return _infer_task_type(self.task)

    @property
    def config(self) -> dict:
        """Plain dict view of the task (for code paths that still want it)."""
        return self.task.model_dump()


def _get_task_name(task, index: int) -> str:
    """Generate a descriptive name for a typed TaskConfig."""
    from .schemas import DefenseEvaluateTask, PromptTransformTask, TransformationSpec
    parts = [task.mode]
    if isinstance(task, PromptTransformTask):
        chain = [
            s.type if isinstance(s, TransformationSpec) else s.get("type", "?")
            for s in task.transformation_list
        ]
        parts.append("+".join(chain))
    elif isinstance(task, DefenseEvaluateTask):
        parts.append(task.defense)
        parts.append(task.target_model)
    parts.append(str(index))
    return "_".join(parts)


# ==================== Orchestrator ====================

class Experiment:
    """
    Experiment orchestrator with thread-pool scheduling and vLLM server lifecycle.
    
    The orchestrator maintains a thread pool (sized by num_main_job_threads).
    Tasks arrive in queue order; each occupies a thread from the pool, runs,
    and releases the thread on completion so the next queued task can proceed.
    
    For cluster models, vLLM servers are submitted as separate SLURM jobs.
    The total number of SLURM jobs (1 orchestrator + N vLLM servers) is
    capped by num_cluster_jobs.
    
    Usage:
        exp = Experiment(conf_dir, num_main_job_threads=5, num_cluster_jobs=8)
        exp.add_tasks(mixed_tasks)
        results = exp.run()
    """

    def __init__(self, conf_dir: Optional[Path] = None,
                 num_main_job_threads: int = 5,
                 num_cluster_jobs: int = MAX_SUBMIT_JOBS_PER_USER):
        """
        Args:
            conf_dir: Path to conf/ directory.
            num_main_job_threads: Thread pool size — max concurrent tasks
                within this orchestrator process.
            num_cluster_jobs: Total SLURM job budget (orchestrator + vLLM
                servers).  Capped at MAX_SUBMIT_JOBS_PER_USER (= 8).
        """
        if conf_dir is None:
            conf_dir = Path(__file__).resolve().parent.parent.parent / "conf"
        self.conf_dir = conf_dir
        self.tasks: deque[TaskInfo] = deque()
        self.results: list[dict[str, Any]] = []
        self.num_main_job_threads = num_main_job_threads
        self.num_cluster_jobs = min(num_cluster_jobs, MAX_SUBMIT_JOBS_PER_USER)
        self._task_counter = 0
        self._server_manager = None
        # Per-model remaining-task counter; populated in _run_async() and
        # decremented in _run_task_safe() so we can mid-run-teardown a model's
        # vLLM servers as soon as the last task needing it completes.
        self._model_remaining: dict = {}

    def add_task(self, task_def) -> None:
        """Add a task to the queue.

        Accepts either a plain dict (validated via the Pydantic TaskConfig
        discriminated union) or an already-validated TaskConfig instance.
        Typed validation fails loud at this boundary — typos in YAML fields
        raise ValidationError with field paths, instead of failing deep
        inside a runner.
        """
        from .schemas import (
            DefenseEvaluateTask, PromptTransformTask,
        )
        from pydantic import TypeAdapter
        from .schemas import TaskConfig as _TaskConfigAlias

        if isinstance(task_def, (PromptTransformTask, DefenseEvaluateTask)):
            task = task_def
        else:
            # TypeAdapter handles the Annotated[Union[...], Discriminator(...)]
            task = TypeAdapter(_TaskConfigAlias).validate_python(task_def)

        info = TaskInfo(
            index=self._task_counter,
            task=task,
            name=_get_task_name(task, self._task_counter),
        )
        self.tasks.append(info)
        self._task_counter += 1
        logger.debug(
            f"Added task '{info.name}' (type={info.task_type.value}, "
            f"total: {len(self.tasks)})")

    def add_tasks(self, task_defs: list) -> None:
        """Add multiple task definitions to the queue."""
        for task_def in task_defs:
            self.add_task(task_def)

    # ==================== Cluster Server Management ====================

    def _find_cluster_models(self, tasks: list[TaskInfo]) -> set:
        """Scan tasks for unique cluster models that need vLLM servers.

        Covers BOTH the task's target model AND the judge model implied by
        judge_method (each evaluator hard-binds its canonical judge via its
        own constants.JUDGE_MODEL). Without judge inclusion, an `evaluate`
        task with an API target + cluster-hosted judge silently hangs on
        acquire_endpoint() because the judge's vLLM server was never started.
        """
        cluster_models: set = set()
        for task in tasks:
            cluster_models |= _required_cluster_models_for_task(task)
        return cluster_models

    def _load_cluster_config(self, model):
        """
        Load cluster server config for a model.

        Uses the shared _load_conf helper: merges conf/llm/default.yaml
        with any model-specific overrides, returns the 'cluster' section.
        """
        from .config import load_conf

        return load_conf(
            "llm", section="cluster",
            match_field="model.model", match_value=model.model_id)

    def _count_existing_slurm_jobs(self) -> int:
        """Count this user's existing SLURM jobs that count against the QOS budget.

        Used as a pre-flight check before submitting vLLM server jobs, so we
        don't over-submit when the user already has unrelated jobs queued
        (HF downloads, prior experiments, etc.).

        Excludes the orchestrator's own job (if running under SLURM, identified
        via SLURM_JOB_ID) — that one is what we're sitting in.
        """
        import os
        import subprocess

        user = os.environ.get("USER")
        if not user:
            return 0
        try:
            result = subprocess.run(
                ["squeue", "-u", user, "-h", "-o", "%i"],
                capture_output=True, text=True, timeout=15)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.debug("squeue unavailable; skipping pre-flight budget check.")
            return 0
        if result.returncode != 0:
            return 0
        own_job = os.environ.get("SLURM_JOB_ID")
        job_ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if own_job:
            job_ids = [j for j in job_ids if j != own_job]
        return len(job_ids)

    def _wait_for_servers_parallel(self, models: list) -> set:
        """Wait for the first server of each model to come up, in parallel.

        Returns the set of models whose first server failed to start —
        the caller skips tasks for those models upfront so they don't hang
        waiting for an endpoint that will never exist.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        failed: set = set()
        if not models:
            return failed
        with ThreadPoolExecutor(
            max_workers=len(models), thread_name_prefix="server-wait"
        ) as ex:
            futures = {
                ex.submit(self._server_manager.wait_for_first_server, m): m
                for m in models
            }
            for fut in as_completed(futures):
                model = futures[fut]
                try:
                    endpoint = fut.result()
                    logger.info(f"  → {model.model_id}: first server ready at {endpoint}")
                except RuntimeError as e:
                    logger.error(f"  ✗ {model.model_id}: server failed — {e}")
                    failed.add(model)
        return failed

    def _setup_cluster_servers(self, cluster_models: set) -> None:
        """Submit vLLM servers for all cluster models and return immediately.

        Fire-and-forget: this method does NOT wait for any server to become
        healthy. Tasks block on `acquire_endpoint(model)` when they need a
        not-yet-ready model, and the manager's monitor thread populates
        the pool as servers come up.

        This is what gives us "dispatch as servers come up" behavior: fast
        judges' tasks run as soon as that judge is ready, without being
        gated by slow/queued judges. A slow judge (e.g. queue-blocked on
        QoS) only delays the tasks that depend on it, not the whole run.

        `acquire_endpoint` has its own short-circuit: if all submitted jobs
        for a model are marked failed by the monitor, the next acquire
        immediately raises RuntimeError instead of waiting through the full
        endpoint timeout.

        Budget enforcement is two-layered (still done synchronously here):
          1. Pre-flight against MAX_SUBMIT_JOBS_PER_USER minus the user's
             existing SLURM jobs.
          2. Cap num_instances per model to never exceed each model's YAML
             request — capping never *promotes* a model's count.

        Port assignment uses a cumulative offset over a stable model order
        (sorted by model_id) — prevents collisions with mixed num_instances
        and keeps assignments reproducible across runs.
        """
        from src.llm_utils.cluster_server_manager import ClusterModelServerManager
        from src.llm_utils import LLMServiceFactory

        self._server_manager = ClusterModelServerManager()

        # Stable order: sort by model_id so port assignment is reproducible
        # and `enumerate(set)`'s non-determinism doesn't bite us.
        cluster_models_sorted = sorted(cluster_models, key=lambda m: m.model_id)
        model_configs = {m: self._load_cluster_config(m) for m in cluster_models_sorted}

        # Pre-flight: account for any existing user SLURM jobs against QOS budget.
        existing = self._count_existing_slurm_jobs()
        if existing:
            effective_budget = min(
                self.num_cluster_jobs, MAX_SUBMIT_JOBS_PER_USER - existing
            )
            logger.warning(
                f"Pre-flight: user has {existing} existing SLURM job(s). "
                f"Effective budget = min(num_cluster_jobs={self.num_cluster_jobs}, "
                f"MAX={MAX_SUBMIT_JOBS_PER_USER} - existing={existing}) "
                f"= {effective_budget}")
        else:
            effective_budget = self.num_cluster_jobs

        available_slots = effective_budget - 1  # 1 reserved for orchestrator
        if available_slots < 1:
            raise RuntimeError(
                f"No SLURM slots available after pre-flight: existing={existing}, "
                f"num_cluster_jobs={self.num_cluster_jobs}, "
                f"effective_budget={effective_budget}. Aborting before submission.")

        # Cap num_instances proportionally if over budget — but never promote.
        requested = {m: cfg.get("num_instances", 1) for m, cfg in model_configs.items()}
        total_requested = sum(requested.values())
        if total_requested > available_slots:
            n_models = len(model_configs)
            per_model_cap = max(available_slots // n_models, 1)
            logger.warning(
                f"Requested {total_requested} vLLM instances exceeds "
                f"{available_slots} slots; capping each model to "
                f"<= {per_model_cap} (never promotes above YAML request).")
            for m, cfg in model_configs.items():
                new = min(requested[m], per_model_cap)
                if new != requested[m]:
                    logger.info(f"  {m.model_id}: {requested[m]} -> {new} instance(s)")
                cfg["num_instances"] = new

        # Cumulative port assignment over the sorted model list.
        # Base port comes from the YAML default (typically 8000); each model's
        # port range is contiguous and non-overlapping.
        base_port = next(iter(model_configs.values()))["port"]
        next_port = base_port
        for m in cluster_models_sorted:
            cfg = model_configs[m]
            cfg["port"] = next_port
            next_port += cfg["num_instances"]
            logger.info(
                f"Starting {cfg['num_instances']} vLLM server(s) for "
                f"{m.model_id} on port(s) {cfg['port']}-"
                f"{cfg['port'] + cfg['num_instances'] - 1}")
            self._server_manager.start_server(m, cfg)

        # Register with factory so tasks auto-get endpoints when they call
        # acquire_endpoint(). No upfront blocking wait — tasks dispatch
        # immediately; slow servers only block their own dependent tasks.
        LLMServiceFactory.set_server_manager(self._server_manager)
        logger.info(
            "Server submission complete. Tasks will start dispatching "
            "immediately; per-task acquire_endpoint() will wait per-server.")

    def _teardown_cluster_servers(self) -> None:
        """Shut down all vLLM servers and clear factory-side singleton state."""
        if self._server_manager:
            logger.info("Shutting down cluster vLLM servers...")
            self._server_manager.shutdown_all()
            self._server_manager = None
        # Clear the factory's class-level singleton so subsequent Experiment
        # runs in the same process don't see a stale (shut-down) manager.
        from src.llm_utils import LLMServiceFactory
        LLMServiceFactory.clear_server_manager()

    def _maybe_release_model(self, model) -> None:
        """Decrement remaining-task count for a model; scancel its servers when 0.

        Lets the orchestrator free a heavy model's GPU allocation mid-experiment
        as soon as the last task needing it finishes — instead of holding
        4× A100s pinned for the entire experiment.
        """
        if not self._model_remaining or model not in self._model_remaining:
            return
        remaining = self._model_remaining[model] - 1
        self._model_remaining[model] = remaining
        if remaining <= 0 and self._server_manager is not None:
            logger.info(
                f"All tasks for {model.model_id} complete; "
                f"shutting down its vLLM servers to free GPUs.")
            try:
                self._server_manager.shutdown_model(model)
            except Exception as e:
                logger.warning(f"shutdown_model({model.model_id}) failed: {e}")

    # ==================== Async Execution ====================

    async def _run_task_safe(
        self, task: TaskInfo, semaphore: asyncio.Semaphore,
        queue_name: str, total: int,
    ) -> dict[str, Any]:
        """Execute a single task with semaphore-based concurrency control.

        No upfront skip — if the task's required cluster model failed to
        start, the failure surfaces inside the runner when it calls
        acquire_endpoint(), which short-circuits on all-jobs-failed. The
        runner's try/except catches and reports the failure cleanly.

        Equivalent outcome to the old upfront-skip, but doesn't require
        the orchestrator to know about failed models in advance — which is
        what unblocks "dispatch as servers come up" (some tasks dispatch
        before slow servers are even known to have failed or succeeded).
        """
        # Resolve cluster-model dependencies once so we can decrement
        # remaining counts on completion (mid-run teardown).
        required_cluster = _required_cluster_models_for_task(task)

        async with semaphore:
            logger.info(f"\n{'~'*70}")
            logger.info(f"[{queue_name}] Executing Task {task.index+1}/{total}: {task.name}")
            logger.info(f"{'~'*70}\n")

            t0 = time.time()
            try:
                # Run synchronous task in thread pool
                result = await asyncio.to_thread(run_task, task.task)
                elapsed = time.time() - t0
                result["task_name"] = task.name
                result["original_index"] = task.index
                result["status"] = result.get("status", "success")
                result["elapsed_seconds"] = round(elapsed, 1)

                logger.info(f"[{queue_name}] Completed: {task.name} ({elapsed:.1f}s)")
                return result
            except Exception as e:
                elapsed = time.time() - t0
                err_str = str(e)
                err_summary = err_str[:500] + "..." if len(err_str) > 500 else err_str
                tb = traceback.format_exc()
                tb_lines = tb.splitlines()
                tb_short = "\n".join(tb_lines[:20] + (["  ... (truncated)"] if len(tb_lines) > 20 else []))
                logger.error(f"[{queue_name}] Failed: {task.name} ({elapsed:.1f}s) — {err_summary}")
                logger.error(tb_short)
                return {
                    "task_name": task.name,
                    "original_index": task.index,
                    "status": "failed",
                    "error": err_summary,
                    "traceback": tb_short,
                    "elapsed_seconds": round(elapsed, 1),
                }
            finally:
                # Mid-run teardown: decrement remaining count and shut down
                # this model's servers if it was the last task needing them.
                for m in required_cluster:
                    self._maybe_release_model(m)

    async def _run_async(self) -> list[dict[str, Any]]:
        """
        Execute all tasks with thread-pool scheduling.
        
        Tasks share one semaphore (num_main_job_threads) acting as a thread
        pool: each task acquires a slot in queue order, runs, and releases.
        Cluster models: vLLM servers are started before tasks run,
        and shut down after all tasks complete (or on error).
        """
        if not self.tasks:
            logger.warning("No tasks to execute")
            return []

        tasks_to_run = list(self.tasks)
        self.tasks.clear()
        total = len(tasks_to_run)

        # Build per-model remaining-task counts (covers target AND judge).
        # Used by _maybe_release_model() for mid-run server teardown.
        self._model_remaining = {}
        for task in tasks_to_run:
            for m in _required_cluster_models_for_task(task):
                self._model_remaining[m] = self._model_remaining.get(m, 0) + 1

        try:
            # Submit vLLM servers for cluster models. Non-blocking: tasks
            # dispatch immediately and per-task acquire_endpoint() handles
            # the wait for each model independently.
            cluster_models = self._find_cluster_models(tasks_to_run)
            if cluster_models:
                model_names = sorted(m.model_id for m in cluster_models)
                logger.info(f"Cluster models detected: {model_names}")
                self._setup_cluster_servers(cluster_models)

            logger.info(f"\n{'='*70}")
            logger.info(f"EXPERIMENT: {total} tasks (thread pool: {self.num_main_job_threads}, "
                        f"cluster jobs: {self.num_cluster_jobs})")
            logger.info(f"{'='*70}\n")

            # Thread pool: tasks acquire a slot in order, run, release.
            # Tasks needing a slow/failed cluster model will block per-task
            # on acquire_endpoint() (or fail-fast on its all-failed short-
            # circuit), while tasks needing already-ready models proceed.
            sem = asyncio.Semaphore(self.num_main_job_threads)
            coroutines = [
                self._run_task_safe(task, sem, task.mode.upper(), total)
                for task in tasks_to_run
            ]

            self.results = list(await asyncio.gather(*coroutines))

        finally:
            # Always shut down cluster servers, even on error
            self._teardown_cluster_servers()
            self._model_remaining = {}

        self._print_summary()
        return self.results

    def run(self) -> list[dict[str, Any]]:
        """Execute tasks (sync entry point)."""
        return asyncio.run(self._run_async())

    def _print_summary(self):
        """Print experiment summary."""
        logger.info(f"\n{'='*70}")
        logger.info("EXPERIMENT SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Total tasks executed: {len(self.results)}")

        successful = sum(1 for r in self.results if r.get("status") == "success")
        failed = len(self.results) - successful

        logger.info(f"Successful: {successful}")
        if failed > 0:
            logger.info(f"Failed: {failed}")
            for r in self.results:
                if r.get("status") == "failed":
                    logger.info(f"  ✗ {r.get('task_name', 'unknown')}: {r.get('error', 'unknown')}")

        # Per-task timing
        for r in self.results:
            elapsed = r.get("elapsed_seconds", 0)
            status = "✓" if r.get("status") == "success" else "✗"
            logger.info(f"  {status} {r.get('task_name', 'unknown'):40s} {elapsed:>7.1f}s")

        # Aggregate statistics
        total_prompts = sum(
            r.get('count', r.get('num_prompts', 0)) for r in self.results
            if isinstance(r, dict)
        )
        if total_prompts:
            logger.info(f"Total prompts processed: {total_prompts}")

        total_elapsed = sum(r.get("elapsed_seconds", 0) for r in self.results)
        logger.info(f"Total task time: {total_elapsed:.1f}s")
        logger.info(f"{'='*70}\n")

    def __repr__(self) -> str:
        return (f"Experiment(tasks={len(self.tasks)}, "
                f"threads={self.num_main_job_threads}, "
                f"cluster_jobs={self.num_cluster_jobs})")


# ==================== Convenience ====================

def run_experiment_from_preset(preset_name: str, conf_dir: Optional[Path] = None) -> list[dict[str, Any]]:
    """Run an experiment from a preset name."""
    if conf_dir is None:
        conf_dir = Path(__file__).resolve().parent.parent.parent / "conf"
    preset = load_preset(preset_name, conf_dir)

    exp = Experiment(
        conf_dir,
        num_main_job_threads=preset.num_main_job_threads,
        num_cluster_jobs=preset.num_cluster_jobs,
    )
    exp.add_tasks(preset.tasks)
    return exp.run()
