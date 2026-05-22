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
import re
import subprocess
import tempfile
import time
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.llm_utils.llm_model import LLMModel, Provider
from src.utils.logger import get_logger

logger = get_logger(__name__)

ClusterConfigDict = Dict[str, Any]


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
        self._jobs: Dict[LLMModel, List[dict]] = {}
        self._pool: Dict[LLMModel, List[dict]] = {}
        self._pool_lock = threading.Lock()
        self._pool_changed = threading.Event()

        self.model_configs: Dict[LLMModel, ClusterConfigDict] = {}

        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitor = threading.Event()

        self._sbatch_dir = Path(tempfile.mkdtemp(prefix="vllm_sbatch_"))

        # Cache: (partition, frozenset(excluded_types)) -> [node names with excluded GPU]
        self._gpu_type_exclude_cache: Dict[tuple, List[str]] = {}

    # ==================== Public API ====================

    def start_server(self, model: LLMModel, config: ClusterConfigDict) -> None:
        """
        Start vLLM server(s) for the given model.

        Submits SLURM jobs and starts a background monitor thread.
        Returns immediately — does NOT wait for servers to be healthy.

        Args:
            model: The cluster model to serve.
            config: Cluster config dict (from load_conf("llm", section="cluster")).
        """
        if model in self._jobs and self._jobs[model]:
            logger.info(f"Servers already submitted for {model.model_id}")
            return

        if model.provider != Provider.NU_CLUSTER:
            raise ValueError(
                f"{model.model_id} is not a cluster model (provider: {model.provider})")

        self.model_configs[model] = config

        num_instances = config["num_instances"]
        base_port = config["port"]

        logger.info(
            f"Starting {num_instances} vLLM server(s) for {model.model_id} "
            f"(ports {base_port}-{base_port + num_instances - 1})")

        self._jobs[model] = []
        self._pool[model] = []

        for i in range(num_instances):
            instance_port = base_port + i
            instance_config = {**config, "port": instance_port}

            sbatch_path = self._generate_sbatch(model, instance_config, instance_id=i)
            job_id = self._submit_sbatch(sbatch_path)

            self._jobs[model].append({
                "job_id": job_id,
                "port": instance_port,
                "instance_id": i,
                "discovered": False,
            })
            logger.info(f"  Instance {i}: SLURM job {job_id}, port {instance_port}")

        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._stop_monitor.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="vllm-pool-monitor",
            )
            self._monitor_thread.start()
            logger.info("Started background server monitor thread")

    def acquire_endpoint(self, model: LLMModel, timeout: Optional[int] = None) -> str:
        """
        Acquire an available endpoint from the pool. Blocks until one is available.

        Returns:
            Endpoint URL string.

        Raises:
            RuntimeError: If no endpoint becomes available within timeout.
        """
        config = self.model_configs.get(model, {})
        wait_interval = config.get("endpoint_wait_timeout", 30)
        if timeout is None:
            timeout = config.get("cluster_server_endpoint_timeout", 10000)
        deadline = time.time() + timeout

        while time.time() < deadline:
            with self._pool_lock:
                for entry in self._pool.get(model, []):
                    if entry["is_available"]:
                        entry["is_available"] = False
                        logger.debug(f"Acquired endpoint {entry['endpoint']}")
                        return entry["endpoint"]

            remaining = deadline - time.time()
            wait_time = min(wait_interval, max(remaining, 0))
            if wait_time <= 0:
                break
            self._pool_changed.wait(timeout=wait_time)
            self._pool_changed.clear()

        raise RuntimeError(
            f"No endpoint available for {model.model_id} within {timeout}s. "
            f"Pool has {len(self._pool.get(model, []))} server(s), "
            f"all busy or none started.")

    def release_endpoint(self, model: LLMModel, endpoint: str) -> None:
        """Release an endpoint back to the pool, marking it as available."""
        with self._pool_lock:
            for entry in self._pool.get(model, []):
                if entry["endpoint"] == endpoint:
                    entry["is_available"] = True
                    logger.debug(f"Released endpoint {endpoint}")
                    break
        self._pool_changed.set()

    def get_num_instances(self, model: LLMModel) -> int:
        """Get the number of submitted server instances for a model."""
        return len(self._jobs.get(model, []))

    def get_num_ready(self, model: LLMModel) -> int:
        """Get the number of healthy, pool-registered endpoints for a model."""
        with self._pool_lock:
            return len(self._pool.get(model, []))

    def wait_for_first_server(self, model: LLMModel, timeout: Optional[int] = None) -> str:
        """Block until at least one server for `model` enters the pool.

        Short-circuits if all submitted server jobs for this model have
        already been resolved by the monitor and none added to the pool —
        i.e., every job failed. Without this, we'd keep polling an empty
        pool until full timeout (1h default), even though the manager
        already knows the model has no live servers.

        Returns:
            The first available endpoint URL.

        Raises:
            RuntimeError: If no server comes up within timeout, OR if the
                monitor has confirmed every job for this model failed.
        """
        config = self.model_configs.get(model, {})
        if timeout is None:
            timeout = config.get("server_start_timeout", 3600)
        deadline = time.time() + timeout
        start = time.time()
        logger.info(f"Waiting for first server for {model.model_id} (timeout: {timeout}s)...")

        last_progress_log = start
        progress_interval = 60.0  # emit a "still waiting" status every 60s

        while time.time() < deadline:
            with self._pool_lock:
                if self._pool.get(model):
                    first_endpoint = self._pool[model][0]["endpoint"]
                    logger.info(f"First server ready: {first_endpoint}")
                    return first_endpoint

            # Short-circuit on all-failed: if every submitted job for this
            # model is already discovered (resolved by monitor) and the pool
            # is still empty, every one of them failed — no point waiting.
            jobs = self._jobs.get(model, [])
            if jobs and all(j["discovered"] for j in jobs):
                with self._pool_lock:
                    pool_empty = not self._pool.get(model)
                if pool_empty:
                    raise RuntimeError(
                        f"All {len(jobs)} server job(s) for "
                        f"{model.model_id} failed during discovery. "
                        f"Check logs/vllm_{model.name.lower()}_*.err for "
                        f"startup errors (config mismatch, OOM, etc.).")

            # Periodic progress log so an extended wait isn't silent (the
            # monitor only logs successes/failures; PENDING + slow-server
            # would otherwise produce no orchestrator-side output for many
            # minutes).
            now = time.time()
            if now - last_progress_log >= progress_interval:
                with self._pool_lock:
                    pool_size = len(self._pool.get(model, []))
                jobs_now = self._jobs.get(model, [])
                discovered = sum(1 for j in jobs_now if j["discovered"])
                elapsed = int(now - start)
                logger.info(
                    f"Still waiting for {model.model_id}: elapsed={elapsed}s, "
                    f"jobs_submitted={len(jobs_now)}, jobs_discovered="
                    f"{discovered}, pool_size={pool_size}. "
                    f"(See per-job monitor lines above for what's blocking.)")
                last_progress_log = now

            remaining = deadline - time.time()
            if remaining <= 0:
                break
            self._pool_changed.wait(timeout=min(10, remaining))
            self._pool_changed.clear()

        raise RuntimeError(
            f"No server for {model.model_id} became ready within {timeout}s. "
            f"Check SLURM logs.")

    def get_server_status(self, model: LLMModel) -> Dict[str, Any]:
        """Get the current lifecycle status of servers for a model."""
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

    def shutdown_all(self) -> None:
        """Cancel all active SLURM jobs and clean up."""
        self._stop_monitor.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)

        for model, jobs in self._jobs.items():
            for job_info in jobs:
                job_id = job_info["job_id"]
                logger.info(f"Cancelling SLURM job {job_id} ({model.model_id})")
                try:
                    subprocess.run(
                        ["scancel", job_id],
                        capture_output=True, timeout=10)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    logger.warning(f"Could not cancel job {job_id}")

        self._jobs.clear()
        with self._pool_lock:
            self._pool.clear()
        self._pool_changed.set()
        logger.info("All vLLM servers shut down")

    def shutdown_model(self, model: LLMModel) -> None:
        """Cancel all SLURM jobs for a single model and clear its pool entries.

        Mid-run teardown: lets the orchestrator free a heavy model's GPU
        allocation as soon as the last task needing it completes, instead of
        holding 4× A100s pinned for the entire experiment lifetime.

        Safe to call on a model that's already been torn down (no-op).
        """
        jobs = self._jobs.pop(model, [])
        for job_info in jobs:
            job_id = job_info["job_id"]
            logger.info(
                f"Cancelling SLURM job {job_id} ({model.model_id}) [mid-run]")
            try:
                subprocess.run(
                    ["scancel", job_id], capture_output=True, timeout=10)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.warning(f"Could not cancel job {job_id}")
        with self._pool_lock:
            self._pool.pop(model, None)
        self._pool_changed.set()

    def __del__(self):
        if self._jobs:
            self.shutdown_all()

    # ==================== Background Monitor ====================

    def _monitor_loop(self) -> None:
        """Background thread: discover new servers AND keep checking pool health.

        Phase 1 (discovery): poll SLURM jobs and add healthy endpoints to the
        pool as they become reachable. Each job is "discovered" exactly once.

        Phase 2 (maintenance): periodically re-ping every pool entry's /health.
        If a previously-discovered server stops responding (vLLM OOM'd, GPU
        ECC'd, etc.), evict it from the pool. Without this, acquire_endpoint()
        would hand out a stale dead endpoint and the task would hang on the
        first request rather than waiting for a fresh one.

        Runs until _stop_monitor is set (i.e. until shutdown_all()).
        """
        config = next(iter(self.model_configs.values()), {})
        poll_interval = config.get("monitor_poll_interval", 10)
        # Cadence at which discovered endpoints get re-health-checked.
        # 60s default keeps overhead near zero for typical pool sizes.
        recheck_interval = config.get("health_recheck_interval", 60)
        last_recheck = 0.0

        while not self._stop_monitor.is_set():
            # ---- Phase 1: discovery ----
            for model, jobs in list(self._jobs.items()):
                for job_info in jobs:
                    if job_info["discovered"]:
                        continue

                    job_id = job_info["job_id"]
                    port = job_info["port"]
                    instance_id = job_info["instance_id"]
                    instance_suffix = f"[{instance_id}]" if instance_id > 0 else ""

                    state = self._get_job_state(job_id)

                    if state is None:
                        model_safe_name = model.name.lower()
                        logger.warning(
                            f"Server{instance_suffix} (job {job_id}) failed. "
                            f"Check logs/vllm_{model_safe_name}_*.err")
                        job_info["discovered"] = True
                        continue

                    if state == "PENDING":
                        # Log first observation only, then quietly poll.
                        if not job_info.get("_logged_pending"):
                            logger.info(
                                f"Server{instance_suffix} (job {job_id}) "
                                f"still PENDING in SLURM queue; will keep polling.")
                            job_info["_logged_pending"] = True
                        continue

                    node = self._resolve_job_node(job_id)
                    if not node:
                        # Log first N occurrences so we know SLURM isn't surfacing
                        # the node assignment yet — silent-forever before this fix.
                        attempts = job_info.get("_node_resolve_attempts", 0) + 1
                        job_info["_node_resolve_attempts"] = attempts
                        if attempts <= 3 or attempts % 30 == 0:
                            logger.info(
                                f"Server{instance_suffix} (job {job_id}) state="
                                f"{state} but scontrol hasn't returned a NodeList/"
                                f"NodeAddr yet (attempt {attempts}). Retrying.")
                        continue

                    endpoint = f"http://{node}:{port}/v1"
                    healthy, err = self._health_check(endpoint)

                    if not healthy:
                        # The previously-silent failure mode. Could be:
                        #   - vLLM still loading weights / compiling graphs
                        #   - inter-partition network unreachable (firewall, etc.)
                        #   - wrong NodeAddr resolved
                        #   - vLLM crashed but SLURM hasn't noticed
                        # Log first few + every Nth so user sees something.
                        attempts = job_info.get("_health_check_attempts", 0) + 1
                        job_info["_health_check_attempts"] = attempts
                        if attempts <= 3 or attempts % 12 == 0:  # first 3, then ~every 2min
                            logger.info(
                                f"Server{instance_suffix} (job {job_id}) at "
                                f"{endpoint} not yet healthy "
                                f"(attempt {attempts}, err={err}). Retrying.")

                    if healthy:
                        with self._pool_lock:
                            self._pool[model].append({
                                "endpoint": endpoint,
                                "is_available": True,
                                "job_id": job_id,
                            })
                        job_info["discovered"] = True
                        logger.info(
                            f"Server{instance_suffix} ready at {endpoint} "
                            f"(pool size: {len(self._pool[model])})")
                        self._pool_changed.set()

            # ---- Phase 2: re-health-check discovered endpoints ----
            now = time.time()
            if now - last_recheck >= recheck_interval:
                last_recheck = now
                self._recheck_pool_health()

            self._stop_monitor.wait(timeout=poll_interval)

    def _recheck_pool_health(self) -> None:
        """Re-ping every pool entry's /health; evict any that fail.

        Catches mid-run vLLM crashes (OOM, GPU error, network blip) so that
        acquire_endpoint() doesn't hand out a dead URL. Eviction does NOT
        scancel the SLURM job — the job is presumed already dying or done,
        and a future shutdown_all/_model will clean it up.

        Single-failure eviction is intentional: /health is a constant-time
        endpoint, so a 5s timeout failing means the server really is gone.
        """
        with self._pool_lock:
            snapshot = {m: list(entries) for m, entries in self._pool.items()}

        evicted_any = False
        for model, entries in snapshot.items():
            for entry in entries:
                healthy, err = self._health_check(entry["endpoint"])
                if healthy:
                    continue
                with self._pool_lock:
                    pool = self._pool.get(model, [])
                    self._pool[model] = [
                        e for e in pool if e["endpoint"] != entry["endpoint"]
                    ]
                logger.warning(
                    f"Mid-run health check failed for {entry['endpoint']} "
                    f"({model.model_id}): {err}. Evicted from pool "
                    f"(remaining: {len(self._pool.get(model, []))}).")
                evicted_any = True

        if evicted_any:
            self._pool_changed.set()

    # ==================== SLURM Helpers ====================

    def _generate_sbatch(
        self, model: LLMModel, config: ClusterConfigDict,
        instance_id: int = 0
    ) -> Path:
        """Generate sbatch script for a vLLM server instance."""
        from .constants import MAX_SLURM_TIME_LIMIT

        model_safe_name = model.name.lower()
        instance_suffix = f"_i{instance_id}" if instance_id > 0 else ""

        # Combine explicit node exclusions with GPU-type-based exclusions.
        # gpu_types_excluded is resolved to a node list by querying sinfo
        # (the cluster GRES strings carry the GPU type, but not all GPU types
        # are exposed as SLURM features, so `--constraint` can't express this).
        explicit_excluded = list(config.get("excluded_nodes", []))
        type_excluded_nodes = self._resolve_gpu_type_excludes(
            config["partition"], config.get("gpu_types_excluded", []))
        all_excluded = sorted(set(explicit_excluded) | set(type_excluded_nodes))
        exclude_directive = (
            f"#SBATCH --exclude={','.join(all_excluded)}"
            if all_excluded else ""
        )

        time_limit = config["time_limit"]
        if time_limit and time_limit > MAX_SLURM_TIME_LIMIT:
            logger.warning(
                f"time_limit '{time_limit}' exceeds cluster max "
                f"'{MAX_SLURM_TIME_LIMIT}', clamping")
            time_limit = MAX_SLURM_TIME_LIMIT

        vllm_args = [
            f"--model {model.model_id}",
            "--host 0.0.0.0",
            f"--port {config['port']}",
            f"--gpu-memory-utilization {config['gpu_memory_utilization']}",
            f"--max-model-len {config['max_model_len']}",
        ]
        if config.get("dtype"):
            vllm_args.append(f"--dtype {config['dtype']}")
        if config["num_gpus"] > 1:
            vllm_args.append(f"--tensor-parallel-size {config['num_gpus']}")
        if config.get("chat_template"):
            chat_template_dir = Path(__file__).parent / "chat_templates"
            template_file = chat_template_dir / f"{config['chat_template']}.jinja"
            if template_file.exists():
                vllm_args.append(f"--chat-template {template_file.resolve()}")
                logger.info(f"Using chat template: {template_file.resolve()}")
            else:
                logger.warning(
                    f"Chat template not found: {template_file}. "
                    f"vLLM will use model default.")

        vllm_cmd = "python -m vllm.entrypoints.openai.api_server \\\n    " + \
                   " \\\n    ".join(vllm_args)

        sbatch_lines = [
            "#!/bin/bash",
            f"#SBATCH --job-name=vllm_{model_safe_name}{instance_suffix}",
            f"#SBATCH --partition={config['partition']}",
        ]
        if exclude_directive:
            sbatch_lines.append(exclude_directive)
        sbatch_lines.extend([
            "#SBATCH --nodes=1",
            f"#SBATCH --gres=gpu:{config['num_gpus']}",
            f"#SBATCH --cpus-per-task={config['cpus_per_task']}",
            f"#SBATCH --mem={config['mem_gb']}GB",
            f"#SBATCH --time={time_limit}",
            f"#SBATCH --output=logs/vllm_{model_safe_name}{instance_suffix}_%j.out",
            f"#SBATCH --error=logs/vllm_{model_safe_name}{instance_suffix}_%j.err",
            "",
            "# Setup environment",
            "mkdir -p logs",
            f"module load anaconda3/2024.06 {config['cuda_module']}",
            f"source activate {config['conda_env']}",
            "",
            "# Compute nodes have no internet — must run fully offline",
            f"export HF_HOME=\"${{HF_HOME:-{config['hf_home']}}}\"",
            "export HF_HUB_OFFLINE=1",
            "export TRANSFORMERS_OFFLINE=1",
            "",
            "# Start vLLM server (blocks until killed by scancel or time limit)",
            vllm_cmd,
        ])

        script = "\n".join(sbatch_lines) + "\n"

        sbatch_path = self._sbatch_dir / f"vllm_{model_safe_name}{instance_suffix}.sbatch"
        sbatch_path.write_text(script)
        logger.debug(f"Generated sbatch at {sbatch_path}")
        return sbatch_path

    def _submit_sbatch(self, sbatch_path: Path) -> str:
        """Submit sbatch script and return the SLURM job ID."""
        try:
            result = subprocess.run(
                ["sbatch", str(sbatch_path)],
                capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                raise RuntimeError(f"sbatch failed: {result.stderr.strip()}")

            output = result.stdout.strip()
            return output.split()[-1]

        except FileNotFoundError:
            raise RuntimeError(
                "sbatch command not found. "
                "Are you running this on the cluster login node?")

    def _resolve_job_node(self, job_id: str) -> Optional[str]:
        """
        Get the IP address or hostname of the node running a SLURM job.

        Resolves via scontrol: job → NodeList → NodeAddr (IP).
        Falls back to hostname if IP resolution fails.
        """
        config = next(iter(self.model_configs.values()), {})
        cmd_timeout = config.get("slurm_cmd_timeout", 15)

        try:
            result = subprocess.run(
                ["scontrol", "show", "job", job_id],
                capture_output=True, text=True, timeout=cmd_timeout)
            if result.returncode != 0:
                return None

            match = re.search(r"NodeList=(\S+)", result.stdout)
            if not match:
                return None
            node = match.group(1)
            if not node or node == "(null)":
                return None

            # Resolve node name → IP address
            result = subprocess.run(
                ["scontrol", "show", "node", node],
                capture_output=True, text=True, timeout=cmd_timeout)
            if result.returncode != 0:
                return node

            addr_match = re.search(r"NodeAddr=(\S+)", result.stdout)
            if addr_match:
                addr = addr_match.group(1)
                if addr and addr != node:
                    logger.info(f"Resolved node {node} -> IP {addr}")
                    return addr

            return node

        except subprocess.TimeoutExpired:
            logger.warning(f"scontrol timed out for job {job_id}")
            return None
        except FileNotFoundError:
            logger.warning("scontrol command not found")
            return None

    def _resolve_gpu_type_excludes(
        self, partition: str, excluded_types: List[str]
    ) -> List[str]:
        """
        Resolve `gpu_types_excluded` to a concrete node-name list by querying sinfo.

        The cluster encodes GPU type in the GRES string (`gpu:<type>:N`) but not
        always as a SLURM feature, so SBATCH --constraint can't filter by type.
        Instead we expand each excluded GPU type to the set of nodes carrying it
        and merge into --exclude=.

        Result is cached per (partition, frozenset(excluded_types)).
        """
        if not excluded_types:
            return []

        cache_key = (partition, frozenset(excluded_types))
        if cache_key in self._gpu_type_exclude_cache:
            return self._gpu_type_exclude_cache[cache_key]

        config = next(iter(self.model_configs.values()), {})
        cmd_timeout = config.get("slurm_cmd_timeout", 15)

        try:
            result = subprocess.run(
                ["sinfo", "--partition", partition,
                 "--noheader", "-o", "%n %G"],
                capture_output=True, text=True, timeout=cmd_timeout)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(
                f"sinfo failed while resolving gpu_types_excluded: {e}. "
                f"GPU-type filter will be a no-op for this run.")
            return []

        if result.returncode != 0:
            logger.warning(
                f"sinfo returncode={result.returncode} resolving "
                f"gpu_types_excluded: {result.stderr.strip()}")
            return []

        excluded_set = set(excluded_types)
        nodes: List[str] = []
        seen: set = set()
        for line in result.stdout.strip().splitlines():
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            node, gres = parts[0], parts[1]
            # GRES form: "gpu:v100-pcie:2(S:0-1)" or "gpu:a100:4" or "(null)"
            m = re.match(r"gpu:([^:()]+):", gres)
            if not m:
                continue
            gpu_type = m.group(1)
            if gpu_type in excluded_set and node not in seen:
                nodes.append(node)
                seen.add(node)

        logger.info(
            f"gpu_types_excluded={excluded_types} resolved to "
            f"{len(nodes)} node(s) on partition '{partition}'")
        self._gpu_type_exclude_cache[cache_key] = nodes
        return nodes

    def _get_job_state(self, job_id: str) -> Optional[str]:
        """Get the current SLURM state of a job (RUNNING, PENDING, etc.)."""
        config = next(iter(self.model_configs.values()), {})
        cmd_timeout = config.get("slurm_cmd_timeout", 15)

        try:
            result = subprocess.run(
                ["squeue", "-j", job_id, "--noheader", "--format=%T"],
                capture_output=True, text=True, timeout=cmd_timeout)
            state = result.stdout.strip()
            return state or None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def _health_check(self, endpoint: str) -> tuple[bool, Optional[str]]:
        """
        Check if the vLLM server is responding at the /health endpoint.

        Returns:
            (is_healthy, error_message_or_None)
        """
        import urllib.request
        import urllib.error

        config = next(iter(self.model_configs.values()), {})
        check_timeout = config.get("health_check_timeout", 5)

        base_url = endpoint.rstrip("/")
        if base_url.endswith("/v1"):
            base_url = base_url[:-3]

        health_url = f"{base_url}/health"
        try:
            proxy_handler = urllib.request.ProxyHandler({})
            opener = urllib.request.build_opener(proxy_handler)
            req = urllib.request.Request(health_url, method="GET")
            with opener.open(req, timeout=check_timeout) as resp:
                return (resp.status == 200, None)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            return (False, str(e))
