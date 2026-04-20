"""
Experiment orchestrator for PTP.

Manages parallel execution of multiple tasks with multi-queue scheduling:
- API queue: tasks using cloud providers (OpenAI, Anthropic, Google) — high concurrency
- Cluster queue: per-model sub-queues with concurrency matching server instances
- Local queue: sequential (single GPU constraint)

Based on asyncio with semaphore-per-queue for fine-grained concurrency control.
"""
import asyncio
import threading
import traceback
from typing import Any, Optional
from collections import deque
from dataclasses import dataclass

from .config import ExperimentConfig
from src.llm_utils.llm_model import LLMModel, Provider
from .task import run_task
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Provider categories
API_PROVIDERS = {Provider.OPENAI, Provider.ANTHROPIC, Provider.GOOGLE}
LOCAL_PROVIDERS = {Provider.LOCAL}
CLUSTER_PROVIDERS = {Provider.NU_CLUSTER}


@dataclass
class TaskInfo:
    """Task metadata for scheduling."""
    index: int
    config: dict
    provider: str
    model: str
    name: str

    @property
    def requires_cluster(self) -> bool:
        """True if this task uses a local/cluster GPU provider."""
        return self.provider in {p.value for p in (CLUSTER_PROVIDERS | LOCAL_PROVIDERS)}


def _get_provider(task_config: dict) -> Optional[Provider]:
    """Extract provider from task config."""
    # Hydra path: llm.model; legacy path: llm_config.model
    model_str = task_config.get("model", {}).get("model", "") or task_config.get("llm_config", {}).get("model", "")
    if not model_str:
        return None
    try:
        return LLMModel.from_string(model_str).provider
    except (ValueError, AttributeError):
        return None


def _get_task_name(task_config: dict, index: int) -> str:
    """Generate a descriptive name for a task."""
    mode = task_config.get("mode", "unknown")
    dataset = (task_config.get("data_loader", {}).get("name")
               or task_config.get("data_loader_config", {}).get("name", "unknown"))
    model = (task_config.get("model", {}).get("model")
             or task_config.get("llm_config", {}).get("model", "default"))
    return f"{mode}_{dataset}_{model}_{index}"


def _extract_provider_model(task_config: dict) -> tuple[str, str]:
    """Extract provider string and model string from task config."""
    # Hydra path: llm.model; legacy path: llm_config.model
    model_str = task_config.get("model", {}).get("model", "") or task_config.get("llm_config", {}).get("model", "default")
    try:
        llm_model = LLMModel.from_string(model_str)
        return llm_model.provider.value, llm_model.model_id
    except (ValueError, AttributeError):
        return "unknown", str(model_str)


class Experiment:
    """
    Experiment orchestrator with multi-queue async scheduling.
    
    Tasks are auto-classified into queues:
    - API queue: cloud API tasks, high concurrency (semaphore = num_api_workers)
    - Cluster queue: per-model sub-queues matching server instance count
    - Local queue: sequential (semaphore = 1)
    
    Usage:
        exp = Experiment(num_api_workers=8)
        exp.add_task(task_config_1)
        exp.add_task(task_config_2)
        results = exp.run()
    """
    
    def __init__(self, num_api_workers: int = 5,
                 num_cluster_workers: Optional[int] = None):
        """
        Initialize the experiment.
        
        Args:
            num_api_workers: Max concurrent API tasks.
            num_cluster_workers: Number of vLLM server instances per model.
                Each server exclusively serves one task at a time.
                If None, uses the default from YAML config.
        """
        self.tasks: deque[TaskInfo] = deque()
        self.results: list[dict[str, Any]] = []
        self.num_api_workers = num_api_workers
        self.num_cluster_workers = num_cluster_workers
        self._server_manager = None
        self._task_counter = 0  # Auto-incrementing task index
    
    def add_task(self, task_config: dict):
        """Add a task config dict to the execution queue."""
        provider, model = _extract_provider_model(task_config)
        task_info = TaskInfo(
            index=self._task_counter,
            config=task_config,
            provider=provider,
            model=model,
            name=_get_task_name(task_config, self._task_counter),
        )
        self.tasks.append(task_info)
        self._task_counter += 1
        logger.debug(f"Added task '{task_info.name}' (total: {len(self.tasks)})")
    
    def add_tasks(self, task_configs: list[dict]):
        """Add multiple task config dicts to the queue."""
        for config in task_configs:
            self.add_task(config)
    
    # ==================== Cluster Server Lifecycle ====================
    
    def _find_cluster_models(self, tasks: list[TaskInfo]) -> set:
        """Scan tasks for cluster models that need vLLM servers."""
        cluster_models = set()
        for task in tasks:
            if task.provider in {p.value for p in CLUSTER_PROVIDERS}:
                try:
                    llm_model = LLMModel.from_string(task.model)
                    cluster_models.add(llm_model)
                except ValueError:
                    pass
        return cluster_models
    
    def _setup_cluster_servers(self, cluster_models: set, cluster_tasks: list) -> None:
        """Start vLLM servers for all cluster models.
        
        Builds cluster config DictConfig from Hydra YAML (the 'cluster' section in
        each task's llm config) and caps num_instances to the actual task count.
        """
        from src.llm_utils.cluster_server_manager import ClusterModelServerManager
        from src.llm_utils.llm_service_factory import LLMServiceFactory
        from omegaconf import OmegaConf
        
        # Count tasks per model and collect their configs
        from collections import Counter
        tasks_per_model = Counter()
        model_task_cfg = {}  # model -> first task's full config dict
        for task in cluster_tasks:
            try:
                llm_model = LLMModel.from_string(task.model)
                tasks_per_model[llm_model] += 1
                if llm_model not in model_task_cfg:
                    model_task_cfg[llm_model] = task.config
            except ValueError:
                pass
        
        self._server_manager = ClusterModelServerManager()
        
        for model in cluster_models:
            # Cap instances: don't launch more servers than tasks
            num_tasks = tasks_per_model.get(model, 1)
            num_instances = num_tasks
            if self.num_cluster_workers is not None:
                num_instances = min(self.num_cluster_workers, num_tasks)
            
            # Build cluster config from YAML's top-level 'cluster' section
            task_cfg = model_task_cfg.get(model, {})
            cluster_data = dict(task_cfg.get("cluster", {}))
            cluster_data["num_instances"] = num_instances
            config = OmegaConf.create(cluster_data)
            
            logger.info(f"Starting vLLM server(s) for {model.model_id}...")
            self._server_manager.start_server(model, config)  # Non-blocking
            
            # Wait for at least one server to be ready before starting tasks
            self._server_manager.wait_for_first_server(
                model, timeout=config.server_start_timeout
            )
            logger.info(f"  {model.model_id}: {self._server_manager.get_num_ready(model)} server(s) ready, "
                        f"{num_instances} submitted")
        
        # Register with factory so tasks get server_manager reference
        LLMServiceFactory.set_server_manager(self._server_manager)
    
    def _teardown_cluster_servers(self) -> None:
        """Shut down all vLLM servers."""
        if self._server_manager:
            logger.info("Shutting down cluster vLLM servers...")
            self._server_manager.shutdown_all()
            self._server_manager = None
    
    # ==================== Task Execution ====================
    
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
                result["status"] = "success"
                
                eval_results = result.get("evaluation", {})
                accuracy = eval_results.get("accuracy", "N/A")
                if isinstance(accuracy, float):
                    logger.info(f"[{queue_name}] Completed: {task.name} — {accuracy:.2%}")
                else:
                    logger.info(f"[{queue_name}] Completed: {task.name} — {accuracy}")
                
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
        
        API tasks and cluster tasks run concurrently in separate queues,
        each with their own semaphore for concurrency control.
        """
        if not self.tasks:
            logger.warning("No tasks to execute")
            return []
        
        tasks_to_run = list(self.tasks)
        self.tasks.clear()
        total = len(tasks_to_run)
        
        # Classify tasks
        api_tasks = [t for t in tasks_to_run if t.provider in {p.value for p in API_PROVIDERS}]
        cluster_tasks = [t for t in tasks_to_run if t.provider in {p.value for p in CLUSTER_PROVIDERS}]
        local_tasks = [t for t in tasks_to_run if t.provider in {p.value for p in LOCAL_PROVIDERS}]
        
        self.results = []
        
        # Fix tqdm thread-safety: initialize lock before concurrent data loading
        from tqdm import tqdm
        tqdm.set_lock(threading.RLock())
        
        try:
            # Setup cluster servers if needed (non-blocking — waits only for first server)
            total_cluster_workers = 0
            if cluster_tasks:
                cluster_models = self._find_cluster_models(cluster_tasks)
                if cluster_models:
                    model_names = [m.model_id for m in cluster_models]
                    logger.info(f"Cluster models detected: {model_names}")
                    self._setup_cluster_servers(cluster_models, cluster_tasks)
                    
                    total_cluster_workers = sum(
                        self._server_manager.get_num_instances(m)
                        for m in cluster_models
                    )
            
            logger.info(f"\n{'='*70}")
            logger.info(f"EXPERIMENT: {total} tasks")
            logger.info(f"  API tasks: {len(api_tasks)} (max {self.num_api_workers} concurrent)")
            logger.info(f"  Cluster tasks: {len(cluster_tasks)} ({total_cluster_workers} workers submitted)")
            logger.info(f"  Local tasks: {len(local_tasks)} (sequential)")
            logger.info(f"{'='*70}\n")
            
            # Build coroutines
            coroutines = []
            
            # API tasks — single shared semaphore
            api_semaphore = asyncio.Semaphore(self.num_api_workers)
            for task in api_tasks:
                coroutines.append(
                    self._run_task_safe(task, api_semaphore, f"API:{task.provider}", total)
                )
            
            # Cluster tasks — concurrency controlled by pool acquire/release
            # Use num_instances as semaphore to cap concurrent tasks
            cluster_semaphore = asyncio.Semaphore(max(total_cluster_workers, 1))
            for task in cluster_tasks:
                coroutines.append(
                    self._run_task_safe(task, cluster_semaphore, "Cluster", total)
                )
            
            # Local tasks — sequential (semaphore = 1)
            local_semaphore = asyncio.Semaphore(1)
            for task in local_tasks:
                coroutines.append(
                    self._run_task_safe(task, local_semaphore, "LOCAL", total)
                )
            
            # Run all queues concurrently
            self.results = list(await asyncio.gather(*coroutines))
        
        finally:
            self._teardown_cluster_servers()
        
        self._print_summary()
        return self.results
    
    def run(self, num_of_tasks: Optional[int] = None) -> list[dict[str, Any]]:
        """
        Execute tasks (sync entry point).
        
        Args:
            num_of_tasks: Max tasks to run. None = all.
        
        Returns:
            List of task result dicts.
        """
        if num_of_tasks is not None:
            # Only keep the first N tasks
            keep = min(num_of_tasks, len(self.tasks))
            self.tasks = deque(list(self.tasks)[:keep])
        
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
        return f"Experiment(tasks={len(self.tasks)}, api_workers={self.num_api_workers})"


# ==================== Legacy Functions ====================

def run_experiment(config_path: str) -> list[dict[str, Any]]:
    """
    Run an experiment from a JSON config file (legacy compatibility).
    
    Args:
        config_path: Path to JSON config file.
    
    Returns:
        List of task result dicts.
    """
    import json
    
    logger.info(f"Loading experiment config from: {config_path}")
    with open(config_path, "r") as f:
        config = json.load(f)
    
    num_workers = config.get("num_workers", 5)
    tasks = config.get("tasks", [])
    
    exp = Experiment(num_api_workers=num_workers)
    exp.add_tasks(tasks)
    return exp.run()


def run_experiment_from_cfg(cfg) -> list[dict[str, Any]]:
    """
    Run an experiment from a Hydra/OmegaConf DictConfig.
    
    Args:
        cfg: OmegaConf DictConfig with num_workers and experiment.tasks.
    
    Returns:
        List of task result dicts.
    """
    
    
    num_workers = cfg.get("num_workers", 5)
    experiment_cfg = cfg.get("experiment", cfg)
    tasks_cfg = experiment_cfg.get("tasks", [])
    tasks = list(tasks_cfg)
    
    exp = Experiment(num_api_workers=num_workers)
    exp.add_tasks(tasks)
    return exp.run()
