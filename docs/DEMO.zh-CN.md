# 十分钟 NeuronMesh 演示

[English](DEMO.md) | [简体中文](DEMO.zh-CN.md)

该演示使用两个本地节点和确定性的 Echo 后端，不需要下载模型或使用 GPU。

## 1. 启动节点

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
python scripts/e2e_check.py
```

预期输出包含：

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

## 2. 演示证明了什么

- 两个独立启动的节点会公告签名能力记录。
- 第二个节点可以发现符合条件的远端节点。
- 请求可以显式路由到远端提供者。
- 重要记忆会在另一个故障域中生成加密副本。
- 本地删除冷记忆后，可以从副本恢复。
- 当就绪状态或跨节点备份被破坏时，检查会失败。

## 3. 演示没有证明什么

- 公网 libp2p 传输；
- 真实模型切分或张量并行；
- 联邦训练；
- 生产级安全性或可用性。

这些边界记录在[路线图](../ROADMAP.zh-CN.md)中。

## 4. 展示 UI/API

```bash
export NEURON_SHARED_TOKEN="replace-with-a-long-random-token"
neuron-mesh serve --host 127.0.0.1 --port 8000
```

打开 <http://127.0.0.1:8000/docs>，演示：

1. `/v1/node/capabilities`
2. `/v1/memory/write`
3. `/v1/memory/search`
4. `/v1/chat/completions`
5. `/v1/node/drain`

## 5. 打开实时关系图

运行带示例主机、角色和活动的关系图演示：

```bash
python scripts/graph_demo.py --open
```

打开 <http://127.0.0.1:18082/graph> 并输入终端打印的 Token。可以拖拽平移、
滚轮缩放，并选择节点查看详情。节点公告、远端算力和加密存储支持发生时，
对应关系线会在短时间内发光闪烁。

## 6. 预览可配置规模的虚拟集群

节点服务运行后，打开：

<http://127.0.0.1:8000/graph?demo=fleet256>

该入口不需要 Token，因为主机由浏览器确定性生成，不会写入节点数据库。
默认示例会依次加入 256 台异构主机。把 `fleet256` 改为 `fleet50`、
`fleet186`、`fleet543` 或其他受支持的 `fleetN`，也可使用 `demo=N`；
当前范围为 1–2048 台。点击任意主机可查看 CPU、内存、加速器、存储、
网络、估算算力、能力标签、故障域，以及两台跨故障域冗余备份主机。紫色菱形
节点表示运行在该主机上的 Agent。该页面仅用于视觉演练，不代表已经存在 256 台
物理节点或真实资源承诺。

当前采用“混沌云”布局，不使用固定圆环、网格或故障域分组。每台主机
的目标位置和屏外飞入方向都会随机变化；故障域仍显示在主机详情中，但不参与
当前布局。大规模模式会自动启用采样斥力、动态缩放和标签降采样。以后可以
增加独立的域/组视图模式。

主机集群组建完成后会出现青色任务中枢。演示会在长上下文研究、多模态理解、
持续学习、边缘响应和记忆修复等五类计算目标之间轮换。每个目标都会拆分为有
明确能力要求的子任务，并通过随机覆盖序列为每次计划分配 1–40 台主机。点击
任务中枢可查看计算目标、请求入口、随机覆盖规模、主控主机、获批算力以及每台
主机的具体分工。

任务不会同时连接所有计划内主机。每个异步批次会同时联系随机 1–20 台主机，
显示短暂的通信脉冲，结束后再推进到下一批。单主机计划会把多个阶段串行合并到
一台机器；较大计划则把阶段扩展到最多 40 台分片执行主机。

每个子任务都有独立的通信结束时间，根据获批 TFLOPS、阶段复杂度和确定性抖动
计算。快速或份额较高的主机会较早完成，释放并发槽位并让下一台等待主机接入；
慢速或低份额主机会保持更长的通信脉冲，因此同一批次不会同时结束。

调度器会同时保持最多 3 个申请处于活动状态，每个申请由不同入口主机发起。
绿色请求脉冲表示主机向任务中枢申请资源，青色脉冲表示当前正在通信的唯一阶段
主机。

## 7. 创建协调任务

后端已经实现任务协调，并使用 SQLite 持久化任务状态：

```bash
curl http://127.0.0.1:8000/v1/tasks \
  -H "Authorization: Bearer $NEURON_SHARED_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "利用分布式记忆生成经过校验的答案",
    "target_hosts": 3,
    "max_parallel": 2,
    "requested_tflops": 500,
    "stages": [
      {"name": "规划", "capability": "full-model"},
      {"name": "召回上下文", "capability": "cache"},
      {"name": "推理", "capability": "inference"},
      {"name": "校验", "capability": "checkpoint"}
    ]
  }'
```

使用 `GET /v1/tasks/{task_id}` 查询任务。调度器最多同时保持 `max_parallel`
个调用，在并发任务增加时重新计算主机份额，并为每次调用分配独立服务时长。
在接入真实模型阶段执行器之前，`execution_mode` 始终为 `coordination`。
同一主机可以持有多个任务租约；点击主机可查看所有并发分配、资源占比和获批
TFLOPS。新增申请会触发份额再平衡，黄色 `N×` 标记表示该主机正被多个任务共享。
