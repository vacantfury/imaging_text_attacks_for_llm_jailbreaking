"""
Experiment orchestrator for Encoding × Modality jailbreaking.

PTP-style multi-queue async scheduling with vLLM server lifecycle:
- API queue: GPT-4o, Gemini, Claude — concurrent (semaphore-limited)
- Cluster queue: LLaVA-NeXT via vLLM servers — per-model semaphores
- Local queue: text_encode, imaging — sequential (no model needed)

All queues run concurrently. Cluster models share vLLM servers.
SLURM usage: 1 orchestrator + N vLLM servers (N = unique cluster models).

Usage:
    exp = Experiment(conf_dir)
    exp.add_tasks(mixed_tasks)
    results = exp.run()
"""
from __future__ import annotations

import asyncio
import traceback
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Set

import yaml

from .task import run_task
from .constants import MAX_PARALLEL_WORKERS, MAX_RUNNING_JOBS_PER_USER
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ==================== Config Loading ====================

def load_preset(name: str, conf_dir: Path = None) -> dict:
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

def _classify_task(task_config: dict) -> str:
    """
    Classify a task into a queue type.
    
    Returns:
        "api"     — cloud API models (GPT-4o, Gemini, Claude)
        "cluster" — models requiring GPU via vLLM (LLaVA-NeXT)
        "local"   — no model needed (text_encode, imaging)
    """
    from src.llm_utils import LLMModel, Provider

    mode = task_config.get("mode", "")
    
    # text_encode and imaging don't query any target model
    if mode in ("text_encode", "imaging"):
        return "local"
    
    # evaluate mode — depends on target model
    model_str = task_config.get("model", "")
    if model_str:
        try:
            model = LLMModel.from_string(model_str)
            if model.provider == Provider.NU_CLUSTER:
                return "cluster"
        except ValueError:
            pass
    return "api"


def _resolve_model(model_str: str):
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
    config: dict
    mode: str
    queue: str        # "api", "cluster", or "local"
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
    Experiment orchestrator with PTP-style multi-queue async scheduling
    and vLLM server lifecycle management.
    
    Tasks are auto-classified into queues:
    - API queue: cloud API tasks, concurrent (semaphore = num_api_workers)
    - Cluster queue: vLLM cluster tasks, per-model semaphores (1 per server instance)
    - Local queue: encoding/imaging, sequential (semaphore = 1)
    
    Cluster models sharing the same LLMModel share vLLM servers.
    Server lifecycle: start_server() → tasks run → shutdown_all()
    
    Usage:
        exp = Experiment(conf_dir, num_api_workers=5)
        exp.add_tasks(mixed_tasks)
        results = exp.run()
    """

    def __init__(self, conf_dir: Path = None,
                 num_api_workers: int = 5,
                 num_cluster_workers: int = MAX_RUNNING_JOBS_PER_USER):
        """
        Args:
            conf_dir: Path to conf/ directory.
            num_api_workers: Max concurrent API tasks.
            num_cluster_workers: Max concurrent cluster tasks (default: NURC limit of 4).
        """
        if conf_dir is None:
            conf_dir = Path(__file__).resolve().parent.parent.parent / "conf"
        self.conf_dir = conf_dir
        self.tasks: deque[TaskInfo] = deque()
        self.results: list[dict[str, Any]] = []
        self.num_api_workers = num_api_workers
        self.num_cluster_workers = num_cluster_workers
        self._task_counter = 0
        self._server_manager = None

    def add_task(self, task_def: dict):
        """Add a task definition (from experiment YAML) to the queue."""
        queue = _classify_task(task_def)
        task_info = TaskInfo(
            index=self._task_counter,
            config=task_def,
            mode=task_def.get("mode", "unknown"),
            queue=queue,
            name=_get_task_name(task_def, self._task_counter),
        )
        self.tasks.append(task_info)
        self._task_counter += 1
        logger.debug(f"Added task '{task_info.name}' → {queue} queue (total: {len(self.tasks)})")

    def add_tasks(self, task_defs: list[dict]):
        """Add multiple task definitions to the queue."""
        for task_def in task_defs:
            self.add_task(task_def)

    # ==================== Cluster Server Management ====================

    def _find_cluster_models(self, tasks: list[TaskInfo]) -> Set:
        """Scan tasks for unique cluster models that need vLLM servers."""
        from src.llm_utils import LLMModel, Provider

        cluster_models = set()
        for task in tasks:
            model_str = task.config.get("model", "")
            if model_str:
                model = _resolve_model(model_str)
                if model and model.provider == Provider.NU_CLUSTER:
                    cluster_models.add(model)
        return cluster_models

    def _load_cluster_config(self, model):
        """
        Load cluster server config for a model.
        
        Merges conf/llm/default.yaml (cluster section) with any model-specific overrides.
        Returns an object with attributes (via SimpleNamespace).
        """
        from types import SimpleNamespace

        # Load default cluster config
        default_yaml = self.conf_dir / "llm" / "default.yaml"
        if default_yaml.exists():
            with open(default_yaml) as f:
                defaults = yaml.safe_load(f) or {}
        else:
            defaults = {}

        cluster_config = defaults.get("cluster", {})

        # Check for model-specific cluster overrides in the model YAML
        # Attempt to find a matching conf/llm/<name>.yaml
        model_name = model.name.lower()
        for yaml_file in (self.conf_dir / "llm").glob("*.yaml"):
            if yaml_file.stem == "default":
                continue
            with open(yaml_file) as f:
                model_yaml = yaml.safe_load(f) or {}
            model_section = model_yaml.get("model", {})
            model_id = model_section.get("model", "")
            if model_id == model.model_id or model_id == model_name:
                # Merge cluster overrides from model YAML
                model_cluster = model_yaml.get("cluster", {})
                cluster_config.update(model_cluster)
                break

        # Add num_instances (default 1, or from cluster config)
        cluster_config.setdefault("num_instances", 1)

        return SimpleNamespace(**cluster_config)

    def _setup_cluster_servers(self, cluster_models: Set) -> None:
        """Start vLLM servers for all cluster models."""
        from src.llm_utils.cluster_server_manager import ClusterModelServerManager
        from src.llm_utils import LLMServiceFactory

        self._server_manager = ClusterModelServerManager()

        for model in cluster_models:
            config = self._load_cluster_config(model)
            logger.info(f"Starting vLLM server(s) for {model.model_id} "
                        f"({config.num_instances} instance(s))...")
            self._server_manager.start_server(model, config)

        # Wait for at least one server per model to be ready
        for model in cluster_models:
            first_endpoint = self._server_manager.wait_for_first_server(model)
            logger.info(f"  → {model.model_id}: first server ready at {first_endpoint}")

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

            try:
                # Run synchronous task in thread pool
                result = await asyncio.to_thread(run_task, task.config)
                result["task_name"] = task.name
                result["original_index"] = task.index
                result["status"] = result.get("status", "success")

                logger.info(f"[{queue_name}] Completed: {task.name}")
                return result
            except Exception as e:
                logger.error(f"[{queue_name}] Failed: {task.name} — {e}")
                logger.error(traceback.format_exc())
                return {
                    "task_name": task.name,
                    "original_index": task.index,
                    "status": "failed",
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }

    async def _run_async(self) -> list[dict[str, Any]]:
        """
        Execute all tasks with multi-queue async scheduling.
        
        API tasks, cluster tasks, and local tasks run concurrently
        in separate queues, each with their own semaphore.
        
        Cluster models: vLLM servers are started before tasks run,
        and shut down after all tasks complete (or on error).
        """
        if not self.tasks:
            logger.warning("No tasks to execute")
            return []

        tasks_to_run = list(self.tasks)
        self.tasks.clear()
        total = len(tasks_to_run)

        # Classify tasks by queue
        api_tasks = [t for t in tasks_to_run if t.queue == "api"]
        cluster_tasks = [t for t in tasks_to_run if t.queue == "cluster"]
        local_tasks = [t for t in tasks_to_run if t.queue == "local"]

        try:
            # Start cluster servers if needed
            model_semaphores: dict = {}  # LLMModel -> asyncio.Semaphore
            if cluster_tasks:
                cluster_models = self._find_cluster_models(cluster_tasks)
                if cluster_models:
                    model_names = [m.model_id for m in cluster_models]
                    logger.info(f"Cluster models detected: {model_names}")
                    self._setup_cluster_servers(cluster_models)

                    # Create per-model semaphores based on instance count
                    for model in cluster_models:
                        n_instances = self._server_manager.get_num_instances(model)
                        model_semaphores[model] = asyncio.Semaphore(n_instances)
                        logger.info(f"  {model.model_id}: {n_instances} worker(s)")

            # Compute total cluster workers for logging
            total_cluster_workers = sum(
                self._server_manager.get_num_instances(m)
                for m in model_semaphores
            ) if model_semaphores else 0

            logger.info(f"\n{'='*70}")
            logger.info(f"EXPERIMENT: {total} tasks")
            logger.info(f"  API tasks:     {len(api_tasks)} (max {self.num_api_workers} concurrent)")
            logger.info(f"  Cluster tasks: {len(cluster_tasks)} ({total_cluster_workers} total workers)")
            logger.info(f"  Local tasks:   {len(local_tasks)} (sequential)")
            logger.info(f"Execution Mode: ASYNC MULTI-QUEUE")
            logger.info(f"{'='*70}\n")

            # Build coroutines per queue
            coroutines = []

            # API queue — concurrent
            api_sem = asyncio.Semaphore(self.num_api_workers)
            for task in api_tasks:
                coroutines.append(self._run_task_safe(task, api_sem, "API", total))

            # Cluster queue — per-model semaphore
            for task in cluster_tasks:
                model_str = task.config.get("model", "")
                model = _resolve_model(model_str)
                if model and model in model_semaphores:
                    sem = model_semaphores[model]
                    queue_name = f"Cluster:{model.model_id.split('/')[-1]}"
                else:
                    # Fallback: single semaphore with 1 worker
                    sem = asyncio.Semaphore(1)
                    queue_name = "Cluster"
                coroutines.append(self._run_task_safe(task, sem, queue_name, total))

            # Local queue — sequential
            local_sem = asyncio.Semaphore(1)
            for task in local_tasks:
                coroutines.append(self._run_task_safe(task, local_sem, "LOCAL", total))

            # Run all queues concurrently
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

        # Aggregate statistics
        total_prompts = sum(
            r.get('count', r.get('num_prompts', 0)) for r in self.results
            if isinstance(r, dict)
        )
        if total_prompts:
            logger.info(f"Total prompts processed: {total_prompts}")

        logger.info(f"{'='*70}\n")

    def __repr__(self) -> str:
        return f"Experiment(tasks={len(self.tasks)}, api={self.num_api_workers}, cluster={self.num_cluster_workers})"


# ==================== Convenience ====================

def run_experiment_from_preset(preset_name: str, conf_dir: Path = None) -> list[dict[str, Any]]:
    """Run an experiment from a preset name."""
    if conf_dir is None:
        conf_dir = Path(__file__).resolve().parent.parent.parent / "conf"
    preset = load_preset(preset_name, conf_dir)
    tasks = preset.get("tasks", [])

    num_api = preset.get("num_api_workers", 5)
    num_cluster = preset.get("num_cluster_workers", MAX_RUNNING_JOBS_PER_USER)

    exp = Experiment(conf_dir, num_api_workers=num_api, num_cluster_workers=num_cluster)
    exp.add_tasks(tasks)
    return exp.run()
