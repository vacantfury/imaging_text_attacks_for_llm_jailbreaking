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
        """Scan tasks for unique cluster models that need vLLM servers."""
        cluster_models = set()
        for task in tasks:
            if task.task_type == TaskType.CLUSTER_MODEL:
                model = _resolve_model(task.config.get("model", ""))
                if model:
                    cluster_models.add(model)
        return cluster_models

    def _load_cluster_config(self, model):
        """
        Load cluster server config for a model.
        
        Uses the shared _load_conf helper: merges conf/llm/default.yaml
        with any model-specific overrides, returns the 'cluster' section.
        """
        from .config import load_conf
        
        cluster_config = load_conf(
            "llm", section="cluster",
            match_field="model.model", match_value=model.model_id)
        
        cluster_config.setdefault("num_instances", 1)

        return cluster_config

    def _setup_cluster_servers(self, cluster_models: set) -> None:
        """Start vLLM servers for all cluster models.
        
        Enforces num_cluster_jobs budget: total vLLM server instances across
        all models cannot exceed (num_cluster_jobs - 1), since the orchestrator
        itself occupies one SLURM slot.
        
        Fault-tolerant: if a server fails, tasks using that model will fail
        individually without blocking other tasks.
        """
        from src.llm_utils.cluster_server_manager import ClusterModelServerManager
        from src.llm_utils import LLMServiceFactory

        self._server_manager = ClusterModelServerManager()

        # Load configs and enforce SLURM job budget
        model_configs = {}
        for model in cluster_models:
            model_configs[model] = self._load_cluster_config(model)

        available_slots = self.num_cluster_jobs - 1  # 1 reserved for orchestrator
        total_requested = sum(
            cfg.get("num_instances", 1) for cfg in model_configs.values()
        )

        if total_requested > available_slots:
            logger.warning(
                f"Requested {total_requested} vLLM server instances but only "
                f"{available_slots} SLURM slots available (num_cluster_jobs="
                f"{self.num_cluster_jobs}, 1 for orchestrator). "
                f"Capping instances proportionally.")
            n_models = len(model_configs)
            per_model = max(available_slots // n_models, 1)
            for cfg in model_configs.values():
                cfg["num_instances"] = per_model
            logger.info(f"Adjusted to {per_model} instance(s) per model "
                        f"({per_model * n_models} total)")

        for i, model in enumerate(cluster_models):
            config = model_configs[model]
            num_instances = config.get("num_instances", 1)
            config["port"] = config["port"] + i * num_instances
            logger.info(f"Starting vLLM server(s) for {model.model_id} "
                        f"({config['num_instances']} instance(s), port {config['port']})...")
            self._server_manager.start_server(model, config)

        # Wait for at least one server per model to be ready
        failed_models = []
        for model in cluster_models:
            try:
                first_endpoint = self._server_manager.wait_for_first_server(model)
                logger.info(f"  → {model.model_id}: first server ready at {first_endpoint}")
            except RuntimeError as e:
                logger.error(f"  ✗ {model.model_id}: server failed — {e}")
                failed_models.append(model.model_id)

        if failed_models:
            logger.warning(f"Failed servers: {failed_models}. "
                           f"Tasks using these models will fail individually.")

        # Register with factory so tasks auto-get endpoints
        LLMServiceFactory.set_server_manager(self._server_manager)

    def _teardown_cluster_servers(self) -> None:
        """Shut down all vLLM servers."""
        if self._server_manager:
            logger.info("Shutting down cluster vLLM servers...")
            self._server_manager.shutdown_all()
            self._server_manager = None

    # ==================== Async Execution ====================

    async def _run_task_safe(self, task: TaskInfo, semaphore: asyncio.Semaphore,
                             queue_name: str, total: int) -> dict[str, Any]:
        """Execute a single task with semaphore-based concurrency control."""
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
                logger.error(f"[{queue_name}] Failed: {task.name} ({elapsed:.1f}s) — {e}")
                logger.error(traceback.format_exc())
                return {
                    "task_name": task.name,
                    "original_index": task.index,
                    "status": "failed",
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "elapsed_seconds": round(elapsed, 1),
                }

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

        try:
            # Start vLLM servers for cluster models if needed
            cluster_models = self._find_cluster_models(tasks_to_run)
            if cluster_models:
                model_names = [m.model_id for m in cluster_models]
                logger.info(f"Cluster models detected: {model_names}")
                self._setup_cluster_servers(cluster_models)

            logger.info(f"\n{'='*70}")
            logger.info(f"EXPERIMENT: {total} tasks (thread pool: {self.num_main_job_threads}, "
                        f"cluster jobs: {self.num_cluster_jobs})")
            logger.info(f"{'='*70}\n")

            # Thread pool: tasks acquire a slot in order, run, release
            sem = asyncio.Semaphore(self.num_main_job_threads)
            coroutines = [
                self._run_task_safe(task, sem, task.mode.upper(), total)
                for task in tasks_to_run
            ]

            self.results = list(await asyncio.gather(*coroutines))

        finally:
            # Always shut down cluster servers, even on error
            self._teardown_cluster_servers()

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
