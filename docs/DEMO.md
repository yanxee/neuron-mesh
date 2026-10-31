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

## 5. Open the live graph

Run the populated graph demo:

```bash
python scripts/graph_demo.py --open
```

Open <http://127.0.0.1:18082/graph> and enter the printed token. Drag to pan,
scroll to zoom and select a node to inspect it. Peer announcements, remote
compute and encrypted-storage support animate the corresponding relationship
line for a short time.

## 6. Preview a 50-host fleet

With the node service running, open:

<http://127.0.0.1:8000/graph?demo=fleet50>

No token is required because this route creates deterministic synthetic data in
the browser and never writes it to the node database. The animation introduces
50 heterogeneous hosts in sequence. Select any host to inspect its CPU, memory,
accelerator, storage, network, compute estimate, capability tags, failure domain
and two cross-domain redundancy peers. Purple diamond nodes represent the Agent
hosted on each machine. This is a visual rehearsal, not evidence of 50 physical
nodes or pledged capacity.

After the fleet is assembled, a cyan task hub appears. The demo cycles through
five objectives such as long-context research, multimodal understanding,
continual learning, edge response and memory repair. Each objective is decomposed
into capability-specific stages, and a shuffled coverage deck assigns between 1
and 40 hosts to each plan. Select the task hub to inspect the objective, requesting
ingress, random coverage size, lead host, allocated capacity and every host
assignment.

A task does not hold simultaneous connections to all planned workers. Each
asynchronous batch contacts a random 1–20 hosts, shows a short animated
communication window, and advances to the next batch after the calls finish.
Small one-host plans bundle several stages on one machine; large plans spread
stages across up to 40 shard workers.

Each assignment has an independent service deadline calculated from allocated
TFLOPS, stage complexity and deterministic jitter. Faster or better-funded hosts
complete first and free a concurrency slot for another waiting host; slower hosts
remain connected longer. This makes call overlap and release visibly uneven.

The scheduler keeps up to three requests active at once, each initiated by a
different ingress host. Green request pulses show host-to-task intent, while cyan
pulses show the single asynchronous worker call currently in progress. A host may
hold multiple task leases; its detail panel lists every concurrent assignment,
allocation percentage and granted TFLOPS. Expanding the active task count
recalculates shares, and an amber `N×` badge marks a host shared by multiple
requests.

