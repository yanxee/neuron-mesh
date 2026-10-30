# Ten-Minute NeuronMesh Demo

[English](DEMO.md) | [简体中文](DEMO.zh-CN.md)

The demo uses two local nodes and a deterministic Echo backend. It requires no model download or GPU.

## 1. Start the nodes

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
python scripts/e2e_check.py
```

Expected output includes:

```text
{
  "mode": "networked",
  "online_peers": 1,
  "durability": "D2",
  "replicas": ["..."],
  "remote_node": "...",
  "cold_restore": "ok"
}
```

## 2. What the demo proves

- Two independently started nodes announce signed capability records.
- The second node discovers an eligible remote node.
- A request can be explicitly routed to the remote provider.
- Important memory gains an encrypted replica in another failure domain.
- A cold memory can be removed locally and recalled from the replica.
- The check fails when readiness or cross-node backup is broken.

## 3. What it does not prove

- Public-internet libp2p transport
- Real model splitting or tensor parallelism
- Federated training
- Production security or availability

Those boundaries are tracked in [ROADMAP.md](../ROADMAP.md).

## 4. Show the UI/API

```bash
export NEURON_SHARED_TOKEN="replace-with-a-long-random-token"
neuron-mesh serve --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/docs> and demonstrate:

1. `/v1/node/capabilities`
2. `/v1/memory/write`
3. `/v1/memory/search`
4. `/v1/chat/completions`
5. `/v1/node/drain`

