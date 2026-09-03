"""LLMModel-keyed adapter over the canonical SLURM server manager (`devices`).

Why this file exists
--------------------
The vLLM-on-SLURM server lifecycle (job submission, endpoint pool, health
hysteresis, zombie ledger) lives ONCE, in the `devices` infrastructure repo
(`devices/slurm/server_manager.py`) — it is device/compute-dispatch
machinery, not LLM-client machinery. A drifted copy used to live in
`llm_utils` as `cluster_server_manager.py`; the overlap audit of 2026-09-02
(Zeus-ratified) named devices the single home and retired the copy
(llm_utils v7.0.0 removes it; the v5.x line keeps it deprecated).

The API delta
-------------
Devices keys everything by a plain model-id STRING (the HF path handed to
vLLM's `--model`), deliberately: it knows nothing about LLM providers or
registries. This repo — and llm_utils' `SlurmClusterService`, which calls
`acquire_endpoint`/`release_endpoint` on whatever manager the factory was
handed — keys by `llm_utils.LLMModel`. This adapter is the wiring between
the two contracts that devices' own docstring describes: it translates
`LLMModel -> model.model_id` on every call, and injects the model's
registry-declared `chat_template` into the config dict (devices reads the
template name from config; llm_utils' copy read it off the ModelSpec).

Nothing else changes: the adapter forwards to devices and returns whatever
devices returns.
"""
from typing import Any, Dict, Optional

from devices import ClusterModelServerManager as _DevicesClusterManager


class ClusterModelServerManager:
    """`LLMModel`-keyed facade over `devices.ClusterModelServerManager`.

    Exposes exactly the surface this repo and llm_utils' SlurmClusterService
    use. `provider` is validated here (devices dropped that check together
    with its llm_utils import).
    """

    def __init__(self) -> None:
        self._inner = _DevicesClusterManager()

    # -------- lifecycle --------

    def start_server(self, model, config: Dict[str, Any]) -> None:
        from llm_utils import Provider
        if model.provider != Provider.SLURM_CLUSTER:
            raise ValueError(
                f"{model.model_id} is not a cluster model "
                f"(provider: {model.provider})")
        # The chat template is an architectural fact carried by the llm_utils
        # model registry; devices takes it as a config key (bare name -> its
        # own chat_templates/<name>.jinja, or an explicit .jinja path). An
        # explicit config value still wins, as it did before.
        cfg = dict(config)
        if not cfg.get("chat_template") and model.chat_template:
            cfg["chat_template"] = model.chat_template
        self._inner.start_server(model.model_id, cfg)

    def shutdown_model(self, model) -> None:
        self._inner.shutdown_model(model.model_id)

    def shutdown_all(self) -> None:
        self._inner.shutdown_all()

    # -------- endpoint pool (the duck-typed contract llm_utils calls) --------

    def acquire_endpoint(self, model, timeout: Optional[int] = None) -> str:
        return self._inner.acquire_endpoint(model.model_id, timeout)

    def release_endpoint(self, model, endpoint: str) -> None:
        self._inner.release_endpoint(model.model_id, endpoint)

    def wait_for_first_server(self, model, timeout: Optional[int] = None) -> str:
        return self._inner.wait_for_first_server(model.model_id, timeout)

    # -------- status --------

    def get_num_instances(self, model) -> int:
        return self._inner.get_num_instances(model.model_id)

    def get_num_ready(self, model) -> int:
        return self._inner.get_num_ready(model.model_id)

    def get_server_status(self, model) -> Dict[str, Any]:
        return self._inner.get_server_status(model.model_id)


__all__ = ["ClusterModelServerManager"]
