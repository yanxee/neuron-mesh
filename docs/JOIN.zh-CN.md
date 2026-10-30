# 加入 NeuronMesh

[English](JOIN.md) | [简体中文](JOIN.zh-CN.md)

NeuronMesh 是一个可运行的研究原型，探索跨异构主机的按能力调度去中心化 LLM 推理、加密持久记忆和持续学习。

项目仍处于早期阶段，一个小而严谨、经过测试的贡献足以影响架构。我们也刻意保持诚实：公网 P2P 传输、真实跨节点 Transformer 执行、联邦训练和生产级安全都是路线图项目，而不是当前已经完成的能力。

**项目：** <https://github.com/yanxee/neuron-mesh>

**网站：** <https://yanxee.github.io/neuron-mesh/zh-CN/>

**架构：** <https://github.com/yanxee/neuron-mesh/blob/main/ARCHITECTURE.zh-CN.md>

**任务：** <https://github.com/yanxee/neuron-mesh/blob/main/docs/CONTRIBUTOR_TASKS.zh-CN.md>

## 选择参与路线

### 1. 验证原型 —— 约 10 分钟

适合首次访问者、节点运维者和兼容性测试者。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe scripts\e2e_check.py
```

Linux/macOS 请参阅[演示文档](DEMO.zh-CN.md)。测试使用确定性 Echo 后端，因此不需要下载模型或使用 GPU。

有价值的成果：提交一份[兼容性报告](https://github.com/yanxee/neuron-mesh/issues/new?template=deployment_report.yml)，包含操作系统、CPU 架构、Python 版本、准确命令和非敏感输出。

### 2. 完成一个限定问题 —— 30 到 90 分钟

浏览[适合首次贡献的 Issue](https://github.com/yanxee/neuron-mesh/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)。开始前先在 Issue 中留言。只要包含测试或可复现证据，小改动同样欢迎。

适合开始的领域：

- 远端流式推理测试；
- 存储配额边界行为；
- Docker Compose 冒烟测试；
- 后端适配器一致性；
- 角色迁移故障恢复；
- 文档、图表和翻译。

### 3. 带来一个研究问题 —— 一个下午或更久

选择一个可度量问题，而不是争论整个愿景：

- 在相同工作负载下，能力感知调度是否优于轮询和仅按 RTT 路由？
- 热/温/冷加密召回能否在不产生不可接受延迟的情况下降低 prompt token 成本？
- 记忆巩固与回放如何影响事实准确性、陈旧性和遗忘？
- 局域网管线并行何时优于 WAN 上的完整模型提供者？
- 哪些故障会产生虚假耐久性、陈旧副本或不可恢复的角色状态？
- 恶意记忆、模型更新和节点遥测应如何隔离？

请发布基线、硬件、工作负载、指标、验收阈值和失败模式。可复现的负面结果也是有效贡献。

### 4. 评审协议边界

先阅读[架构基线](../ARCHITECTURE.zh-CN.md)、[状态与故障模型](architecture/STATE_AND_FAILURE.zh-CN.md)和[接口契约](architecture/INTERFACE_CONTRACTS.zh-CN.md)。项目有意区分已接受的目标架构和已实现行为。

我们尤其需要以下领域的对抗性评审：

- 分布式系统与 NAT 穿透；
- 命名空间授权、密钥封装和恢复；
- 加密副本删除和回滚语义；
- 模型与 worker 供应链信任；
- 热、电池和网络变化下的推理调度；
- WebXR/OpenXR 隐私和权限边界。

请在 Discussion 中提交威胁模型，或开一个包含具体替代方案的设计 Issue。不要期待核心团队已经解决这些问题。

### 5. 提供上下文而不是代码

你可以分享真实硬件测量、失败部署、大学课程练习、无障碍评审、运维检查表或翻译。只要包含足够证据让其他人复现观测，这些内容就是研究输入。

## 当前重点需求

| 领域 | 当前优先级 |
| --- | --- |
| 架构 | 将核心契约转换为版本化 Schema 和状态机测试 |
| 传输 | 评估 libp2p QUIC、AutoNAT/DCUtR 和中继失败模式 |
| 推理 | 定义 llama.cpp/vLLM worker 与阶段清单契约 |
| 记忆 | 测量上下文成本、召回质量和加密恢复延迟 |
| 学习 | 设计隔离安全的联邦 Adapter 实验 |
| 信任 | 用命名空间授权替换整个邀请网共享令牌 |
| 可靠性 | 增加混沌、Docker 和 NAT 矩阵测试 |
| 接口 | 定义与平台无关的 WebXR/OpenXR 适配器边界 |

## “完成”的含义

当另一个人能够完成以下事项时，贡献才算准备就绪：

1. 理解预期行为；
2. 使用文档中的命令或工作负载复现结果；
3. 识别失败边界和安全假设；
4. 在没有隐藏凭证或专有数据的情况下运行自动检查；
5. 不依赖未记录本地状态来维护变更。

## 贡献者约定

- 具体且友善；批评证据和设计，而不是个人。
- 不要把路线图项目描述为已实现能力。
- 不要上传私有记忆、凭证或未授权模型产物。
- 按照[安全策略](../SECURITY.zh-CN.md)私下报告可利用安全问题。
- 披露实质性 AI 辅助，并对贡献负责。
- 尽早求助。一个范围明确的部分成果，比沉默的大规模重写更有价值。

所有贡献类型都有资格获得发布说明署名，并按照[治理规则](../GOVERNANCE.zh-CN.md)逐步承担评审或维护责任。

## 开始交流

- [GitHub Discussions](https://github.com/yanxee/neuron-mesh/discussions)：开放问题和设计探索
- [Issues](https://github.com/yanxee/neuron-mesh/issues)：可执行缺陷、任务和基准
- [架构验证问题](architecture/QUALITY_SCENARIOS.zh-CN.md)：实现必须满足的可观测场景
- [研究提案](https://github.com/yanxee/neuron-mesh/issues/new?template=research_proposal.yml)：带复现计划的假设
- [兼容性报告](https://github.com/yanxee/neuron-mesh/issues/new?template=deployment_report.yml)：演示和部署结果
