# Architecture

**Layers:** `data_generator` → `protocols` (contracts) → `agents` → `orchestrator` → `services` → `api`.

- **Topology** (`agents/connectivity_agent/topology.py`): NetworkX graph of 3 routers, 6 switches, 8 access points, 3 servers (DNS/DHCP/app). Primary links form a tree rooted at the core router; one redundant router-to-router link exists. It is shared with the generator, connectivity agent and correlation agent.
- **ML:** two Isolation Forests (performance features, infrastructure features) trained on healthy rows only. Their 0-1 anomaly score is blended into rule confidence (25%) and can raise a low-confidence `statistical_anomaly` finding. If a model file is missing, agents fall back to rules.
- **Honesty controls:** ground truth is stripped before agents run; train/test use different seeds; benign transient spikes and overlapping fault severities are injected on purpose.
- **Added files vs. the original tree:** `agents/base_agent.py`, `ml_models/detector_base.py`, `conftest.py`, and `__init__.py` files.
