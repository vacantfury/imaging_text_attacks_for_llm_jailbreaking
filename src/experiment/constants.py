"""Experiment constants derived from cluster QOS limits."""

# NURC cluster gpu partition limits
# See text_docs/nurc_cluster_properties.md for details
MAX_SUBMIT_JOBS_PER_USER = 8  # max total submitted (running + pending)
MAX_RUNNING_JOBS_PER_USER = 4  # max concurrently running

# 1 slot is reserved for the master job that submits workers
MAX_PARALLEL_WORKERS = MAX_SUBMIT_JOBS_PER_USER - 1  # = 7
