"""
Experiment orchestrator for Encoding × Modality jailbreaking.

PTP-style multi-queue async scheduling:
- API queue: GPT-4o, Gemini, Claude — concurrent (semaphore-limited)
- Cluster queue: LLaVA-NeXT via vLLM servers on SLURM — concurrent (server-limited)
- Local queue: text_encode, imaging — sequential (no model needed)

All queues run concurrently. Total SLURM job concurrency respects
NURC cluster limits (MAX_SUBMIT_JOBS_PER_USER = 8).

Usage:
    exp = Experiment(conf_dir)
    exp.add_tasks(mixed_tasks)
    results = exp.run()
"""
from __future__ import annotations

import asyncio
import threading
import traceback
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from .task import run_task
from .constants import MAX_PARALLEL_WORKERS, MAX_RUNNING_JOBS_PER_USER
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Models that require cluster GPU (vLLM serving)
CLUSTER_MODELS = {"llava-next", "llama-guard-3"}

# Models served by cloud APIs
API_MODELS = {"gpt-4o", "gpt-4o-mini", "gpt-5-nano", "gemini-2.5-pro",
              "claude-sonnet-4-20250514"}


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
    mode = task_config.get("mode", "")
    
    # text_encode and imaging don't query any model (or use helper LLM via API)
    if mode in ("text_encode", "imaging"):
        return "local"
    
    # evaluate mode — depends on target model
    model = task_config.get("model", "")
    if model in CLUSTER_MODELS:
        return "cluster"
    return "api"


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
    Experiment orchestrator with PTP-style multi-queue async scheduling.
    
    Tasks are auto-classified into queues:
    - API queue: cloud API tasks, concurrent (semaphore = num_api_workers)
    - Cluster queue: vLLM cluster tasks, concurrent (semaphore = num_cluster_workers)
    - Local queue: encoding/imaging, sequential (semaphore = 1)
    
    All three queues run concurrently, each with their own semaphore.
    
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

        logger.info(f"\n{'='*70}")
        logger.info(f"EXPERIMENT: {total} tasks")
        logger.info(f"  API tasks:     {len(api_tasks)} (max {self.num_api_workers} concurrent)")
        logger.info(f"  Cluster tasks: {len(cluster_tasks)} (max {self.num_cluster_workers} concurrent)")
        logger.info(f"  Local tasks:   {len(local_tasks)} (sequential)")
        logger.info(f"{'='*70}\n")

        # Build coroutines per queue
        coroutines = []

        # API queue — concurrent
        api_sem = asyncio.Semaphore(self.num_api_workers)
        for task in api_tasks:
            coroutines.append(self._run_task_safe(task, api_sem, "API", total))

        # Cluster queue — concurrent, limited by cluster running limit
        cluster_sem = asyncio.Semaphore(self.num_cluster_workers)
        for task in cluster_tasks:
            coroutines.append(self._run_task_safe(task, cluster_sem, "CLUSTER", total))

        # Local queue — sequential
        local_sem = asyncio.Semaphore(1)
        for task in local_tasks:
            coroutines.append(self._run_task_safe(task, local_sem, "LOCAL", total))

        # Run all queues concurrently
        self.results = list(await asyncio.gather(*coroutines))
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
