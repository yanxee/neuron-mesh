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

## 6. 预览 50 台主机的虚拟集群

节点服务运行后，打开：

<http://127.0.0.1:8000/graph?demo=fleet50>

该入口不需要 Token，因为 50 台主机由浏览器确定性生成，不会写入节点数据库。
动画会依次加入 50 台异构主机。点击任意主机可查看 CPU、内存、加速器、存储、
网络、估算算力、能力标签、故障域，以及两台跨故障域冗余备份主机。紫色菱形
节点表示运行在该主机上的 Agent。该页面仅用于视觉演练，不代表已经存在 50 台
物理节点或真实资源承诺。
