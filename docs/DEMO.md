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

## 6. Preview a configurable fleet

With the node service running, open:

<http://127.0.0.1:8000/graph?demo=fleet256>

No token is required because this route creates deterministic synthetic data in
the browser and never writes it to the node database. The default example
introduces 256 heterogeneous hosts in sequence. Change
`fleet256` to `fleet50`, `fleet186`, `fleet543` or another supported `fleetN`
value; `demo=N` is also accepted. The current range is 1–2048 hosts. Select any
host to inspect its CPU, memory,
accelerator, storage, network, compute estimate, capability tags, failure domain
and two cross-domain redundancy peers. Purple diamond nodes represent the Agent
hosted on each machine. This is a visual rehearsal, not evidence of 256 physical
nodes or pledged capacity.

The current layout intentionally uses a hash-mixed chaos cloud instead of rings,
grids or domain grouping. Each host receives an independent target inside a
broad rectangle, warped by several random cluster centers to preserve irregular
density and holes. A joining host starts a short distance from its target and
moves into place; it does not travel from a shared perimeter. Inter-host
repulsion and relationship-line springs are disabled so the final result cannot
collapse back into a ring. Large fleets also use dynamic scaling and label
thinning. Above 256 hosts, selection focuses structural edges; above 600 hosts,
the renderer lowers its frame rate and backing-buffer resolution to keep the
page responsive. Failure-domain metadata remains visible in host details but does
not influence this layout yet; a grouped view can be added as a separate mode
later.

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

## 7. Create a coordination task

Task coordination is also implemented in the backend and persisted in SQLite:

```bash
curl http://127.0.0.1:8000/v1/tasks \
  -H "Authorization: Bearer $NEURON_SHARED_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "Build a verified answer from distributed memory",
    "target_hosts": 3,
    "max_parallel": 2,
    "requested_tflops": 500,
    "stages": [
      {"name": "Plan", "capability": "full-model"},
      {"name": "Retrieve context", "capability": "cache"},
      {"name": "Infer", "capability": "inference"},
      {"name": "Verify", "capability": "checkpoint"}
    ]
  }'
```

Inspect it with `GET /v1/tasks/{task_id}`. The service keeps up to
`max_parallel` calls active, recalculates host shares when another task starts,
and assigns each call an independent duration. `execution_mode` is
`coordination` until a real model-stage executor is connected.

