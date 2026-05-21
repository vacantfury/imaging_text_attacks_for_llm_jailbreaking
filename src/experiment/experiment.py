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

def load_preset(name: str, conf_dir: Optional[Path] = None) -> dict[str, Any]:
    """
    Load an experiment preset from conf/experiment/<name>.yaml.
    """
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
        return yaml.safe_load(f) or {}


# ==================== Task Classification ====================

class TaskType(str, Enum):
    """Task type based on model requirements."""
    API_MODEL = "api_model"          # uses cloud API (GPT-4o, Gemini, Claude)
    CLUSTER_MODEL = "cluster_model"  # uses vLLM server on cluster GPU
    NO_MODEL = "no_model"            # no model query (imaging)


def _infer_task_type(task_config: dict) -> TaskType:
    """Infer task type from config. YAML 'type' field takes priority."""
    # Explicit override from YAML
    explicit = task_config.get("type")
    if explicit:
        return TaskType(explicit)
    
    # imaging never needs a model
    if task_config.get("mode") == "imaging":
        return TaskType.NO_MODEL
    
    # Check model parameter
    model_str = task_config.get("model", "")
    if model_str:
        from src.llm_utils import LLMModel, Provider
        try:
            model = LLMModel.from_string(model_str)
            if model.provider == Provider.NU_CLUSTER:
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


# Map judge_method → evaluator package. We read constants.JUDGE_MODEL from each
# package directly so the orchestrator stays in sync with whatever the
# evaluator actually uses (canonical hard-binding lives there).
_JUDGE_METHOD_TO_PACKAGE: dict[str, str] = {
    "harmbench": "src.evaluation.harmbench_evaluation",
    "jailbreakbench": "src.evaluation.jailbreakbench_evaluation",
    "refusal": "src.evaluation.jailbreakbench_refusal_evaluation",
    "orbench": "src.evaluation.orbench_evaluation",
}


def _judge_model_for_method(judge_method: str) -> Optional[Any]:
    """Resolve a judge_method string to the LLMModel its evaluator hard-binds.

    Returns None if the method is unknown or its constants module can't be
    imported. Used by the orchestrator to pre-start vLLM servers for cluster
    judges, so evaluator calls don't hang on acquire_endpoint().
    """
    pkg = _JUDGE_METHOD_TO_PACKAGE.get(judge_method)
    if not pkg:
        return None
    try:
        import importlib
        constants = importlib.import_module(f"{pkg}.constants")
    except ImportError:
        return None
    return getattr(constants, "JUDGE_MODEL", None)


def _required_cluster_models_for_task(task: "TaskInfo") -> set:
    """Return the set of cluster-hosted LLMModels this task needs.

    Includes the target model (if cluster-hosted) AND the judge model implied
    by judge_method (if cluster-hosted). Modes that don't query a model
    (imaging) return empty.
    """
    from src.llm_utils import Provider
    required: set = set()

    # Target model
    if task.task_type == TaskType.CLUSTER_MODEL:
        m = _resolve_model(task.config.get("model", ""))
        if m is not None:
            required.add(m)

    # Judge model (any mode that runs an evaluator)
    if task.mode in ("evaluate", "defense"):
        judge_method = (
            task.config.get("judge_method")
            or task.config.get("evaluation", {}).get("judge_method")
        )
        if judge_method:
            judge = _judge_model_for_method(judge_method)
            if judge is not None and judge.provider == Provider.NU_CLUSTER:
                required.add(judge)

    return required


@dataclass
class TaskInfo:
    """Task metadata for scheduling."""
    index: int
    config: dict[str, Any]
    mode: str
    task_type: TaskType
    name: str


def _get_task_name(task_config: dict, index: int) -> str:
    """Generate a descriptive name for a task."""
    mode = task_config.get("mode", "unknown")
    encoding = task_config.get("encoding", "")
    model = task_config.get("model", "")
    modality = task_config.get("modality", "")
    parts = [mode]
    if encoding:
        parts.append(encoding)
    if model:
        parts.append(model)
    if modality:
        parts.append(modality)
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

    def add_task(self, task_def: dict[str, Any]) -> None:
        """Add a task definition (from experiment YAML) to the queue."""
        task_type = _infer_task_type(task_def)
        task_info = TaskInfo(
            index=self._task_counter,
            config=task_def,
            mode=task_def.get("mode", "unknown"),
            task_type=task_type,
            name=_get_task_name(task_def, self._task_counter),
        )
        self.tasks.append(task_info)
        self._task_counter += 1
        logger.debug(f"Added task '{task_info.name}' (type={task_type.value}, total: {len(self.tasks)})")

    def add_tasks(self, task_defs: list[dict[str, Any]]) -> None:
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

    def _setup_cluster_servers(self, cluster_models: set) -> set:
        """Start vLLM servers for all cluster models.

        Returns the set of models whose first server failed to come up, so
        the caller can skip tasks that depend on them rather than letting
        them hang on acquire_endpoint() until timeout.

        Budget enforcement is two-layered:
          1. Pre-flight against MAX_SUBMIT_JOBS_PER_USER minus the user's
             existing SLURM jobs (so we don't over-submit when there are
             other jobs queued in the background).
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

        # Wait for the first server of each model in parallel (no serial blocking).
        failed_models = self._wait_for_servers_parallel(cluster_models_sorted)

        if failed_models:
            failed_ids = [m.model_id for m in failed_models]
            logger.warning(
                f"Failed servers: {failed_ids}. Tasks depending on these "
                f"models will be skipped upfront (not hang on acquire).")

        # Register with factory so tasks auto-get endpoints
        LLMServiceFactory.set_server_manager(self._server_manager)
        return failed_models

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
        failed_models: Optional[set] = None,
    ) -> dict[str, Any]:
        """Execute a single task with semaphore-based concurrency control.

        Skips the task upfront (without acquiring a semaphore slot) if any of
        the cluster models it needs is in `failed_models` — there's no point
        running the task only for it to hang on acquire_endpoint().
        """
        # Resolve cluster-model dependencies once so we can both pre-skip on
        # setup failure and decrement remaining counts on completion.
        required_cluster = _required_cluster_models_for_task(task)

        if failed_models and (required_cluster & failed_models):
            blocked = sorted(m.model_id for m in (required_cluster & failed_models))
            err = (
                f"Skipped — depends on cluster model(s) whose server failed "
                f"during setup: {blocked}")
            logger.error(f"[{queue_name}] {err}: {task.name}")
            # Still decrement so mid-run teardown doesn't wait forever.
            for m in required_cluster:
                self._maybe_release_model(m)
            return {
                "task_name": task.name,
                "original_index": task.index,
                "status": "failed",
                "error": err,
                "elapsed_seconds": 0.0,
            }

        async with semaphore:
            logger.info(f"\n{'~'*70}")
            logger.info(f"[{queue_name}] Executing Task {task.index+1}/{total}: {task.name}")
            logger.info(f"{'~'*70}\n")

            t0 = time.time()
            try:
                # Run synchronous task in thread pool
                result = await asyncio.to_thread(run_task, task.config)
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

        failed_models: set = set()

        try:
            # Start vLLM servers for cluster models if needed
            cluster_models = self._find_cluster_models(tasks_to_run)
            if cluster_models:
                model_names = sorted(m.model_id for m in cluster_models)
                logger.info(f"Cluster models detected: {model_names}")
                failed_models = self._setup_cluster_servers(cluster_models)

            logger.info(f"\n{'='*70}")
            logger.info(f"EXPERIMENT: {total} tasks (thread pool: {self.num_main_job_threads}, "
                        f"cluster jobs: {self.num_cluster_jobs})")
            logger.info(f"{'='*70}\n")

            # Thread pool: tasks acquire a slot in order, run, release.
            # failed_models pre-skips tasks whose cluster dependency never came up.
            sem = asyncio.Semaphore(self.num_main_job_threads)
            coroutines = [
                self._run_task_safe(
                    task, sem, task.mode.upper(), total,
                    failed_models=failed_models,
                )
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
    tasks = preset.get("tasks", [])

    # Support both new and legacy key names
    num_threads = preset.get(
        "num_main_job_threads",
        preset.get("num_parallel_workers", 5),
    )
    num_cluster_jobs = preset.get("num_cluster_jobs", MAX_SUBMIT_JOBS_PER_USER)

    exp = Experiment(conf_dir,
                     num_main_job_threads=num_threads,
                     num_cluster_jobs=num_cluster_jobs)
    exp.add_tasks(tasks)
    return exp.run()
