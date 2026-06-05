"""
Pydantic schemas for the destroyer-paper pipeline (post-refactor).

Two modes only:

  Stage 1 — prompt_transform
      Runs a chain of PromptTransformations (encoders + image renderers)
      one-by-one. Each step writes its own subfolder under the task's
      output dir, plus a cumulative results.json carrying the chain's
      full history.

  Stage 2 — defense+evaluate
      Takes a specific subfolder from a prompt_transform output, hands the
      prompts to a Defense (which owns the target-model interaction loop),
      runs the canonical judge, writes raw_results.jsonl + results.json.
"""
from typing import Annotated, Any, List, Literal, Optional, Union
from pydantic import BaseModel, Discriminator, Field, field_validator, model_validator

from src.utils.provenance import SCHEMA_VERSION


# ====================================================================
# Inter-stage Prompt records
# ====================================================================


class RawPrompt(BaseModel):
    """Source prompt loaded from harmful/benign dataset JSONL."""
    id: str
    category: str
    source: str           # "advbench" | "harmbench" | "jailbreakbench"
    prompt: str


class Prompt(BaseModel):
    """Carrier across prompt_transform steps.

    `original` is the raw harmful query — never modified by the chain.
    Judges read it as ground-truth intent. `encoded` is the current text
    after the chain so far. `image_encoded` is set by image transformations.

    `image_original` / `encoding` are kept for back-compat with older
    prompts.jsonl files; the new pipeline doesn't write `image_original`
    and treats `encoding` as a free-text label (chain executor sets it to
    the last text transformation's type_name)."""
    id: str
    encoding: str = ""
    original: str
    encoded: str
    image_original: Optional[str] = None
    # List of rendered-image paths (relative to the prompt_transform step dir).
    # The paginated renderer emits one path per page; short prompts → 1 path.
    image_encoded: Optional[List[str]] = None

    @field_validator("image_encoded", mode="before")
    @classmethod
    def _coerce_image_encoded(cls, v):
        """Back-compat: archived prompts.jsonl stored `image_encoded` as a
        single path string; the paginated renderer now emits a list. Coerce a
        bare string → 1-element list so old data still loads."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        return list(v)


class EvaluationRow(BaseModel):
    """One row in raw_results.jsonl (long format)."""
    id: str
    prompt_stage: str
    response: str
    asr: Optional[bool] = None
    # Multi-image overflow bookkeeping (paginated renderer). `num_images` is the
    # page count of the rendered prompt; `is_within_maxlen` is False when that
    # exceeds MAX_PAGES_PER_PROMPT, in which case the prompt is EXCLUDED from the
    # target query and from ASR (asr stays None) rather than silently truncated.
    num_images: int = 0
    is_within_maxlen: bool = True
    judge_output: Optional[str] = None
    judge_reasoning: Optional[str] = None
    judge_raw_response: Optional[str] = None
    refusal: Optional[bool] = None
    refusal_judge_output: Optional[str] = None
    refusal_judge_reasoning: Optional[str] = None
    refusal_judge_raw_response: Optional[str] = None


class Judgment(BaseModel):
    """ASR judgment for a single response."""
    id: str
    model: str
    encoding: str
    prompt_stage: str
    judge_output: str
    judge_reasoning: Optional[str] = None
    is_jailbroken: bool


# ====================================================================
# prompt_transform results
# ====================================================================


class PromptTransformStepResult(BaseModel):
    """A single step record inside the chain's results_history list."""
    config: dict                       # transformation's resolved kwargs
    metrics: dict = Field(default_factory=dict)
    prompts_file: str                  # relative or absolute path to prompts.jsonl
    images_dir: Optional[str] = None
    is_multimodal_after: bool
    elapsed_seconds: float
    usage: Optional[dict] = None


class PromptTransformResult(BaseModel):
    """Top-level results.json for every step subfolder of a prompt_transform task.

    Each step subfolder writes its own copy of this object, with
    `results_history` truncated to that step. The final step's results.json
    is the chain's complete record.
    """
    mode: Literal["prompt_transform"] = "prompt_transform"
    task_id: str
    benchmark: str
    prompt_range: Optional[list[int]] = None
    dataset_path: str

    is_multimodal: bool                # cumulative state AFTER latest step
    total_steps: int
    latest_step: str                   # type_name of the most recent step
    latest_step_dir: str               # relative path under task_dir
    task_dir: str
    timestamp_last_step: str           # ISO-8601
    elapsed_seconds_total: float
    count: int
    mlflow_run_id: Optional[str] = None

    # Provenance — see src/utils/provenance.py.
    schema_version: int = SCHEMA_VERSION
    git_sha: str = ""
    git_dirty: bool = False
    status: str = "success"

    # Configured plan — full chain including any upstream steps, in order.
    transformation_list: list[str]

    # Per-step log — only steps run THIS task. Steps from an upstream chain
    # (when source_transform_subdir was set) live in `upstream` instead.
    results_history: list[dict[str, PromptTransformStepResult]]

    # Provenance to the step this task chained from, if any. `upstream_ref`
    # ({source_dir, results_sha256}) is the current form — a pointer, not an
    # embedded copy (embedding bloated O(chain-depth) and could drift from its
    # source). `upstream` is legacy (old data embedded the full dict); new
    # writes leave it None and set `upstream_ref`.
    upstream: Optional[dict] = None
    upstream_ref: Optional[dict] = None


# ====================================================================
# defense+evaluate results
# ====================================================================


class TargetModelConfig(BaseModel):
    """Resolved LLM inference params for the target model."""
    max_tokens: int
    temperature: float
    top_p: float
    top_k: int
    frequency_penalty: float
    presence_penalty: float
    stop_sequences: list[str]
    seed: int
    n_completions: int
    stream: bool


class DefenseEvaluateResult(BaseModel):
    """Complete record of a defense+evaluate task — written to results.json."""
    mode: Literal["defense+evaluate"] = "defense+evaluate"

    # Provenance — which prompt_transform step subfolder this consumed.
    source_transform_subdir: str
    upstream: Optional[dict] = None      # legacy embedded copy (old data only)
    upstream_ref: Optional[dict] = None  # {source_dir, results_sha256} pointer — current form
    is_multimodal: bool              # copied from upstream's PromptTransformResult

    # Defense.
    defense: str
    defense_config: dict = Field(default_factory=dict)

    # Target model.
    target_model: str
    target_model_config: TargetModelConfig
    model_family: Optional[str] = None        # first-class, from the registry
    alignment_tier: Optional[str] = None      # first-class, from the registry
    system_message: Optional[str] = None

    # Benchmark + encoding (inferred or override).
    benchmark: str
    encoding: Optional[str] = None
    transformation_list: list[str] = Field(default_factory=list)
    # First-class decoy/companion image path — no more digging into
    # upstream.results_history[i].<step>.config.image_path to recover it.
    companion_image_path: Optional[str] = None
    prompt_range: Optional[list[int]] = None

    # Judging.
    judge_method: str
    judge_model: Optional[str] = None

    # Results.
    count: int
    asr: Optional[float] = None          # HarmBench-style ASR only — never overloaded
    refusal_rate: Optional[float] = None
    # Metric contract: every named scalar metric lives in `metrics`, and
    # `primary_metric` names which key is this benchmark's headline number
    # (e.g. "attack_success_rate", "refusal_rate", "direct_answer_rate") — so a
    # reader never has to know that, say, OR-Bench's headline hides in `asr`.
    metrics: dict[str, float] = Field(default_factory=dict)
    primary_metric: Optional[str] = None
    eval_stats: Optional[dict[str, dict]] = None

    # Usage.
    target_usage: dict
    defense_usage: Optional[dict] = None

    elapsed_seconds: float
    output_dir: str
    mlflow_run_id: Optional[str] = None

    # Provenance — see src/utils/provenance.py.
    schema_version: int = SCHEMA_VERSION
    git_sha: str = ""
    git_dirty: bool = False
    judge_config_hash: Optional[str] = None
    status: str = "success"
    warnings: list[str] = Field(default_factory=list)


# ====================================================================
# Task configs — what experiment.yaml's `tasks:` list contains
# ====================================================================


class _TaskBase(BaseModel):
    """Fields shared by every task mode."""
    benchmark: Optional[str] = None
    prompt_range: Optional[list[int]] = None


class TransformationSpec(BaseModel):
    """One entry in PromptTransformTask.transformation_list."""
    type: str                                  # transformation type_name
    params: dict[str, Any] = Field(default_factory=dict)


class PromptTransformTask(_TaskBase):
    """Stage 1: run a chain of PromptTransformations.

    Each step in `transformation_list` runs in order. The chain executor
    creates one subfolder per step (named by type_name) and writes a
    cumulative results.json into every subfolder.

    Either `source_file` (raw dataset) OR `source_transform_subdir` (a
    prior prompt_transform step) supplies the input prompts. Chaining from
    a prior step lets multiple downstream chains share an identical text
    encoding — critical for paired ablations where encoder-LLM
    nondeterminism would otherwise confound results.
    """
    mode: Literal["prompt_transform"]
    source_file: Optional[str] = None
    source_transform_subdir: Optional[str] = None
    transformation_list: list[TransformationSpec]

    @model_validator(mode="after")
    def _validate(self):
        if not self.transformation_list:
            raise ValueError("transformation_list must contain at least one step")
        if (self.source_file is None) == (self.source_transform_subdir is None):
            raise ValueError(
                "exactly one of source_file (raw dataset) or "
                "source_transform_subdir (prior step) must be set")
        return self


class DefenseEvaluateTask(_TaskBase):
    """Stage 2: defense + target-model query + judging, combined.

    `source_transform_subdir` points at a specific step subfolder of a
    prompt_transform run. The Defense reads that step's prompts.jsonl, runs
    its query-loop against the target model, and the result is judged with
    the canonical evaluator for the benchmark.
    """
    mode: Literal["defense+evaluate"]
    source_transform_subdir: str
    defense: str = "no_defense"
    defense_config: dict[str, Any] = Field(default_factory=dict)
    target_model: str
    system_message: Optional[str] = None
    judge_method: Optional[str] = None    # override; usually None (canonical)


# Discriminated union: Pydantic dispatches by `mode`.
TaskConfig = Annotated[
    Union[PromptTransformTask, DefenseEvaluateTask],
    Discriminator("mode"),
]


class ExperimentPreset(BaseModel):
    """Top-level shape of conf/experiment/*.yaml."""
    num_main_job_threads: int = 5
    num_cluster_jobs: int = 8
    tasks: list[TaskConfig]


# ====================================================================
# LLM / Cluster configs — what conf/llm/*.yaml contains.
# Unchanged from the pre-refactor version; consumed by LLMServiceFactory.
# ====================================================================


class ModelConfig(BaseModel):
    """LLM request parameters."""
    model: str
    max_tokens: int
    temperature: float
    top_p: float
    top_k: int
    frequency_penalty: float
    presence_penalty: float
    stop_sequences: list[str]
    seed: int
    n_completions: int
    stream: bool
    max_concurrency: int
    max_retries: int
    batch_poll_interval: int
    batch_timeout: int


class ClusterConfig(BaseModel):
    """Cluster/vLLM server parameters."""
    partition: str
    excluded_nodes: list[str]
    gpu_types_excluded: list[str]
    gpu_constraint: Optional[str] = None
    num_gpus: int
    num_instances: int
    cpus_per_task: int
    mem_gb: int
    time_limit: str
    port: int
    gpu_memory_utilization: float
    max_model_len: int
    dtype: Optional[str] = None
    chat_template: Optional[str] = None
    trust_remote_code: bool = False
    server_start_timeout: int
    endpoint_wait_timeout: int
    cluster_server_endpoint_timeout: int
    monitor_poll_interval: int
    health_check_timeout: int
    slurm_cmd_timeout: int
    conda_env: str
    cuda_module: str
    hf_home: str
    health_recheck_interval: int = 60


class LLMConfig(BaseModel):
    """Top-level LLM config."""
    model: ModelConfig
    cluster: ClusterConfig

    @model_validator(mode="after")
    def _check_max_model_len_against_arch_ceiling(self) -> "LLMConfig":
        from src.llm_utils.llm_model import LLMModel
        try:
            m = LLMModel.from_string(self.model.model)
        except ValueError:
            return self
        ceiling = m.max_context_len
        if ceiling is not None and self.cluster.max_model_len > ceiling:
            raise ValueError(
                f"cluster.max_model_len={self.cluster.max_model_len} exceeds "
                f"{m.model_id}'s architectural ceiling of {ceiling} "
                f"(from upstream config.json max_position_embeddings). vLLM "
                f"would refuse to serve this at startup. Lower `max_model_len` "
                f"in conf/llm/{m.name.lower()}.yaml.")
        return self

    @model_validator(mode="after")
    def _check_chat_template_file_exists(self) -> "LLMConfig":
        from pathlib import Path
        from src.llm_utils.llm_model import LLMModel
        try:
            m = LLMModel.from_string(self.model.model)
        except ValueError:
            return self
        chat_template = self.cluster.chat_template or m.chat_template
        if not chat_template:
            return self
        templates_dir = (
            Path(__file__).resolve().parent.parent
            / "llm_utils" / "chat_templates")
        template_file = templates_dir / f"{chat_template}.jinja"
        if not template_file.exists():
            raise ValueError(
                f"chat_template={chat_template!r} for {m.model_id} "
                f"does not resolve to a file at {template_file}. "
                f"Available templates: "
                f"{sorted(p.stem for p in templates_dir.glob('*.jinja'))}")
        return self


# ====================================================================
# Evaluation config — judge LLM settings shared by every evaluator.
# ====================================================================


class JudgeLLMConfig(BaseModel):
    """Judge LLM service config."""
    model: str = "gpt-5-nano"
    max_tokens: int = 16384
    temperature: float = 0.0


class EvaluationConfig(BaseModel):
    """Top-level evaluation config."""
    judge_llm_config: JudgeLLMConfig = Field(default_factory=JudgeLLMConfig)
    judge_method: Optional[str] = None
