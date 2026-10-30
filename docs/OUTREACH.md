# Outreach Kit

Use these materials to invite collaborators without overstating the current implementation.

## Why someone should participate

NeuronMesh is not asking newcomers to accept the full vision. It offers a runnable prototype, explicit research questions and scoped work that can produce a test, benchmark or design artifact. A contributor can start without a GPU, a model download or a commitment to run a permanent node.

The first goal is evidence: reproduce the two-node demo, identify failure boundaries and decide which parts of the architecture deserve real implementation.

## One-sentence pitch

NeuronMesh is an open-source research network exploring capability-aware distributed LLM inference, encrypted persistent memory and continual learning across heterogeneous nodes.

## Short announcement

NeuronMesh v0.2.0 is a runnable research MVP for decentralized LLM infrastructure. It includes signed node capabilities, entry-side routing, an OpenAI-compatible API, AES-GCM memory, cross-failure-domain encrypted replicas, role migration, safe drain receipts and a two-node integration test. We are looking for contributors in distributed systems, LLM serving, memory consolidation, federated learning, security and WebXR.

## Call for contributors

We need help turning the research skeleton into a reproducible platform:

- libp2p QUIC, DHT and NAT traversal;
- real llama.cpp and vLLM stage workers;
- memory consolidation and retrieval benchmarks;
- federated LoRA and unlearning research;
- namespace authorization and encrypted key recovery;
- Docker, observability and chaos testing;
- WebXR/OpenXR adapters.

Start with the 10-minute demo or a scoped issue: <https://yanxee.github.io/neuron-mesh/join.html>.

## Ready-to-share posts

### GitHub-friendly announcement

> NeuronMesh v0.2.0 is now public: a runnable, invite-only research prototype for capability-aware decentralized LLM inference, encrypted persistent memory and offline autonomy.
>
> It already demonstrates signed node capabilities, entry-side routing, an OpenAI-compatible API, AES-GCM memory, cross-failure-domain ciphertext replicas, cold recall and safe drain receipts. Public-internet P2P transport, cross-node Transformer execution and federated training remain explicit roadmap items.
>
> We are looking for reproducible contributions, not hype: run the no-GPU two-node demo, pick a scoped test, or propose a benchmark with a baseline and failure boundary.
>
> Start here: https://yanxee.github.io/neuron-mesh/join.html

### Chinese social/community post

> 开源项目 NeuronMesh 开始寻找首批研究与实践协作者。
>
> 这是一个可运行的研究型 MVP：异构设备按实测能力参与网络，任意授权节点可作为入口，记忆以密文跨故障域备份，断网时退回本地自治。当前公网传输仍是邀请制 HTTP 网格；libp2p/QUIC、真实的跨节点 Transformer 执行和联邦训练都在路线图中，没有包装成已完成能力。
>
> 不需要 GPU 或大模型权重也能参与：10 分钟跑通双节点演示、认领一个边界测试、报告一类真实硬件结果，或者提出一个可复现的研究问题。代码、测试、基准、翻译和兼容性报告都会被记录。
>
> 参与入口：https://yanxee.github.io/neuron-mesh/join.html
>
> GitHub：https://github.com/yanxee/neuron-mesh

### Direct invitation to distributed-systems researchers

> We are testing whether capability-aware routing, encrypted cold-memory recall and role migration can remain correct when nodes have unstable NAT, thermal limits and intermittent connectivity. The current MVP is deliberately small enough to audit. We would value a failed-path matrix or a benchmark proposal more than a broad architecture endorsement. Would the transport decision record or partition-recovery task be relevant to your group?

### Direct invitation to LLM-serving engineers

> NeuronMesh currently routes whole-model requests to an OpenAI-compatible worker. We are defining a backend and stage-manifest contract before implementing pipeline execution. A useful contribution could be a llama.cpp/vLLM conformance fixture, cancellation semantics or a WAN baseline showing where whole-model routing is still the better design.

## Suitable channels

- GitHub Discussions and issues
- University distributed-systems and AI systems groups
- Local open-source meetups
- LLM serving and inference engineering communities
- Edge computing and WebXR research communities

Post only where self-promotion or project announcements are welcome. Tailor the invitation to the group's expertise and answer technical questions in the same thread.

## Launch sequence

1. Pin one welcome/discussion thread that links the demo, contributor guide and issue templates.
2. Keep at least three genuinely bounded `good first issue` tasks open.
3. Invite five specific researchers or engineers with a task matched to their expertise instead of a generic mass message.
4. Publish the first reproducible hardware or memory benchmark within 30 days of outreach.
5. Convert recurring questions into documentation or scoped issues; thank and credit every accepted result.

Track useful indicators rather than stars alone:

- demo runs or compatibility reports from independent people;
- issues claimed and merged by first-time contributors;
- reproducible benchmarks, including negative results;
- external review comments on protocol or security boundaries;
- repeat contributors returning for a second scoped task.

## Honest framing

Always state:

- This is `v0.2.0` research software.
- Online discovery currently uses an invite-only HTTP mesh.
- Public-internet P2P transport is planned, not implemented.
- The default backend is deterministic Echo; real inference uses a configured OpenAI-compatible worker.
- “Persistent memory” means encrypted replication and recovery, not physically permanent storage.

## Canonical links

- Repository: <https://github.com/yanxee/neuron-mesh>
- Website: <https://yanxee.github.io/neuron-mesh/>
- Roadmap: <https://github.com/yanxee/neuron-mesh/blob/main/ROADMAP.md>
- Contributor tasks: <https://github.com/yanxee/neuron-mesh/blob/main/docs/CONTRIBUTOR_TASKS.md>
- Contributor entry guide: <https://yanxee.github.io/neuron-mesh/join.html>

