"""
Manages vLLM server lifecycle on SLURM cluster.

Handles:
- Auto-generating sbatch scripts for vLLM servers
- Submitting SLURM jobs and tracking their IDs
- Discovering endpoints via scontrol (no shared files needed)
- Multi-instance support: N servers per model on different ports
- Dynamic server pool with acquire/release endpoint allocation
- Background monitoring: servers are added to the pool as they become healthy
"""
import os
import re
import subprocess
import tempfile
import time
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from src.llm_utils.llm_model import LLMModel, Provider
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ClusterModelServerManager:
    """
    Manages vLLM server lifecycle on SLURM cluster with dynamic endpoint pool.
    
    Supports multiple server instances per model for parallel task execution.
    Each instance gets its own SLURM job, GPU, and port.
    
    Servers are added to the pool dynamically as they become healthy.
    Tasks acquire/release endpoints — no blocking on all servers at startup.
    
    Usage:
        manager = ClusterModelServerManager()
        manager.start_server(LLMModel.PIXTRAL_12B, config)  # returns immediately
        
        endpoint = manager.acquire_endpoint(model)  # blocks until one is available
        # ... use endpoint ...
        manager.release_endpoint(model, endpoint)
        
        manager.shutdown_all()
    """
    
    def __init__(self):
        """Initialize the manager."""
        # SLURM job tracking: model -> list of {job_id, port, instance_id}
        self._jobs: Dict[LLMModel, List[dict]] = {}
        
        # Dynamic endpoint pool: model -> list of {endpoint, is_available, job_id}
        self._pool: Dict[LLMModel, List[dict]] = {}
        self._pool_lock = threading.Lock()
        self._pool_changed = threading.Event()  # signals new endpoint or release
        
        # Store config per model
        self.model_configs: Dict[LLMModel, Any] = {}
        
        # Monitor thread control
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitor = threading.Event()
        
        self._sbatch_dir = Path(tempfile.mkdtemp(prefix="vllm_sbatch_"))
    
    def start_server(self, model: LLMModel, config: Any) -> None:
        """
        Start vLLM server(s) for the given model.
        
        Submits SLURM jobs and starts a background monitor thread.
        Returns immediately — does NOT wait for servers to be healthy.
        Servers are added to the pool by the monitor thread as they come up.
        
        Args:
            model: The cluster model to serve.
            config: Fully populated Any (from YAML).
        """
        if model in self._jobs and self._jobs[model]:
            logger.info(f"Servers already submitted for {model.model_id}")
            return
        
        if model.provider != Provider.NU_CLUSTER:
            raise ValueError(f"{model.model_id} is not a cluster model (provider: {model.provider})")
        
        # Store config for later lookups
        self.model_configs[model] = config
        
        num_instances = config.num_instances
        base_port = config.port
        
        logger.info(f"Starting {num_instances} vLLM server(s) for {model.model_id} "
                     f"(ports {base_port}-{base_port + num_instances - 1})")
        
        # Initialize tracking
        self._jobs[model] = []
        self._pool[model] = []
        
        # Submit N sbatch jobs
        for i in range(num_instances):
            instance_port = base_port + i
            from omegaconf import OmegaConf
            instance_config = OmegaConf.merge(config, {"port": instance_port})
            
            sbatch_path = self._generate_sbatch(model, instance_config, instance_id=i)
            job_id = self._submit_sbatch(sbatch_path)
            
            self._jobs[model].append({
                "job_id": job_id,
                "port": instance_port,
                "instance_id": i,
                "discovered": False,  # True once added to pool
            })
            logger.info(f"  Instance {i}: SLURM job {job_id}, port {instance_port}")
        
        # Start monitor thread (if not already running)
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._stop_monitor.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="vllm-pool-monitor",
            )
            self._monitor_thread.start()
            logger.info("Started background server monitor thread")
    
    def _monitor_loop(self) -> None:
        """
        Background thread that polls SLURM jobs and adds healthy endpoints to the pool.
        
        Runs until _stop_monitor is set or all jobs are discovered/failed.
        """
        poll_interval = 10  # seconds
        
        while not self._stop_monitor.is_set():
            all_done = True
            
            for model, jobs in self._jobs.items():
                config = self.model_configs[model]
                
                for job_info in jobs:
                    if job_info["discovered"]:
                        continue
                    
                    all_done = False
                    job_id = job_info["job_id"]
                    port = job_info["port"]
                    instance_id = job_info["instance_id"]
                    instance_suffix = f"[{instance_id}]" if instance_id > 0 else ""
                    
                    # Check SLURM state
                    state = self._get_job_state(job_id)
                    
                    if state is None:
                        # Job disappeared from queue — it failed
                        model_safe_name = model.name.lower()
                        logger.warning(
                            f"Server{instance_suffix} (job {job_id}) failed. "
                            f"Check logs/vllm_{model_safe_name}_*.err"
                        )
                        job_info["discovered"] = True  # Mark so we stop checking
                        continue
                    
                    if state == "PENDING":
                        continue  # Still waiting for resources
                    
                    # RUNNING — try to discover endpoint
                    node = self._discover_node(job_id)
                    if not node:
                        continue
                    
                    endpoint = f"http://{node}:{port}/v1"
                    healthy, err = self._health_check(endpoint)
                    
                    if healthy:
                        with self._pool_lock:
                            self._pool[model].append({
                                "endpoint": endpoint,
                                "is_available": True,
                                "job_id": job_id,
                            })
                        job_info["discovered"] = True
                        logger.info(f"Server{instance_suffix} ready at {endpoint} "
                                   f"(pool size: {len(self._pool[model])})")
                        self._pool_changed.set()  # Wake up acquire_endpoint waiters
            
            if all_done:
                logger.info("All server jobs resolved, monitor stopping")
                break
            
            self._stop_monitor.wait(timeout=poll_interval)
    
    def _discover_node(self, job_id: str) -> Optional[str]:
        """Get the node hostname/IP for a running SLURM job."""
        try:
            sq_result = subprocess.run(
                ["squeue", "-j", job_id, "--noheader", "--format=%N"],
                capture_output=True, text=True, timeout=15
            )
            node_name = sq_result.stdout.strip()
        except Exception:
            return None
        
        if not node_name or node_name == "(null)":
            return None
        
        # Try to resolve to IP
        node = self._get_job_node(job_id)
        return node if node else node_name
    
    def acquire_endpoint(self, model: LLMModel, timeout: int = None) -> str:
        """
        Acquire an available endpoint from the pool.
        
        Blocks until one is available. Marks it as busy.
        
        Args:
            model: The cluster model.
            timeout: Max seconds to wait for an available endpoint.
            
        Returns:
            Endpoint URL string.
            
        Raises:
            RuntimeError: If no endpoint becomes available within timeout.
        """
        config = self.model_configs.get(model)
        wait_interval = config.endpoint_wait_timeout if config else 30
        if timeout is None:
            timeout = getattr(config, "cluster_server_endpoint_timeout", 10000) if config else 10000
        deadline = time.time() + timeout
        
        while time.time() < deadline:
            with self._pool_lock:
                for entry in self._pool.get(model, []):
                    if entry["is_available"]:
                        entry["is_available"] = False
                        logger.debug(f"Acquired endpoint {entry['endpoint']}")
                        return entry["endpoint"]
            
            # No endpoint available — wait for pool change
            remaining = deadline - time.time()
            wait_time = min(wait_interval, max(remaining, 0))
            if wait_time <= 0:
                break
            self._pool_changed.wait(timeout=wait_time)
            self._pool_changed.clear()
        
        raise RuntimeError(
            f"No endpoint available for {model.model_id} within {timeout}s. "
            f"Pool has {len(self._pool.get(model, []))} server(s), "
            f"all busy or none started."
        )
    
    def release_endpoint(self, model: LLMModel, endpoint: str) -> None:
        """
        Release an endpoint back to the pool, marking it as available.
        
        Args:
            model: The cluster model.
            endpoint: The endpoint URL to release.
        """
        with self._pool_lock:
            for entry in self._pool.get(model, []):
                if entry["endpoint"] == endpoint:
                    entry["is_available"] = True
                    logger.debug(f"Released endpoint {endpoint}")
                    break
        self._pool_changed.set()  # Wake up anyone waiting in acquire_endpoint
    
    def get_num_instances(self, model: LLMModel) -> int:
        """
        Get the number of submitted server instances for a model.
        
        Returns:
            Number of submitted jobs (0 if not started).
        """
        return len(self._jobs.get(model, []))
    
    def get_num_ready(self, model: LLMModel) -> int:
        """
        Get the number of healthy, pool-registered endpoints for a model.
        
        Returns:
            Number of endpoints in the pool.
        """
        with self._pool_lock:
            return len(self._pool.get(model, []))
    
    def wait_for_first_server(self, model: LLMModel, timeout: int = 3600) -> str:
        """
        Block until at least one server for the model is in the pool.
        
        Used by experiment setup to ensure at least one server is ready
        before starting tasks. This is the ONLY blocking call.
        
        Args:
            model: The cluster model.
            timeout: Max seconds to wait.
            
        Returns:
            The first available endpoint URL.
            
        Raises:
            RuntimeError: If no server comes up within timeout.
        """
        deadline = time.time() + timeout
        logger.info(f"Waiting for first server for {model.model_id} (timeout: {timeout}s)...")
        
        while time.time() < deadline:
            with self._pool_lock:
                if self._pool.get(model):
                    first_endpoint = self._pool[model][0]["endpoint"]
                    logger.info(f"First server ready: {first_endpoint}")
                    return first_endpoint
            
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            self._pool_changed.wait(timeout=min(10, remaining))
            self._pool_changed.clear()
        
        raise RuntimeError(
            f"No server for {model.model_id} became ready within {timeout}s. "
            f"Check SLURM logs."
        )
    
    def get_server_status(self, model: LLMModel) -> Dict[str, Any]:
        """
        Get the current lifecycle status of servers for a model.
        
        Returns:
            Dict with state, job_ids, endpoints, pool info.
        """
        status: Dict[str, Any] = {
            "state": "not_started",
            "job_ids": [],
            "endpoints": [],
            "num_submitted": 0,
            "num_ready": 0,
            "num_available": 0,
        }
        
        if model not in self._jobs:
            return status
        
        jobs = self._jobs[model]
        status["job_ids"] = [j["job_id"] for j in jobs]
        status["num_submitted"] = len(jobs)
        
        with self._pool_lock:
            pool = self._pool.get(model, [])
            status["num_ready"] = len(pool)
            status["num_available"] = sum(1 for e in pool if e["is_available"])
            status["endpoints"] = [e["endpoint"] for e in pool]
        
        if status["num_ready"] == 0:
            status["state"] = "pending"
        elif status["num_ready"] < status["num_submitted"]:
            status["state"] = "partially_ready"
        else:
            status["state"] = "ready"
        
        return status
    
    def shutdown_all(self):
        """Cancel all active SLURM jobs and clean up."""
        # Stop monitor thread
        self._stop_monitor.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        
        # Cancel all SLURM jobs
        for model, jobs in self._jobs.items():
            for job_info in jobs:
                job_id = job_info["job_id"]
                logger.info(f"Cancelling SLURM job {job_id} ({model.model_id})")
                try:
                    subprocess.run(
                        ["scancel", job_id],
                        capture_output=True, timeout=10
                    )
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    logger.warning(f"Could not cancel job {job_id}")
        
        self._jobs.clear()
        with self._pool_lock:
            self._pool.clear()
        self._pool_changed.set()  # Wake up any waiters so they can fail
        logger.info("All vLLM servers shut down")
    
    def __del__(self):
        """Ensure cleanup on garbage collection."""
        if self._jobs:
            self.shutdown_all()
    
    # ==================== SLURM Helpers (unchanged) ====================
    
    def _find_available_gpu(self, config: Any) -> str:
        """
        Find the first available GPU type from the preference list.
        
        Checks `sinfo` for idle/mixed nodes with each preferred GPU type,
        skipping any in the exclude list.
        """
        excluded = set(config.gpu_types_excluded)
        candidates = [g for g in config.gpu_types_preferred if g not in excluded]
        
        if not candidates:
            raise RuntimeError(
                f"No GPU candidates after filtering. "
                f"Preferred: {config.gpu_types_preferred}, Excluded: {config.gpu_types_excluded}"
            )
        
        for gpu_type in candidates:
            try:
                result = subprocess.run(
                    [
                        "sinfo", "-p", config.partition,
                        "--gres=gpu:" + gpu_type,
                        "--states=idle,mixed",
                        "--noheader",
                        "--format=%n"
                    ],
                    capture_output=True, text=True, timeout=10
                )
                nodes = result.stdout.strip()
                if nodes:
                    available_count = len(nodes.splitlines())
                    logger.info(f"GPU {gpu_type}: {available_count} nodes available")
                    return gpu_type
                else:
                    logger.debug(f"GPU {gpu_type}: no idle/mixed nodes")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.warning(f"Could not check sinfo for {gpu_type}, skipping")
                continue
        
        # Fallback: use first preferred type and let SLURM queue
        fallback = candidates[0]
        logger.warning(
            f"No GPU type immediately available. Falling back to '{fallback}' "
            f"(job will queue until a node is free)"
        )
        return fallback
    
    def _generate_sbatch(
        self, model: LLMModel, config: Any,
        instance_id: int = 0
    ) -> Path:
        """Generate sbatch script for a vLLM server instance."""
        model_safe_name = model.name.lower()
        instance_suffix = f"_i{instance_id}" if instance_id > 0 else ""
        
        # Build vLLM serve command
        vllm_args = [
            f"--model {model.model_id}",
            f"--host 0.0.0.0",
            f"--port {config.port}",
            f"--gpu-memory-utilization {config.gpu_memory_utilization}",
            f"--max-model-len {config.max_model_len}",
        ]
        if config.dtype:
            vllm_args.append(f"--dtype {config.dtype}")
        if config.num_gpus > 1:
            vllm_args.append(f"--tensor-parallel-size {config.num_gpus}")
        if config.chat_template:
            chat_template_dir = Path(__file__).parent / "chat_templates"
            template_file = chat_template_dir / f"{config.chat_template}.jinja"
            if template_file.exists():
                vllm_args.append(f"--chat-template {template_file.resolve()}")
                logger.info(f"Using chat template: {template_file.resolve()}")
            else:
                logger.warning(f"Chat template not found: {template_file}. vLLM will use model default.")
        vllm_cmd = "python -m vllm.entrypoints.openai.api_server \\\n    " + " \\\n    ".join(vllm_args)
        
        script = f"""#!/bin/bash
#SBATCH --job-name=vllm_{model_safe_name}{instance_suffix}
#SBATCH --partition={config.partition}
#SBATCH --nodes=1
#SBATCH --gres=gpu:{config.num_gpus}
#SBATCH --cpus-per-task={config.cpus_per_task}
#SBATCH --mem={config.mem_gb}GB
#SBATCH --time={config.time_limit}
#SBATCH --output=logs/vllm_{model_safe_name}{instance_suffix}_%j.out
#SBATCH --error=logs/vllm_{model_safe_name}{instance_suffix}_%j.err

# Setup environment
mkdir -p logs
module load anaconda3/2024.06 {config.cuda_module}
source activate {config.conda_env}

# Use shared HF cache (models pre-downloaded on login node)
# Compute nodes have no internet — must run fully offline
export HF_HOME="${{HF_HOME:-{config.hf_home}}}"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

# Start vLLM server (blocks until killed by scancel or time limit)
{vllm_cmd}
"""
        
        sbatch_path = self._sbatch_dir / f"vllm_{model_safe_name}{instance_suffix}.sbatch"
        sbatch_path.write_text(script)
        logger.debug(f"Generated sbatch at {sbatch_path}")
        return sbatch_path
    
    def _submit_sbatch(self, sbatch_path: Path) -> str:
        """Submit sbatch script and return the SLURM job ID."""
        try:
            result = subprocess.run(
                ["sbatch", str(sbatch_path)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                raise RuntimeError(f"sbatch failed: {result.stderr.strip()}")
            
            output = result.stdout.strip()
            job_id = output.split()[-1]
            return job_id
            
        except FileNotFoundError:
            raise RuntimeError(
                "sbatch command not found. "
                "Are you running this on the cluster login node?"
            )
    
    def _get_job_node(self, job_id: str) -> Optional[str]:
        """
        Get the IP address of the node running a SLURM job.
        
        Uses `scontrol show job` to get the NodeList, then
        `scontrol show node` to resolve to an IP address.
        """
        try:
            result = subprocess.run(
                ["scontrol", "show", "job", job_id],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode != 0:
                logger.warning(f"scontrol show job {job_id} failed: rc={result.returncode}, stderr={result.stderr[:200]}")
                return None
            
            match = re.search(r"NodeList=(\S+)", result.stdout)
            if not match:
                logger.warning(f"No NodeList found in scontrol output for job {job_id}")
                return None
            node = match.group(1)
            if not node or node == "(null)":
                return None
            
            # Resolve node name to IP via scontrol show node
            result = subprocess.run(
                ["scontrol", "show", "node", node],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode != 0:
                logger.warning(f"scontrol show node {node} failed: rc={result.returncode}")
                return node  # Fallback to hostname
            
            addr_match = re.search(r"NodeAddr=(\S+)", result.stdout)
            if addr_match:
                addr = addr_match.group(1)
                if addr and addr != node:
                    logger.info(f"Resolved node {node} -> IP {addr}")
                    return addr
            
            logger.info(f"Using hostname {node} (no separate IP found)")
            return node
            
        except subprocess.TimeoutExpired:
            logger.warning(f"scontrol timed out for job {job_id}")
            return None
        except FileNotFoundError:
            logger.warning("scontrol command not found")
            return None
    
    def _get_job_state(self, job_id: str) -> Optional[str]:
        """Get the current SLURM state of a job."""
        try:
            result = subprocess.run(
                ["squeue", "-j", job_id, "--noheader", "--format=%T"],
                capture_output=True, text=True, timeout=10
            )
            state = result.stdout.strip()
            return state or None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
    
    def _health_check(self, endpoint: str) -> tuple:
        """
        Check if the vLLM server is responding.
        
        Returns:
            Tuple of (is_healthy: bool, error_message: str or None).
        """
        import urllib.request
        import urllib.error
        
        base_url = endpoint.rstrip("/")
        if base_url.endswith("/v1"):
            base_url = base_url[:-3]
        
        health_url = f"{base_url}/health"
        try:
            proxy_handler = urllib.request.ProxyHandler({})
            opener = urllib.request.build_opener(proxy_handler)
            req = urllib.request.Request(health_url, method="GET")
            with opener.open(req, timeout=5) as resp:
                return (resp.status == 200, None)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            return (False, str(e))
