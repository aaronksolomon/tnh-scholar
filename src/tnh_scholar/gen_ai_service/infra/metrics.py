"""Metrics Collection.

Aggregates operational metrics (latency, throughput, errors).
Adapters report metrics via a common interface for monitoring and dashboards.

Connected modules:
  - infra.tracer
  - providers.*_adapter
"""