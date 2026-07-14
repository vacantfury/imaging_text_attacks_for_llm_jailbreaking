"""Multi-cluster experiment dispatch (TODO item 3).

Split ONE experiment preset across an ordered pool of SLURM clusters
(AICR first, then NURC), submitting each cluster its own sub-preset over ssh.

Design (why this is a thin pre-submit layer, not a runtime change):
    Every SLURM call in ``ClusterModelServerManager`` (sbatch/squeue/scontrol)
    is a LOCAL subprocess — the orchestrator assumes it runs on the target
    cluster's login node, and "which cluster" is purely where the process runs
    plus the ``CLUSTER_PROFILE`` env var. Since the code is synced to BOTH
    clusters, each cluster runs the existing single-cluster orchestrator
    natively against its own local SLURM. So multi-cluster needs no runtime
    federation: we only (a) split the task matrix here, then (b) ssh each
    cluster its own sub-preset + ``sbatch`` wrapper. Zero edits to the
    orchestrator runtime.

Split key = the full set of *cluster-served* models each task needs
    (target INTERSECT judge INTERSECT guard), computed by reusing the pipeline's
    own ``_required_cluster_models_for_task``. API-hosted models drop out (they
    are not vLLM servers), so the split is target-only when the judge is an API
    model (e.g. gpt-5-nano) and target+judge when the judge is itself served.
    A cell is atomic: it runs on ONE cluster, which serves every model it
    touches — a pipeline is never split across clusters.

Placement = greedy, pool-ordered. Pack whole tasks onto the first cluster whose
    remaining server budget fits them (preset order), overflow the rest to the
    next cluster. A model shared across a split is served once per cluster
    (accepted duplication — the price of running two clusters at once). A
    ``pins`` map forces every task needing a given model onto a named cluster —
    use it to keep a big judge single instead of duplicated.

DRY-RUN by default: :func:`dispatch` writes the sub-presets locally and returns
    the plan + exact ssh commands, submitting nothing. Actual submission happens
    only under ``submit=True`` (and only after the code is synced to both
    clusters). This module never self-initiates a cluster run.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .constants import MAX_SUBMIT_JOBS_PER_USER


class DispatchError(Exception):
    """Raised when a preset cannot be split across the configured pool."""


# ==================== Pool config ====================

@dataclass(frozen=True)
class ClusterSpec:
    """One cluster in the ordered dispatch pool.

    budget = max concurrent vLLM SERVERS the orchestrator may hold on this
    cluster (its GPU-QOS concurrent-job ceiling; the orchestrator itself runs
    on a separate CPU partition/QOS and does NOT count against it).
    """
    name: str
    ssh: str                 # ssh alias/target in ~/.ssh/config
    repo: str                # repo path on the cluster (may start with ~)
    sbatch: str              # sbatch wrapper, e.g. scripts/run_experiment_aicr.sbatch
    cluster_profile: str     # CLUSTER_PROFILE the wrapper exports ("" = NURC default)
    budget: int              # max concurrent vLLM servers on this cluster


def load_pool(path: Path) -> tuple[list[ClusterSpec], dict[str, str]]:
    """Load the ordered cluster pool + optional model pins from a YAML file.

    Returns (clusters, pins) where pins maps a model_id -> cluster name.
    """
    if not path.exists():
        raise DispatchError(
            f"cluster pool config not found: {path}\n"
            f"Copy conf/cluster_pool.example.yaml to {path} and fill in your "
            f"cluster ssh aliases / repo paths (the real file is gitignored)."
        )
    data = yaml.safe_load(path.read_text()) or {}
    raw_clusters = data.get("clusters") or []
    if not raw_clusters:
        raise DispatchError(f"{path} has no 'clusters' list.")

    clusters: list[ClusterSpec] = []
    for i, c in enumerate(raw_clusters):
        missing = {"name", "ssh", "repo", "sbatch", "budget"} - set(c)
        if missing:
            raise DispatchError(
                f"cluster #{i} in {path} is missing keys: {sorted(missing)}")
        clusters.append(ClusterSpec(
            name=str(c["name"]),
            ssh=str(c["ssh"]),
            repo=str(c["repo"]),
            sbatch=str(c["sbatch"]),
            cluster_profile=str(c.get("cluster_profile", "")),
            budget=int(c["budget"]),
        ))

    names = [c.name for c in clusters]
    if len(set(names)) != len(names):
        raise DispatchError(f"duplicate cluster names in {path}: {names}")

    pins = {str(k): str(v) for k, v in (data.get("pins") or {}).items()}
    for model, cname in pins.items():
        if cname not in names:
            raise DispatchError(
                f"pin '{model}' -> '{cname}' references an unknown cluster "
                f"(known: {names}).")
    return clusters, pins


# ==================== Split plan ====================

@dataclass
class ClusterAssignment:
    cluster: ClusterSpec
    task_indices: list[int]
    server_models: set[str]         # model_ids that will be served on this cluster

    @property
    def num_cluster_jobs(self) -> int:
        """orchestrator (1) + one vLLM job per distinct served model, code-capped."""
        return min(len(self.server_models) + 1, MAX_SUBMIT_JOBS_PER_USER)

    @property
    def active(self) -> bool:
        return bool(self.task_indices)


@dataclass
class SplitPlan:
    assignments: list[ClusterAssignment]
    leftover: list[int]                 # task indices that fit no cluster
    total_cluster_models: set[str]      # distinct served models across the whole preset


def plan_split(
    task_models: list[tuple[int, frozenset[str]]],
    clusters: list[ClusterSpec],
    pins: dict[str, str],
) -> SplitPlan:
    """Assign tasks to clusters, AICR-first (pool order).

    task_models: (task_index, frozenset of cluster-served model_ids) per task.
    Pure function — no I/O, no pipeline import — so the packing is unit-testable
    with fabricated inputs.
    """
    by_name = {c.name: c for c in clusters}
    assign: dict[str, list[int]] = {c.name: [] for c in clusters}
    servers: dict[str, set[str]] = {c.name: set() for c in clusters}

    # Phase 1 — pin-forced tasks. A task needing a pinned model goes to that
    # cluster; needing two models pinned to DIFFERENT clusters is unsatisfiable.
    pending: list[tuple[int, frozenset[str]]] = []
    for idx, models in task_models:
        pinned = {pins[m] for m in models if m in pins}
        if len(pinned) > 1:
            raise DispatchError(
                f"task #{idx} needs models pinned to different clusters "
                f"{sorted(pinned)}; a single pipeline cannot be split across "
                f"clusters. Fix the pins so its models share one cluster.")
        if pinned:
            cname = next(iter(pinned))
            assign[cname].append(idx)
            servers[cname] |= models
        else:
            pending.append((idx, models))

    # Pins may already overflow a cluster's budget — surface that clearly.
    for c in clusters:
        if len(servers[c.name]) > c.budget:
            raise DispatchError(
                f"pins force {len(servers[c.name])} servers onto '{c.name}' "
                f"(budget {c.budget}): {sorted(servers[c.name])}. "
                f"Raise its budget or repin.")

    # Phase 2 — greedy pool-ordered fill (preset order within each cluster).
    for c in clusters:
        still: list[tuple[int, frozenset[str]]] = []
        for idx, models in pending:
            new = models - servers[c.name]
            if len(servers[c.name]) + len(new) <= c.budget:
                assign[c.name].append(idx)
                servers[c.name] |= models
            else:
                still.append((idx, models))
        pending = still

    leftover = [idx for idx, _ in pending]
    assignments = [
        ClusterAssignment(
            cluster=c,
            task_indices=sorted(assign[c.name]),
            server_models=servers[c.name],
        )
        for c in clusters
    ]
    total: set[str] = set()
    for _, models in task_models:
        total |= models
    return SplitPlan(assignments=assignments, leftover=leftover,
                     total_cluster_models=total)


# ==================== Pipeline coupling ====================

def _model_key(m) -> str:
    """Stable identity for an LLMModel (its model_id)."""
    return getattr(m, "model_id", None) or getattr(m, "name", None) or str(m)


def compute_task_models(preset) -> list[tuple[int, frozenset[str]]]:
    """Per task, the set of cluster-served model_ids it needs.

    Reuses the orchestrator's own ``_required_cluster_models_for_task`` so the
    split key stays exactly consistent with what the pipeline actually serves.
    """
    from .experiment import (
        _required_cluster_models_for_task, TaskInfo, _get_task_name,
    )
    out: list[tuple[int, frozenset[str]]] = []
    for i, task in enumerate(preset.tasks):
        info = TaskInfo(index=i, task=task, name=_get_task_name(task, i))
        models = _required_cluster_models_for_task(info)
        out.append((i, frozenset(_model_key(m) for m in models)))
    return out


# ==================== Sub-preset rendering ====================

def subpreset_name(preset_name: str, cluster_name: str) -> str:
    """Sub-preset name, kept under the ORIGINAL paper subdir so output
    namespacing (paper = first path component) is preserved.

    'autoattack_defense/experiment' + 'aicr'
        -> 'autoattack_defense/_mc_experiment_aicr'
    'test' + 'nurc' -> '_mc_test_nurc'
    """
    if "/" in preset_name:
        paper, base = preset_name.split("/", 1)
        return f"{paper}/_mc_{base.replace('/', '_')}_{cluster_name}"
    return f"_mc_{preset_name}_{cluster_name}"


def render_subpreset(preset, assignment: ClusterAssignment) -> dict:
    """Build the sub-preset dict for one cluster (its assigned tasks only)."""
    tasks = [preset.tasks[i].model_dump(mode="json")
             for i in assignment.task_indices]
    return {
        "num_main_job_threads": preset.num_main_job_threads,
        "num_cluster_jobs": assignment.num_cluster_jobs,
        "tasks": tasks,
    }


def write_subpreset(conf_dir: Path, name: str, data: dict) -> Path:
    """Write a sub-preset YAML under conf/experiment/<name>.yaml locally."""
    path = conf_dir / "experiment" / f"{name}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"# GENERATED by dispatch.py (multi-cluster split) — do not edit by hand.\n"
        f"# Regenerate with: python dispatch.py <preset>\n"
    )
    path.write_text(header + yaml.safe_dump(data, sort_keys=False, width=120))
    return path


# ==================== ssh command construction ====================

def _remote_yaml_path(cluster: ClusterSpec, name: str) -> str:
    return f"{cluster.repo}/conf/experiment/{name}.yaml"


def dispatch_commands(cluster: ClusterSpec, name: str) -> list[str]:
    """The exact ssh command sequence to place + submit one cluster's sub-preset.

    Returned as human-readable strings (also what --submit executes). Remote
    paths are NOT single-quoted so a leading ~ expands on the remote shell.
    """
    remote_yaml = _remote_yaml_path(cluster, name)
    remote_dir = remote_yaml.rsplit("/", 1)[0]
    return [
        f"ssh {cluster.ssh} 'mkdir -p {remote_dir}'",
        f"cat conf/experiment/{name}.yaml | ssh {cluster.ssh} 'cat > {remote_yaml}'",
        f"ssh {cluster.ssh} 'cd {cluster.repo} && sbatch {cluster.sbatch} {name}'",
    ]


def _run_dispatch(cluster: ClusterSpec, name: str, conf_dir: Path) -> str:
    """Actually place the sub-preset on the cluster and submit it. Returns the
    sbatch stdout (job id line). Only called under submit=True."""
    remote_yaml = _remote_yaml_path(cluster, name)
    remote_dir = remote_yaml.rsplit("/", 1)[0]
    local_yaml = conf_dir / "experiment" / f"{name}.yaml"

    subprocess.run(["ssh", cluster.ssh, f"mkdir -p {remote_dir}"],
                   check=True, timeout=60)
    with open(local_yaml, "rb") as fh:
        subprocess.run(["ssh", cluster.ssh, f"cat > {remote_yaml}"],
                       stdin=fh, check=True, timeout=60)
    result = subprocess.run(
        ["ssh", cluster.ssh, f"cd {cluster.repo} && sbatch {cluster.sbatch} {name}"],
        capture_output=True, text=True, check=True, timeout=120)
    return result.stdout.strip()


# ==================== Orchestration ====================

@dataclass
class DispatchResult:
    preset_name: str
    plan: SplitPlan
    subpresets: dict[str, str]           # cluster name -> sub-preset name
    written: dict[str, Path]             # cluster name -> local sub-preset path
    commands: dict[str, list[str]]       # cluster name -> ssh command list
    submitted: dict[str, str] = field(default_factory=dict)  # cluster -> sbatch stdout


def dispatch(
    preset_name: str,
    pool_path: Path,
    conf_dir: Path,
    submit: bool = False,
) -> DispatchResult:
    """Plan the split, write sub-presets locally, and (only if submit=True)
    ssh them to each cluster and sbatch. Dry-run otherwise."""
    from .experiment import load_preset

    clusters, pins = load_pool(pool_path)
    preset = load_preset(preset_name, conf_dir)
    task_models = compute_task_models(preset)
    plan = plan_split(task_models, clusters, pins)

    if plan.leftover:
        need = {i: sorted(dict(task_models)[i]) for i in plan.leftover}
        raise DispatchError(
            f"{len(plan.leftover)} task(s) need more distinct servers than any "
            f"cluster's budget and cannot be dispatched: {need}. "
            f"Raise a cluster budget or reduce the task's model fan-out.")

    subpresets: dict[str, str] = {}
    written: dict[str, Path] = {}
    commands: dict[str, list[str]] = {}
    submitted: dict[str, str] = {}

    for a in plan.assignments:
        if not a.active:
            continue
        name = subpreset_name(preset_name, a.cluster.name)
        subpresets[a.cluster.name] = name
        written[a.cluster.name] = write_subpreset(
            conf_dir, name, render_subpreset(preset, a))
        commands[a.cluster.name] = dispatch_commands(a.cluster, name)
        if submit:
            submitted[a.cluster.name] = _run_dispatch(a.cluster, name, conf_dir)

    return DispatchResult(
        preset_name=preset_name, plan=plan, subpresets=subpresets,
        written=written, commands=commands, submitted=submitted)
