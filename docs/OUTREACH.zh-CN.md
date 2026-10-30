# 招募与传播工具包

[English](OUTREACH.md) | [简体中文](OUTREACH.zh-CN.md)

使用这些材料邀请协作者，同时避免夸大当前实现。

## 为什么值得参与

NeuronMesh 并不要求新参与者接受完整愿景。它提供一个可运行原型、明确研究问题和限定任务，参与者可以产出测试、基准或设计产物。无需 GPU、模型下载或长期运行节点的承诺即可开始。

第一阶段目标是证据：复现双节点演示、识别失败边界，并判断哪些架构值得真实实现。

## 一句话介绍

NeuronMesh 是一个开源研究网络，探索跨异构节点的能力感知分布式 LLM 推理、加密持久记忆和持续学习。

## 简短公告

NeuronMesh v0.2.0 是一个可运行的、面向去中心化 LLM 基础设施的研究型 MVP。它包含签名节点能力、入口侧路由、OpenAI 兼容 API、AES-GCM 记忆、跨故障域加密副本、角色迁移、安全排空回执和双节点集成测试。我们正在寻找分布式系统、LLM Serving、记忆巩固、联邦学习、安全和 WebXR 领域的贡献者。

## 招募贡献者

我们需要帮助将研究骨架变成可复现平台：

- libp2p QUIC、DHT 和 NAT 穿透；
- 真实 llama.cpp 和 vLLM 阶段 worker；
- 记忆巩固与检索基准；
- 联邦 LoRA 和遗忘研究；
- 命名空间授权与加密密钥恢复；
- Docker、可观测性和混沌测试；
- WebXR/OpenXR 适配器。

请从 10 分钟演示或有明确范围的 Issue 开始：<https://yanxee.github.io/neuron-mesh/zh-CN/>

## 可直接使用的发布文案

### GitHub 公告

> NeuronMesh v0.2.0 已公开：一个可运行的邀请制研究原型，探索能力感知去中心化 LLM 推理、加密持久记忆和离线自治。
>
> 它已经展示签名节点能力、入口侧路由、OpenAI 兼容 API、AES-GCM 记忆、跨故障域密文副本、冷召回和安全排空回执。公网 P2P 传输、跨节点 Transformer 执行和联邦训练仍是明确标注的路线图项目。
>
> 我们需要可复现贡献，而不是炒作：运行无需 GPU 的双节点演示、选择一个限定测试，或提出包含基线和失败边界的基准。
>
> 入口：https://yanxee.github.io/neuron-mesh/zh-CN/

### 中文社交/社区发布

> 开源项目 NeuronMesh 正在寻找首批研究与实践协作者。
>
> 这是一个可运行的研究型 MVP：异构设备按实测能力参与网络，任意授权节点可作为入口，记忆以密文跨故障域备份，断网时退回本地自治。当前公网传输仍是邀请制 HTTP 网格；libp2p/QUIC、真实的跨节点 Transformer 执行和联邦训练都在路线图中，没有包装成已完成能力。
>
> 不需要 GPU 或大模型权重也能参与：10 分钟跑通双节点演示、认领一个边界测试、报告真实硬件结果，或者提出可复现研究问题。代码、测试、基准、翻译和兼容性报告都会被记录。
>
> 参与入口：https://yanxee.github.io/neuron-mesh/zh-CN/
>
> GitHub：https://github.com/yanxee/neuron-mesh

### 面向分布式系统研究者的定向邀请

> 我们正在测试能力感知路由、加密冷记忆恢复和角色迁移，在 NAT 不稳定、热限制和间歇连接条件下是否仍能保持正确。当前 MVP 有意保持足够小，便于审计。相比宽泛背书，我们更希望得到失败路径矩阵或基准提案。传输决策记录或分区恢复任务是否适合贵组？

### 面向 LLM Serving 工程师的定向邀请

> NeuronMesh 当前将完整模型请求路由到 OpenAI 兼容 worker。我们正在先定义后端和阶段清单契约，再实现管线执行。有价值的贡献可以是 llama.cpp/vLLM 一致性夹具、取消语义，或证明完整模型路由仍更优的 WAN 基线。

## 合适渠道

- GitHub Discussions 和 Issues；
- 高校分布式系统与 AI 系统研究组；
- 本地开源聚会；
- LLM Serving 与推理工程社区；
- 边缘计算和 WebXR 研究社区。

只在允许项目介绍或自我宣传的渠道发布。针对群体专业能力调整邀请内容，并在同一讨论串中回答技术问题。

## 启动顺序

1. 置顶一个欢迎/Discussion 帖子，链接演示、贡献指南和 Issue 模板。
2. 保持至少三个真正有边界的 `good first issue`。
3. 根据专业能力邀请五名具体研究者或工程师，而不是群发泛化消息。
4. 在启动招募后的 30 天内发布第一个可复现硬件或记忆基准。
5. 将重复问题转化为文档或有范围 Issue，并对每项被接受成果署名致谢。

追踪真正有用的指标，而不只看 Star：

- 独立参与者完成演示或提交兼容性报告；
- 首次贡献者认领并合并的 Issue；
- 包括负面结果在内的可复现基准；
- 对协议或安全边界的外部评审；
- 再次回来完成第二项限定任务的贡献者。

## 诚实表述

始终说明：

- 这是 `v0.2.0` 研究软件；
- 在线发现目前使用邀请制 HTTP 网格；
- 公网 P2P 传输属于计划，不是已完成能力；
- 默认后端是确定性 Echo，真实推理需要配置 OpenAI 兼容 worker；
- “持久记忆”表示加密复制与恢复，不是物理上永久存储。

## 规范链接

- 仓库：<https://github.com/yanxee/neuron-mesh>
- 网站：<https://yanxee.github.io/neuron-mesh/>
- 路线图：<https://github.com/yanxee/neuron-mesh/blob/main/ROADMAP.zh-CN.md>
- 贡献任务：<https://github.com/yanxee/neuron-mesh/blob/main/docs/CONTRIBUTOR_TASKS.zh-CN.md>
- 贡献入口：<https://yanxee.github.io/neuron-mesh/join.zh-CN.html>
