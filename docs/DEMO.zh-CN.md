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
